"""
AstroFin Sentinel v5 — AstroCouncil Agent
Главный координатор всех аналитических агентов.
Гибридное взвешивание через TradingSignal.from_agents.

Все суб-агенты запускаются параллельно.
Финальный сигнал = взвешенная комбинация всех голосов.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List

from agents.base_agent import BaseAgent, AgentResponse
from agents._impl.types import TradingSignal
from agents._impl.ephemeris_decorator import require_ephemeris


# Финальные веса (сумма = 100%)
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
    
    Получает данные от всех аналитических агентов и объединяет
    через гибридное взвешивание TradingSignal.from_agents.
    
    Критично: всегда вызывает Swiss Ephemeris.
    """

    def __init__(self):
        super().__init__(
            name="AstroCouncil",
            instructions_path=None,
            domain=None,
            weight=1.0,
        )
        self._weights = HYBRID_WEIGHTS
        self._sub_agents = {}

    def register_sub_agent(self, name: str, agent) -> None:
        """Register a sub-agent."""
        self._sub_agents[name] = agent

    @require_ephemeris
    async def run(self, context: Dict[str, Any]) -> AgentResponse:
        """
        Главный метод координации.
        
        1. Swiss Ephemeris (критично)
        2. Параллельно все суб-агенты
        3. TradingSignal.from_agents для финального взвешивания
        """
        dt = context.get("datetime") or datetime.utcnow()
        symbol = context.get("symbol", "BTC")
        price = context.get("price") or context.get("current_price") or 100.0

        # 1. Критичный вызов Swiss Ephemeris
        eph = self._call_ephemeris(dt)

        # 2. Параллельный запуск всех суб-агентов
        responses = await self._run_sub_agents(context)

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
            reasoning=final_signal.summary,
            sources=[],
            metadata={
                "astro_yoga": eph.get("yoga", "unknown"),
                "astro_score": eph.get("score", 50),
                "ephemeris": {k: v for k, v in eph.items() if k != "error"},
                "total_agents": len(responses),
                "weights": self._weights,
                "final_signal": final_signal.to_dict(),
            },
        )

    async def _run_sub_agents(self, context: Dict[str, Any]) -> List[AgentResponse]:
        """Параллельно запускает всех суб-агентов."""
        # Lazy import и регистрация суб-агентов
        if not self._sub_agents:
            self._register_sub_agents()

        tasks = []
        names = []
        for name, agent in self._sub_agents.items():
            if hasattr(agent, "run"):
                tasks.append(agent.run(context))
                names.append(name)

        if not tasks:
            return []

        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        responses = []
        for name, result in zip(names, results):
            if isinstance(result, Exception):
                responses.append(AgentResponse(
                    agent_name=name,
                    signal="NEUTRAL",
                    confidence=30,
                    reasoning=f"Agent error: {str(result)[:100]}",
                    sources=[],
                    metadata={"error": True},
                ))
            else:
                responses.append(result)
        
        return responses

    def _register_sub_agents(self) -> None:
        """Регистрация всех суб-агентов."""
        try:
            from agents.fundamental_agent import FundamentalAgent
            from agents.macro_agent import MacroAgent
            from agents.quant_agent import QuantAgent
            from agents.options_flow_agent import OptionsFlowAgent
            from agents.sentiment_agent import SentimentAgent
            from agents.technical_agent import TechnicalAgent
            from agents.bull_researcher import BullResearcherAgent
            from agents.bear_researcher import BearResearcherAgent

            self._sub_agents = {
                "Fundamental": FundamentalAgent(),
                "Macro": MacroAgent(),
                "Quant": QuantAgent(),
                "OptionsFlow": OptionsFlowAgent(),
                "Sentiment": SentimentAgent(),
                "Technical": TechnicalAgent(),
                "BullResearcher": BullResearcherAgent(),
                "BearResearcher": BearResearcherAgent(),
            }
        except ImportError as e:
            # Если агенты не найдены, используем пустой dict
            self._sub_agents = {}

    def _call_ephemeris(self, dt: datetime) -> Dict[str, Any]:
        """Критичный вызов Swiss Ephemeris."""
        try:
            from core.ephemeris import calculate_planet, _julian_day, HAS_SWISS_EPHEMERIS

            if not HAS_SWISS_EPHEMERIS:
                return {"yoga": "unknown", "score": 50}

            jd = _julian_day(dt)
            jupiter = calculate_planet("jupiter", jd)
            venus = calculate_planet("venus", jd)
            mercury = calculate_planet("mercury", jd)
            mars = calculate_planet("mars", jd)
            saturn = calculate_planet("saturn", jd)
            moon = calculate_planet("moon", jd)

            score = 50
            yoga = "neutral"

            # Jupiter-Moon = expansion
            jup_moon = abs(jupiter.longitude - moon.longitude) % 360
            if jup_moon < 30 or jup_moon > 330:
                score += 15
                yoga = "jupiter_moon_trine"
            elif 85 < jup_moon < 95:
                score -= 10
                yoga = "jupiter_moon_square"

            # Venus-Moon = favor
            ven_moon = abs(venus.longitude - moon.longitude) % 360
            if ven_moon < 30 or ven_moon > 330:
                score += 10
                yoga = f"{yoga}_venus"

            # Saturn caution
            sat_moon = abs(saturn.longitude - moon.longitude) % 360
            if 85 < sat_moon < 95:
                score -= 15
                yoga = f"{yoga}_saturn_square"

            return {
                "yoga": yoga,
                "score": max(0, min(100, score)),
                "jupiter": round(jupiter.longitude, 2),
                "venus": round(venus.longitude, 2),
                "mercury": round(mercury.longitude, 2),
                "mars": round(mars.longitude, 2),
                "saturn": round(saturn.longitude, 2),
                "moon": round(moon.longitude, 2),
            }
        except Exception as e:
            return {"yoga": "error", "score": 50, "error": str(e)}


# ─── Convenience runner ────────────────────────────────────────────────────────

async def run_astro_council(context: Dict[str, Any]) -> Dict[str, Any]:
    """Runner для оркестратора."""
    agent = AstroCouncilAgent()
    result = await agent.run(context)
    return {"astro_council_signal": result.to_dict()}
