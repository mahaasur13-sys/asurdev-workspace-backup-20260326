"""
TradingView Webhook API для AstroFin Sentinel.

Endpoints:
- POST /webhook/tradingview — приём алертов
- GET /health — liveness probe
- GET /api/alerts — список алертов
- GET /api/alerts/{id} — статус алерта
- GET /api/stats — статистика
"""

from fastapi import FastAPI, HTTPException, Header, Depends, Request
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager
import logging
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db, init_db, close_db
from core.config import settings
from agents import orchestrator, Alert
from repositories.alert_repository import AlertRepository

# === Lifespan ===

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown events."""
    # Startup
    await init_db()
    logger.info("AstroFin Sentinel started")
    yield
    # Shutdown
    await close_db()
    logger.info("AstroFin Sentinel stopped")

# === Логирование ===

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# === FastAPI App ===

app = FastAPI(
    title=settings.APP_NAME,
    description="Мультиагентная система для анализа торговых сигналов",
    version=settings.VERSION,
    lifespan=lifespan,
)

# Global orchestrator instance (LangChain agents with tool-calling)
_orchestrator = orchestrator.Orchestrator(use_langchain=True)


# === Pydantic Models ===

class TradingViewAlert(BaseModel):
    """TradingView Alert payload."""
    alert_id: Optional[str] = None
    symbol: str
    action: str  # buy, sell, hold
    price: float
    quantity: Optional[float] = None
    strategy: Optional[str] = "unknown"
    timeframe: Optional[str] = "1h"
    astro_signal: Optional[bool] = False
    ml_confidence: Optional[float] = 0.5


class AlertStatus(BaseModel):
    """Статус алерта для API response."""
    id: str
    symbol: str
    action: str
    price: float
    status: str
    created_at: str
    completed_at: Optional[str] = None
    processing_time_ms: Optional[float] = None
    synthesis: Optional[dict] = None
    error: Optional[str] = None


class WebhookResponse(BaseModel):
    """Response для webhook."""
    status: str
    alert_id: str
    timestamp: str
    message: str


# === Dependencies ===

async def get_orchestrator(
    db: AsyncSession = Depends(get_db)
) -> orchestrator.Orchestrator:
    """Предоставляет оркестратор с привязкой к БД."""
    _orchestrator.set_db(db)
    return _orchestrator


# === API Endpoints ===

@app.get("/health")
async def health_check():
    """Liveness probe."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "timestamp": datetime.utcnow().isoformat(),
        "ollama": settings.OLLAMA_BASE_URL,
    }


@app.post("/webhook/tradingview", response_model=WebhookResponse)
async def receive_tradingview_alert(
    alert: TradingViewAlert,
    request: Request,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
    orch: orchestrator.Orchestrator = Depends(get_orchestrator),
):
    """
    Принимает alert от TradingView и передаёт в оркестратор.
    
    Workflow:
    1. Валидация payload
    2. Генерация alert_id если не предоставлен
    3. Передача в Orchestrator
    4. Возврат промежуточного статуса
    """
    # Валидация webhook secret (если настроен)
    if settings.TRADINGVIEW_SECRET and x_webhook_secret != settings.TRADINGVIEW_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    
    # Генерируем alert_id если не предоставлен
    alert_id = alert.alert_id or str(uuid.uuid4())[:8]
    
    logger.info(
        f"[ALERT #{alert_id}] {alert.symbol.upper()} {alert.action.upper()} "
        f"@ ${alert.price:,.2f} | Strategy: {alert.strategy} "
        f"| Astro: {alert.astro_signal} | ML: {alert.ml_confidence:.2%}"
    )
    
    # Преобразуем в dict для оркестратора
    raw_data = alert.model_dump()
    raw_data["alert_id"] = alert_id
    raw_data["received_at"] = datetime.utcnow().isoformat()
    
    try:
        processed_alert = await orch.process_alert(raw_data)
        
        return WebhookResponse(
            status="processed",
            alert_id=processed_alert.id,
            timestamp=datetime.utcnow().isoformat(),
            message=(
                f"Alert #{processed_alert.id} processed: "
                f"{processed_alert.synthesis_result.recommendation.upper()} "
                f"({processed_alert.synthesis_result.confidence:.2%})"
            )
        )
    except Exception as e:
        logger.error(f"[ALERT #{alert_id}] Processing failed: {e}")
        return WebhookResponse(
            status="error",
            alert_id=alert_id,
            timestamp=datetime.utcnow().isoformat(),
            message=f"Processing failed: {str(e)}"
        )


@app.get("/api/alerts", response_model=list[AlertStatus])
async def list_alerts(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """Возвращает последние алерты из БД."""
    repo = AlertRepository(db)
    db_alerts = await repo.get_recent(limit)
    
    return [
        AlertStatus(
            id=a.id,
            symbol=a.symbol,
            action=a.action,
            price=a.price,
            status=a.status,
            created_at=a.received_at.isoformat() if a.received_at else "",
            completed_at=a.completed_at.isoformat() if a.completed_at else None,
            processing_time_ms=a.processing_time_ms,
            error=a.error,
            synthesis={
                "recommendation": a.synthesis_result.get("recommendation") if a.synthesis_result else None,
                "confidence": a.synthesis_result.get("confidence") if a.synthesis_result else None,
                "reasoning": a.synthesis_result.get("reasoning") if a.synthesis_result else None,
                "warnings": a.synthesis_result.get("warnings", []) if a.synthesis_result else [],
                "key_factors": a.synthesis_result.get("key_factors", []) if a.synthesis_result else [],
            } if a.synthesis_result else None
        )
        for a in db_alerts
    ]


@app.get("/api/alerts/{alert_id}", response_model=AlertStatus)
async def get_alert_status(
    alert_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Возвращает статус конкретного алерта."""
    repo = AlertRepository(db)
    alert = await repo.get_by_id(alert_id)
    
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert #{alert_id} not found")
    
    return AlertStatus(
        id=alert.id,
        symbol=alert.symbol,
        action=alert.action,
        price=alert.price,
        status=alert.status,
        created_at=alert.received_at.isoformat() if alert.received_at else "",
        completed_at=alert.completed_at.isoformat() if alert.completed_at else None,
        processing_time_ms=alert.processing_time_ms,
        error=alert.error,
        synthesis={
            "recommendation": alert.synthesis_result.get("recommendation") if alert.synthesis_result else None,
            "confidence": alert.synthesis_result.get("confidence") if alert.synthesis_result else None,
            "reasoning": alert.synthesis_result.get("reasoning") if alert.synthesis_result else None,
            "warnings": alert.synthesis_result.get("warnings", []) if alert.synthesis_result else [],
            "key_factors": alert.synthesis_result.get("key_factors", []) if alert.synthesis_result else [],
            "metadata": alert.synthesis_result.get("metadata", {}) if alert.synthesis_result else {},
        } if alert.synthesis_result else None
    )


@app.get("/api/stats")
async def get_stats(
    db: AsyncSession = Depends(get_db),
):
    """Возвращает статистику."""
    repo = AlertRepository(db)
    stats = await repo.get_stats()
    breakdown = await repo.get_recommendations_breakdown()
    
    return {
        **stats,
        "recommendations_breakdown": breakdown,
    }


# === Запуск ===

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.WEBHOOK_HOST, port=settings.WEBHOOK_PORT)
