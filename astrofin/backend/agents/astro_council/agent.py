"""AstroCouncilAgent v4.4 — Production Ready."""
from __future__ import annotations
import asyncio
from datetime import datetime
from typing import Dict, Any, List

from backend.agents.base_agent import BaseAgent, AgentResponse, TradingSignal, Signal
from backend.agents.orchestra.mcp_manager import MCPManager
from backend.shared_memory.bank import SharedMemoryBank
from backend.src.aiq_compat import AgentIQ, DynamoRuntime, accelerated_graph
from backend.agents.guardrails_client import NeMoGuardrailsClient, GuardrailsConfig, SafetyLevel
from backend.logging_config import get_logger, AuditLogger

# Import all agents
from backend.agents.fundamental.fundamental_agent import FundamentalAgent
from backend.agents.macro.macro_agent import MacroAgent
from backend.agents.quant.quant_agent import QuantAgent
from backend.agents.options_flow.options_flow_agent import OptionsFlowAgent
from backend.agents.sentiment.sentiment_agent import SentimentAgent
from backend.agents.technical.technical_agent import TechnicalAgent
from backend.agents.bull_researcher.bull_researcher import BullResearcherAgent
from backend.agents.bear_researcher.bear_researcher import BearResearcherAgent
from backend.agents.risk.risk_agent import RiskAgent
from backend.agents.predictor.predictor_agent import PredictorAgent

logger = get_logger(__name__)
audit_logger = AuditLogger("AstroCouncil")

class AstroCouncilAgent(BaseAgent):
    """AstroCouncilAgent v4.4 — Production-ready orchestrator."""

    SUB_AGENTS = [
        ("fundamental", FundamentalAgent, "high"),
        ("macro", MacroAgent, "high"),
        ("quant", QuantAgent, "critical"),
        ("options_flow", OptionsFlowAgent, "critical"),
        ("sentiment", SentimentAgent, "normal"),
        ("technical", TechnicalAgent, "normal"),
        ("bull", BullResearcherAgent, "normal"),
        ("bear", BearResearcherAgent, "normal"),
        ("risk", RiskAgent, "critical"),
        ("predictor", PredictorAgent, "critical"),
    ]

    def __init__(self, use_guardrails: bool = True, use_sandbox: bool = False, use_memory: bool = True, safety_level: SafetyLevel = SafetyLevel.STANDARD):
        super().__init__(name="AstroCouncil", system_prompt="AstroFin Council")
        
        self.aiq = AgentIQ(runtime=DynamoRuntime(max_concurrency=24, latency_target_ms=650, adaptive_scaling=True))
        self.guardrails = NeMoGuardrailsClient(GuardrailsConfig(enabled=use_guardrails, safety_level=safety_level))
        self.sandbox_manager = None
        self.use_sandbox = use_sandbox
        self.memory_bank = SharedMemoryBank() if use_memory else None
        self._agents: Dict[str, BaseAgent] = {}
        
        logger.info("astro_council_initialized", agents_count=len(self.SUB_AGENTS))

    def _get_agent(self, key: str, cls: type) -> BaseAgent:
        if key not in self._agents:
            self._agents[key] = cls()
        return self._agents[key]

    @accelerated_graph()
    async def run(self, context: Dict[str, Any]) -> AgentResponse:
        self._start_time = datetime.utcnow()
        symbol = context.get("symbol", "BTC")
        price = context.get("price", context.get("current_price", 100.0))
        
        tasks = [self._run_agent(name, cls, priority, context) for name, cls, priority in self.SUB_AGENTS]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_responses = [r for r in results if isinstance(r, AgentResponse)]
        failed_count = sum(1 for r in results if isinstance(r, Exception))
        
        final_signal = TradingSignal.from_agents(symbol=symbol, responses=valid_responses, entry_price=price)
        
        guardrails_result = await self.guardrails.check_output(content=final_signal.reasoning, agent_name="AstroCouncil", context=context)
        
        duration_ms = (datetime.utcnow() - self._start_time).total_seconds() * 1000
        
        audit_logger.log_trading_signal(
            symbol=symbol, direction=final_signal.signal.value, confidence=final_signal.confidence,
            entry_price=price, stop_loss=price * (1 - final_signal.stop_loss_pct),
            targets=[], position_size=final_signal.position_size_pct, council_votes=[]
        )
        
        if self.memory_bank and final_signal.confidence > 0.6:
            await self.memory_bank.store_from_response("AstroCouncil", final_signal)

        logger.info("council_completed", symbol=symbol, direction=final_signal.signal.value, 
                    confidence=final_signal.confidence, duration_ms=duration_ms)
        
        return AgentResponse(
            agent_name="AstroCouncil", signal=final_signal.signal, confidence=final_signal.confidence,
            reasoning=guardrails_result.filtered_content, sources=[],
            metadata={"sub_agents_executed": len(valid_responses), "failed": failed_count,
                     "guardrails_passed": guardrails_result.passed, "duration_ms": duration_ms}
        )

    async def _run_agent(self, name: str, cls: type, priority: str, context: Dict[str, Any]) -> AgentResponse:
        agent_start = datetime.utcnow()
        try:
            agent = self._get_agent(name, cls)
            result = await agent.run(context)
            duration_ms = (datetime.utcnow() - agent_start).total_seconds() * 1000
            audit_logger.log_agent_decision(name, result.signal.value, result.confidence, result.reasoning, context, duration_ms)
            return result
        except Exception as e:
            logger.error("agent_failed", agent=name, error=str(e))
            return AgentResponse(agent_name=name, signal=Signal.NEUTRAL, confidence=0.0, reasoning=f"Error: {str(e)}")

    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        return await self.run(context)

    def get_stats(self) -> Dict[str, Any]:
        return {"total_agents": len(self.SUB_AGENTS), "active": len(self._agents),
                "guardrails_stats": self.guardrails.get_audit_stats(),
                "memory_stats": self.memory_bank.get_stats() if self.memory_bank else {}}
