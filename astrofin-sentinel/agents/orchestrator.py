"""
Оркестратор — центральный диспетчер AstroFin Sentinel.

Управляет всеми 11 агентами и обеспечивает:
- Параллельное/последовательное выполнение
- Result aggregation от всех агентов
- Финальный синтез
- Alert tracking
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
import uuid
import logging
import asyncio

from .base import AgentInput, AgentOutput
from .agent_registry import AgentFactory, AgentTeam

logger = logging.getLogger(__name__)


@dataclass
class Alert:
    """TradingView Alert с трекингом статуса и результатами всех агентов."""
    id: str
    symbol: str
    action: str
    price: float
    quantity: float | None
    strategy: str
    timeframe: str
    ml_confidence: float
    astro_signal: bool
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    
    # Все агенты
    market_analyst_result: AgentOutput | None = None
    bull_result: AgentOutput | None = None
    bear_result: AgentOutput | None = None
    cycle_result: AgentOutput | None = None
    astro_council_result: AgentOutput | None = None
    gann_result: AgentOutput | None = None
    elliot_result: AgentOutput | None = None
    bradley_result: AgentOutput | None = None
    sentiment_result: AgentOutput | None = None
    risk_result: AgentOutput | None = None
    timewindow_result: AgentOutput | None = None
    synthesis_result: AgentOutput | None = None
    
    # Debate результат
    debate_result: dict | None = None
    
    # Метаданные
    processing_time_ms: float | None = None
    error: str | None = None
    
    def to_dict(self) -> dict:
        """Конвертирует в dict."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "action": self.action,
            "price": self.price,
            "status": self.status,
            "error": self.error,
            "processing_time_ms": self.processing_time_ms,
            "results": {
                "market_analyst": self.market_analyst_result.model_dump() if self.market_analyst_result else None,
                "bull": self.bull_result.model_dump() if self.bull_result else None,
                "bear": self.bear_result.model_dump() if self.bear_result else None,
                "cycle": self.cycle_result.model_dump() if self.cycle_result else None,
                "astro_council": self.astro_council_result.model_dump() if self.astro_council_result else None,
                "gann": self.gann_result.model_dump() if self.gann_result else None,
                "elliot": self.elliot_result.model_dump() if self.elliot_result else None,
                "bradley": self.bradley_result.model_dump() if self.bradley_result else None,
                "sentiment": self.sentiment_result.model_dump() if self.sentiment_result else None,
                "risk": self.risk_result.model_dump() if self.risk_result else None,
                "timewindow": self.timewindow_result.model_dump() if self.timewindow_result else None,
                "synthesis": self.synthesis_result.model_dump() if self.synthesis_result else None,
            },
            "debate": self.debate_result,
        }


