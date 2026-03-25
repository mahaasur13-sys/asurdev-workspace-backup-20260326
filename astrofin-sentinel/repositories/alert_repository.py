"""
Репозиторий для работы с Alert записями в БД.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AlertRecord
import logging

logger = logging.getLogger(__name__)


class AlertRepository:
    """Репозиторий для Alert записей."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create(self, data: dict) -> AlertRecord:
        """Создаёт новую запись Alert."""
        alert = AlertRecord(
            id=data.get("id"),
            symbol=data.get("symbol", "UNKNOWN").upper(),
            action=data.get("action", "hold"),
            price=float(data.get("price", 0)),
            quantity=data.get("quantity"),
            strategy=data.get("strategy", "unknown"),
            timeframe=data.get("timeframe", "1h"),
            ml_confidence=float(data.get("ml_confidence", 0.5)),
            astro_signal=bool(data.get("astro_signal", False)),
            status="pending",
            received_at=datetime.utcnow(),
            raw_data=data.get("raw_data"),
        )
        self.db.add(alert)
        await self.db.commit()
        await self.db.refresh(alert)
        logger.info(f"[DB] Created alert {alert.id}")
        return alert
    
    async def get_by_id(self, alert_id: str) -> Optional[AlertRecord]:
        """Получает Alert по ID."""
        result = await self.db.execute(
            select(AlertRecord).where(AlertRecord.id == alert_id)
        )
        return result.scalar_one_or_none()
    
    async def update_status(
        self,
        alert_id: str,
        status: str,
        error: Optional[str] = None
    ) -> Optional[AlertRecord]:
        """Обновляет статус Alert."""
        alert = await self.get_by_id(alert_id)
        if not alert:
            return None
        
        alert.status = status
        if status == "processing":
            alert.started_at = datetime.utcnow()
        elif status in ("completed", "failed"):
            alert.completed_at = datetime.utcnow()
            if alert.started_at:
                delta = alert.completed_at - alert.started_at
                alert.processing_time_ms = delta.total_seconds() * 1000
        
        if error:
            alert.error = error
        
        await self.db.commit()
        await self.db.refresh(alert)
        return alert
    
    async def update_results(
        self,
        alert_id: str,
        tech_result: Optional[dict] = None,
        astro_result: Optional[dict] = None,
        synthesis_result: Optional[dict] = None,
    ) -> Optional[AlertRecord]:
        """Обновляет результаты агентов."""
        alert = await self.get_by_id(alert_id)
        if not alert:
            return None
        
        if tech_result:
            alert.tech_result = tech_result
        if astro_result:
            alert.astro_result = astro_result
        if synthesis_result:
            alert.synthesis_result = synthesis_result
        
        await self.db.commit()
        await self.db.refresh(alert)
        return alert
    
    async def mark_notification_sent(
        self,
        alert_id: str,
        channel: str
    ) -> Optional[AlertRecord]:
        """Отмечает что уведомление отправлено."""
        alert = await self.get_by_id(alert_id)
        if not alert:
            return None
        
        now = datetime.utcnow()
        if channel == "telegram":
            alert.telegram_sent = True
            alert.telegram_sent_at = now
        elif channel == "sms":
            alert.sms_sent = True
            alert.sms_sent_at = now
        
        await self.db.commit()
        await self.db.refresh(alert)
        return alert
    
    async def get_recent(self, limit: int = 10) -> list[AlertRecord]:
        """Получает последние алерты."""
        result = await self.db.execute(
            select(AlertRecord)
            .order_by(AlertRecord.received_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_by_symbol(
        self,
        symbol: str,
        limit: int = 10
    ) -> list[AlertRecord]:
        """Получает алерты по символу."""
        result = await self.db.execute(
            select(AlertRecord)
            .where(AlertRecord.symbol == symbol.upper())
            .order_by(AlertRecord.received_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def get_stats(self) -> dict:
        """Возвращает статистику."""
        total = await self.db.scalar(select(func.count(AlertRecord.id)))
        
        completed = await self.db.scalar(
            select(func.count(AlertRecord.id))
            .where(AlertRecord.status == "completed")
        )
        
        failed = await self.db.scalar(
            select(func.count(AlertRecord.id))
            .where(AlertRecord.status == "failed")
        )
        
        pending = await self.db.scalar(
            select(func.count(AlertRecord.id))
            .where(AlertRecord.status == "pending")
        )
        
        processing = await self.db.scalar(
            select(func.count(AlertRecord.id))
            .where(AlertRecord.status == "processing")
        )
        
        # Среднее время обработки
        avg_time_result = await self.db.execute(
            select(func.avg(AlertRecord.processing_time_ms))
            .where(AlertRecord.processing_time_ms.isnot(None))
        )
        avg_time = avg_time_result.scalar()
        
        return {
            "total": total or 0,
            "completed": completed or 0,
            "failed": failed or 0,
            "pending": pending or 0,
            "processing": processing or 0,
            "avg_processing_time_ms": round(avg_time, 2) if avg_time else 0,
        }
    
    async def get_recommendations_breakdown(self) -> dict:
        """Статистика по рекомендациям."""
        result = await self.db.execute(
            select(
                AlertRecord.synthesis_result["recommendation"].astext.label("rec"),
                func.count(AlertRecord.id).label("count")
            )
            .where(AlertRecord.synthesis_result.isnot(None))
            .group_by(AlertRecord.synthesis_result["recommendation"].astext)
        )
        
        return {row.rec: row.count for row in result.all()}
