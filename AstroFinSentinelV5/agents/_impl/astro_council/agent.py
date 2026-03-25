"""
AstroCouncil Agent — Главный координатор всех суб-агентов.
Гибридное взвешивание через TradingSignal.from_agents.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List

from agents.base_agent import BaseAgent
from agents._impl.types import AgentResponse, TradingSignal
from agents._impl.ephemeris_decorator import require_ephemeris


# Weights для гибридного анализа (сумма = 100%)
HYBRID_WEIGHTS = {
    "Fundamental": 0.20,
    "Macro": 0.15,
    "Quant": 0.20,
    "OptionsFlow": 0.15,
    "Sentiment": 0.10,
    "Technical": 0.10,
    "BullResearcher": 0.05,
    "BearResearcher": 0.05,
}


class AstroCouncilAgent(BaseAgent):
    """
    AstroCouncil — координатор всех агентов.
    
    Получает данные от всех аналитических агентов:
    - FundamentalAgent (20%)
    - MacroAgent (15%)
    - QuantAgent (20%)
    - OptionsFlowAgent (15%)
    - SentimentAgent (10%)
    - TechnicalAgent (10%)
    - BullResearcher (5%)
    - BearResearcher (5%)
    
    Объединяет через гибридное взвешивание TradingSignal.from_agents.
    """

    def __init__(self):
        super().__init__(
            name="AstroCouncil",
            instructions_path=None,
            domain=None,
            weight=1.0,
        )
        self._sub_agents = {}
        self._weights = HYBRID_WEIGHTS

    def register_sub_agent(self, name: str, agent) -> None:
        """Register a sub-agent for coordination."""
        self._sub_agents[name] = agent

    @require_ephemeris
    async def run(self, context: Dict[str, Any]) -> AgentResponse:
        """
        Главный метод координации.
        
        1. Вызывает Swiss Ephemeris (критично)
        2. Параллельно запускает всех суб-агентов
        3. Объединяет через TradingSignal.from_agents
        """
        dt = context.get("datetime") or datetime.now()
        symbol = context.get("symbol", "BTC")
        price = context.get("price") or context.get("current_price") or 100.0

        # 1. Критичный вызов Swiss Ephemeris
        eph = self._call_ephemeris(dt)

        # 2. Параллельный запуск всех суб-агентов
        responses = await self._run_all_agents(context)

        # 3. Гибридное взвешивание
        final_signal = TradingSignal.from_agents(
            symbol=symbol,
            responses=responses,
            entry_price=price,
            weights=self._weights,
        )

        return AgentResponse(
            agent_name="AstroCouncil",
            signal=final_signal.signal.value,
            confidence=final_signal.confidence,
            summary=final_signal.summary,
            details={
                "ephemeris": eph,
                "sub_agents": [r.to_dict() for r in responses],
                "weights": self._weights,
                "final_signal": final_signal.to_dict(),
            },
            metadata={
                "astro_yoga": eph.get("yoga", "unknown"),
                "astro_score": eph.get("score", 50),
                "total_agents": len(responses),
            },
        )

    async def _run_all_agents(self, context: Dict[str, Any]) -> List[AgentResponse]:
        """Параллельно запускает всех зарегистрированных суб-агентов."""
        tasks = []
        agent_names = []

        for name, agent in self._sub_agents.items():
            if hasattr(agent, "run"):
                tasks.append(agent.run(context))
                agent_names.append(name)

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            responses = []
            for name, result in zip(agent_names, results):
                if isinstance(result, Exception):
                    # Fallback при ошибке агента
                    responses.append(AgentResponse(
                        agent_name=name,
                        signal="NEUTRAL",
                        confidence=30,
                        summary=f"Agent error: {str(result)[:50]}",
                    ))
                else:
                    responses.append(result)
            return responses

        # Fallback: возвращаем пустые ответы если нет агентов
        return [
            AgentResponse(
                agent_name=name,
                signal="NEUTRAL",
                confidence=30,
                summary="Agent not registered",
            )
            for name in self._weights.keys()
        ]

    def _call_ephemeris(self, dt: datetime) -> Dict[str, Any]:
        """Критичный вызов Swiss Ephemeris."""
        try:
            from core.ephemeris import calculate_planet, _julian_day, HAS_SWISS_EPHEMERIS

            if not HAS_SWISS_EPHEMERIS:
                return {"yoga": "unknown", "score": 50}

            jd = _julian_day(dt)

            # Get key planets
            jupiter = calculate_planet("jupiter", jd)
            venus = calculate_planet("venus", jd)
            mercury = calculate_planet("mercury", jd)
            mars = calculate_planet("mars", jd)
            saturn = calculate_planet("saturn", jd)
            moon = calculate_planet("moon", jd)

            # Simple yoga calculation
            score = 50
            yoga = "neutral"

            # Jupiter aspects (generally bullish)
            jup_moon_diff = abs(jupiter.longitude - moon.longitude) % 360
            if jup_moon_diff < 30 or jup_moon_diff > 330:
                score += 10
                yoga = "jupiter_moon_trine"
            elif 85 < jup_moon_diff < 95:
                score -= 5
                yoga = "jupiter_moon_square"

            # Venus favorable
            ven_moon_diff = abs(venus.longitude - moon.longitude) % 360
            if ven_moon_diff < 30 or ven_moon_diff > 330:
                score += 8
                yoga = f"{yoga}_venus"

            # Saturn caution
            sat_moon_diff = abs(saturn.longitude - moon.longitude) % 360
            if 85 < sat_moon_diff < 95:
                score -= 10
                yoga = f"{yoga}_saturn_square"

            return {
                "yoga": yoga,
                "score": max(0, min(100, score)),
                "jupiter": jupiter.longitude,
                "venus": venus.longitude,
                "mercury": mercury.longitude,
                "mars": mars.longitude,
                "saturn": saturn.longitude,
                "moon": moon.longitude,
            }
        except Exception as e:
            return {"yoga": "error", "score": 50, "error": str(e)}


# ─── Convenience runners ──────────────────────────────────────────────────────

async def run_astro_council(context: Dict[str, Any]) -> Dict[str, Any]:
    """Runner для оркестратора."""
    agent = AstroCouncilAgent()

    # Register all sub-agents
    from agents.fundamental_agent import FundamentalAgent
    from agents.macro_agent import MacroAgent
    from agents.quant_agent import QuantAgent
    from agents.options_flow_agent import OptionsFlowAgent
    from agents.sentiment_agent import SentimentAgent
    from agents.technical_agent import TechnicalAgent
    from agents.bull_researcher import BullResearcherAgent
    from agents.bear_researcher import BearResearcherAgent

    agent.register_sub_agent("Fundamental", FundamentalAgent())
    agent.register_sub_agent("Macro", MacroAgent())
    agent.register_sub_agent("Quant", QuantAgent())
    agent.register_sub_agent("OptionsFlow", OptionsFlowAgent())
    agent.register_sub_agent("Sentiment", SentimentAgent())
    agent.register_sub_agent("Technical", TechnicalAgent())
    agent.register_sub_agent("BullResearcher", BullResearcherAgent())
    agent.register_sub_agent("BearResearcher", BearResearcherAgent())

    result = await agent.run(context)
    return {"astro_council_signal": result.to_dict()}