class Orchestrator:
    """
    Оркестратор всех 11 агентов AstroFin Sentinel.
    
    Режимы работы:
    - mode="quick": MarketAnalyst + Bull/Bear + Synthesis
    - mode="standard": Core agents + AstroCouncil + RiskAgent
    - mode="full": Все 11 агентов + DebateModerator
    """
    
    def __init__(self, mode: str = "standard", use_langchain: bool = True):
        """
        Инициализирует оркестратор.
        
        Args:
            mode: 'quick' | 'standard' | 'full'
            use_langchain: Использовать LangChain agents (default: True)
        """
        self.mode = mode
        self.use_langchain = use_langchain
        
        # Создаём команду агентов
        if mode == "quick":
            agent_names = [
                "MarketAnalyst",
                "BullResearcher", 
                "BearResearcher",
                "DebateModerator",
                "SynthesisEngine",
            ]
        elif mode == "standard":
            agent_names = [
                "MarketAnalyst",
                "BullResearcher",
                "BearResearcher",
                "DebateModerator",
                "CycleAgent",
                "AstroCouncil",
                "SentimentAgent",
                "RiskAgent",
                "SynthesisEngine",
            ]
        else:  # full
            agent_names = list([
                "MarketAnalyst",
                "BullResearcher",
                "BearResearcher",
                "DebateModerator",
                "CycleAgent",
                "AstroCouncil",
                "GannAgent",
                "ElliotAgent",
                "BradleyAgent",
                "SentimentAgent",
                "RiskAgent",
                "TimeWindowAgent",
                "SynthesisEngine",
            ])
        
        self.team = AgentTeam(agents=agent_names)
        
        # Кэш активных алертов
        self._alerts: dict[str, Alert] = {}
        
        logger.info(f"[Orchestrator] Initialized in {mode} mode with {len(agent_names)} agents")
    
    async def process_alert(self, raw_data: dict) -> Alert:
        """
        Обрабатывает входящий TradingView alert.
        
        Returns:
            Alert с заполненными результатами всех агентов
        """
        start_time = datetime.utcnow()
        
        # Создаём Alert
        alert_id = raw_data.get("alert_id") or str(uuid.uuid4())[:8]
        
        alert = Alert(
            id=alert_id,
            symbol=raw_data.get("symbol", "UNKNOWN"),
            action=raw_data.get("action", "hold"),
            price=float(raw_data.get("price", 0)),
            quantity=raw_data.get("quantity"),
            strategy=raw_data.get("strategy", "unknown"),
            timeframe=raw_data.get("timeframe", "1h"),
            ml_confidence=float(raw_data.get("ml_confidence", 0.5)),
            astro_signal=bool(raw_data.get("astro_signal", False)),
        )
        
        self._alerts[alert_id] = alert
        alert.status = "processing"
        
        logger.info(f"[Orchestrator] Processing #{alert_id}: {alert.symbol} {alert.action} ({self.mode})")
        
        try:
            # Формируем AgentInput
            input_data = AgentInput(
                symbol=alert.symbol,
                action=alert.action,
                price=alert.price,
                quantity=alert.quantity,
                strategy=alert.strategy,
                timeframe=alert.timeframe,
                ml_confidence=alert.ml_confidence,
                astro_signal=alert.astro_signal,
                raw_data=raw_data,
            )
            
            # === PHASE 1: Quick analysis (always runs) ===
            quick_agents = ["MarketAnalyst", "BullResearcher", "BearResearcher"]
            
            tasks = {}
            for name in quick_agents:
                agent = self.team.get_agent(name)
                if agent:
                    tasks[name] = asyncio.create_task(agent.analyze(input_data))
            
            # Запускаем параллельно
            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            
            for (name, task), result in zip(tasks.items(), results):
                if isinstance(result, Exception):
                    logger.warning(f"[Orchestrator] {name} error: {result}")
                    setattr(alert, f"{name.lower().replace(' ', '_').replace('researcher', 'result').replace('analyst', 'result')}Result", None)
                else:
                    attr_name = self._get_result_attr(name)
                    setattr(alert, attr_name, result)
            
            # === PHASE 2: Extended analysis (standard/full modes) ===
            if self.mode in ("standard", "full"):
                extended_agents = []
                
                if self.team.get_agent("CycleAgent"):
                    extended_agents.append("CycleAgent")
                if self.team.get_agent("AstroCouncil"):
                    extended_agents.append("AstroCouncil")
                if self.team.get_agent("SentimentAgent"):
                    extended_agents.append("SentimentAgent")
                if self.team.get_agent("RiskAgent"):
                    extended_agents.append("RiskAgent")
                
                if self.mode == "full":
                    extended_agents.extend([
                        "GannAgent", "ElliotAgent", 
                        "BradleyAgent", "TimeWindowAgent"
                    ])
                
                # Запускаем параллельно
                ext_tasks = {}
                for name in extended_agents:
                    agent = self.team.get_agent(name)
                    if agent:
                        ext_tasks[name] = asyncio.create_task(agent.analyze(input_data))
                
                ext_results = await asyncio.gather(*ext_tasks.values(), return_exceptions=True)
                
                for (name, task), result in zip(ext_tasks.items(), ext_results):
                    if isinstance(result, Exception):
                        logger.warning(f"[Orchestrator] {name} error: {result}")
                    else:
                        attr_name = self._get_result_attr(name)
                        setattr(alert, attr_name, result)
            
            # === PHASE 3: Debate Moderator ===
            moderator = self.team.get_agent("DebateModerator")
            if moderator and alert.bull_result and alert.bear_result:
                try:
                    debate_result = await moderator.moderate(
                        alert.bull_result,
                        alert.bear_result,
                        input_data,
                    )
                    alert.debate_result = debate_result.model_dump() if hasattr(debate_result, 'model_dump') else debate_result
                except Exception as e:
                    logger.warning(f"[Orchestrator] Debate error: {e}")
            
            # === PHASE 4: Synthesis ===
            synthesis = self.team.get_agent("SynthesisEngine")
            if synthesis:
                alert.synthesis_result = await synthesis.analyze(input_data, parallel=False)
            
            alert.status = "completed"
            
            elapsed = (datetime.utcnow() - start_time).total_seconds()
            logger.info(
                f"[Orchestrator] #{alert_id} completed in {elapsed:.1f}s: "
                f"{alert.synthesis_result.recommendation if alert.synthesis_result else 'N/A'}"
            )
            
        except Exception as e:
            alert.status = "failed"
            alert.error = str(e)
            logger.error(f"[Orchestrator] #{alert_id} failed: {e}")
        
        finally:
            alert.completed_at = datetime.utcnow()
            alert.processing_time_ms = (alert.completed_at - start_time).total_seconds() * 1000
        
        return alert
    
    def _get_result_attr(self, agent_name: str) -> str:
        """Маппинг имени агента -> имя атрибута результата."""
        mapping = {
            "MarketAnalyst": "market_analyst_result",
            "BullResearcher": "bull_result",
            "BearResearcher": "bear_result",
            "CycleAgent": "cycle_result",
            "AstroCouncil": "astro_council_result",
            "GannAgent": "gann_result",
            "ElliotAgent": "elliot_result",
            "BradleyAgent": "bradley_result",
            "SentimentAgent": "sentiment_result",
            "RiskAgent": "risk_result",
            "TimeWindowAgent": "timewindow_result",
            "SynthesisEngine": "synthesis_result",
        }
        return mapping.get(agent_name, f"{agent_name.lower()}_result")
    
    def get_alert(self, alert_id: str) -> Alert | None:
        """Возвращает Alert по ID."""
        return self._alerts.get(alert_id)
    
    def get_summary(self) -> dict[str, Any]:
        """Возвращает статистику оркестратора."""
        alerts = list(self._alerts.values())
        
        return {
            "mode": self.mode,
            "agent_count": len(self.team.get_names()),
            "agents": self.team.get_names(),
            "total_alerts": len(alerts),
            "by_status": {
                "pending": len([a for a in alerts if a.status == "pending"]),
                "processing": len([a for a in alerts if a.status == "processing"]),
                "completed": len([a for a in alerts if a.status == "completed"]),
                "failed": len([a for a in alerts if a.status == "failed"]),
            },
            "recent_symbols": list(set([a.symbol for a in alerts[-10:]])),
        }
