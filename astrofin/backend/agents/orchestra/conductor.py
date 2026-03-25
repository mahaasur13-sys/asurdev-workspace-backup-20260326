"""
ConductorAgent — Main orchestrator with NanoClaw Sandbox support.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from backend.agents.base_agent import AgentResponse, Signal
from backend.agents.orchestra.planner import PlanningAgent, Plan
from backend.agents.orchestra.mcp_manager import MCPManager
from backend.shared_memory.bank import SharedMemoryBank

logger = logging.getLogger(__name__)


class ConductorAgent:
    """
    Main orchestrator combining all agent systems.

    Integrates:
    - AgentOrchestra planning
    - MCP tool management
    - LTS Shared Memory
    - NanoClaw Sandboxes (optional)
    """

    WEIGHTS: dict[str, float] = {
        "FundamentalAgent": 0.18,
        "MacroAgent": 0.13,
        "QuantAgent": 0.12,
        "PredictorAgent": 0.12,
        "OptionsFlowAgent": 0.10,
        "SentimentAgent": 0.08,
        "TechnicalAgent": 0.07,
        "BullResearcher": 0.05,
        "BearResearcher": 0.05,
        "RiskAgent": 0.05,
        "AstroCouncil": 0.05,
    }

    def __init__(
        self,
        symbol: str = "BTCUSDT",
        use_sandbox: bool = False,
        use_mcp: bool = True,
        use_memory: bool = True,
    ) -> None:
        self.symbol = symbol
        self.use_sandbox = use_sandbox
        self.use_mcp = use_mcp
        self.planner = PlanningAgent()
        self.mcp_manager = MCPManager()
        self.memory_bank = SharedMemoryBank() if use_memory else None
        self._agent_registry: dict[str, Any] = {}
        self.logger = logger

    async def initialize(self) -> None:
        """Initialize async components."""
        self.logger.info("ConductorAgent initialized")

    async def analyze(
        self,
        user_query: str,
        timeframe: str = "SWING",
        current_price: float = 50000,
        market_context: dict[str, Any] | None = None,
    ) -> AgentResponse:
        """Run full analysis through all agents."""
        start_time = datetime.utcnow()
        context = {
            "user_query": user_query,
            "symbol": self.symbol,
            "timeframe": timeframe,
            "current_price": current_price,
            "market_context": market_context or {},
            "timestamp": start_time.isoformat(),
        }

        # 1. Create plan
        plan = await self.planner.create_plan(user_query, context)

        # 2. Execute agents
        results = await self._execute_plan(plan, context)

        # 3. Synthesize
        final_signal = self._synthesize(results, context)

        # 4. Store insights
        if self.memory_bank and final_signal.confidence > 0.6:
            await self._store_insights(final_signal, results, context)

        duration = (datetime.utcnow() - start_time).total_seconds()
        self.logger.info(
            "analysis_completed symbol=%s direction=%s confidence=%.2f duration=%.2fs",
            self.symbol,
            final_signal.signal.value,
            final_signal.confidence,
            duration,
        )

        return final_signal

    async def _execute_plan(
        self, plan: Plan, context: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Execute plan with appropriate strategy."""
        async def run_task(task_id: str, agent_name: str) -> dict[str, Any]:
            agent = self._get_agent(agent_name)
            if not agent:
                return {
                    "agent": agent_name,
                    "signal": Signal.NEUTRAL,
                    "confidence": 0.3,
                    "reasoning": f"Agent {agent_name} not found",
                }
            try:
                result = await agent.run(context)
                return {
                    "agent": agent_name,
                    "signal": result.signal,
                    "confidence": result.confidence,
                    "reasoning": result.reasoning,
                    "sources": result.sources,
                    "metadata": result.metadata,
                }
            except Exception as e:
                return {
                    "agent": agent_name,
                    "signal": Signal.NEUTRAL,
                    "confidence": 0.3,
                    "reasoning": f"Error: {str(e)}",
                }

        # Execute all tasks in parallel for now
        tasks = [run_task(t.id, t.assigned_agent) for t in plan.subtasks]
        task_results = await asyncio.gather(*tasks, return_exceptions=True)

        return [
            r if not isinstance(r, Exception) else
            {"agent": "unknown", "signal": Signal.NEUTRAL, "confidence": 0.3, "reasoning": str(r)}
            for r in task_results
        ]

    def _synthesize(
        self, results: list[dict[str, Any]], context: dict[str, Any]
    ) -> AgentResponse:
        """Synthesize agent results into final signal."""
        long_score = 0.0
        short_score = 0.0
        avoid_score = 0.0
        total_weight = 0.0
        votes = []

        for result in results:
            agent_name = result.get("agent", "unknown")
            signal = result.get("signal", Signal.NEUTRAL)
            confidence = result.get("confidence", 0.5)
            weight = self.WEIGHTS.get(agent_name, 0.05)
            total_weight += weight

            if signal == Signal.LONG:
                long_score += confidence * weight
                votes.append(f"+{agent_name}")
            elif signal == Signal.SHORT:
                short_score += confidence * weight
                votes.append(f"-{agent_name}")
            elif signal == Signal.AVOID:
                avoid_score += confidence * weight

        if total_weight == 0:
            total_weight = 1.0

        long_pct = long_score / total_weight
        short_pct = short_score / total_weight
        avoid_pct = avoid_score / total_weight

        # Risk rules
        if avoid_pct > 0.3:
            final_signal = Signal.NEUTRAL
            final_confidence = 1.0 - avoid_pct
            reasoning = f"AVOID: {avoid_pct*100:.0f}%. Stand aside."
        elif long_pct > 0.45:
            final_signal = Signal.LONG
            final_confidence = min(0.9, 0.5 + long_pct * 0.4)
            reasoning = f"Long consensus: {long_pct*100:.0f}%"
        elif short_pct > 0.45:
            final_signal = Signal.SHORT
            final_confidence = min(0.9, 0.5 + short_pct * 0.4)
            reasoning = f"Short consensus: {short_pct*100:.0f}%"
        else:
            final_signal = Signal.NEUTRAL
            final_confidence = 0.4
            reasoning = f"No consensus. Long {long_pct*100:.0f}% | Short {short_pct*100:.0f}%"

        current_price = context.get("current_price", 50000)
        rr = 1.5
        if final_signal == Signal.LONG:
            entry = current_price * 1.01
            stop = current_price * 0.97
            target = current_price * 1.06
            rr = (target - entry) / (entry - stop) if entry != stop else 1.5
        elif final_signal == Signal.SHORT:
            entry = current_price * 0.99
            stop = current_price * 1.03
            target = current_price * 0.94
            rr = (entry - target) / (stop - entry) if stop != entry else 1.5

        return AgentResponse(
            agent_name="ConductorAgent",
            signal=final_signal,
            confidence=final_confidence,
            reasoning=reasoning,
            sources=[],
            metadata={
                "symbol": self.symbol,
                "timeframe": context.get("timeframe", "SWING"),
                "current_price": current_price,
                "risk_reward": round(rr, 2),
                "council_votes": votes,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    async def _store_insights(
        self,
        final_signal: AgentResponse,
        results: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> None:
        """Store insights in LTS memory."""
        if not self.memory_bank:
            return
        try:
            await self.memory_bank.store_from_response(
                "ConductorAgent",
                final_signal,
                importance=min(1.0, final_signal.confidence + 0.1),
            )
        except Exception as e:
            self.logger.error("Failed to store insights: %s", e)

    def _get_agent(self, agent_name: str) -> Any | None:
        """Get or create agent instance."""
        if agent_name in self._agent_registry:
            return self._agent_registry[agent_name]

        # Lazy import and create
        agent_map = {
            "FundamentalAgent": ("backend.agents.fundamental.fundamental_agent", "FundamentalAgent"),
            "MacroAgent": ("backend.agents.macro.macro_agent", "MacroAgent"),
            "QuantAgent": ("backend.agents.quant.quant_agent", "QuantAgent"),
            "PredictorAgent": ("backend.agents.predictor.predictor_agent", "PredictorAgent"),
            "OptionsFlowAgent": ("backend.agents.options_flow.options_flow_agent", "OptionsFlowAgent"),
            "SentimentAgent": ("backend.agents.sentiment.sentiment_agent", "SentimentAgent"),
            "TechnicalAgent": ("backend.agents.technical.technical_agent", "TechnicalAgent"),
            "BullResearcherAgent": ("backend.agents.bull_researcher.bull_researcher", "BullResearcherAgent"),
            "BearResearcherAgent": ("backend.agents.bear_researcher.bear_researcher", "BearResearcherAgent"),
            "RiskAgent": ("backend.agents.risk.risk_agent", "RiskAgent"),
            "AstroCouncilAgent": ("backend.agents.astro_council.agent", "AstroCouncilAgent"),
        }

        if agent_name not in agent_map:
            return None

        try:
            from importlib import import_module
            module_path, cls_name = agent_map[agent_name]
            module = import_module(module_path)
            cls = getattr(module, cls_name, None)
            if cls:
                self._agent_registry[agent_name] = cls()
                return self._agent_registry[agent_name]
        except Exception as e:
            self.logger.warning("Failed to load agent %s: %s", agent_name, e)

        return None
