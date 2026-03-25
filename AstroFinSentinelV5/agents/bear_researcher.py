"""
AstroFin Sentinel v5 — Bear Researcher Agent
Медвежий нарратив + рисковые факторы.
Вес в гибридном сигнале: 5%
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

from agents.base_agent import BaseAgent, AgentResponse
from agents._impl.ephemeris_decorator import require_ephemeris


class BearResearcherAgent(BaseAgent):
    """
    BearResearcher — ищет медвежий кейс.
    """

    def __init__(self):
        super().__init__(
            name="BearResearcher",
            instructions_path=None,
            domain="trading",
            weight=0.05,
        )

    @require_ephemeris
    async def run(self, state: Dict[str, Any]) -> AgentResponse:
        symbol = state.get("symbol", "BTC")
        dt = state.get("datetime") or datetime.utcnow()

        eph = self._call_ephemeris(dt)

        score = 50.0

        # Check for bearish astro
        saturn = eph.get("saturn", 0)
        mars = eph.get("mars", 0)
        moon = eph.get("moon", 0)

        if saturn and moon:
            sat_moon = abs(saturn - moon) % 360
            if 85 < sat_moon < 95:
                score += 30

        if mars and moon:
            mars_moon = abs(mars - moon) % 360
            if 85 < mars_moon < 95:
                score += 20

        # Risk factors
        current_price = state.get("current_price", 50000)
        if current_price > 70000:
            score += 15

        score = max(0, min(100, score))

        if score >= 75:
            signal = "STRONG_SELL"
        elif score >= 60:
            signal = "SELL"
        else:
            signal = "NEUTRAL"

        return AgentResponse(
            agent_name="BearResearcher",
            signal=signal,
            confidence=min(85, int(score)),
            reasoning=f"Bear researcher score: {score:.0f}/100. Saturn-Mars aspects caution.",
            sources=["Astro analysis"],
            metadata={
                "bear_score": score,
                "astro_influence": f"Yoga: {eph.get('yoga', 'unknown')}",
                "source": "astrological_bearish",
            },
        )

    def _call_ephemeris(self, dt: datetime) -> Dict:
        try:
            from core.ephemeris import calculate_planet, _julian_day, HAS_SWISS_EPHEMERIS
            if not HAS_SWISS_EPHEMERIS:
                return {"yoga": "unknown"}
            jd = _julian_day(dt)
            return {
                "saturn": calculate_planet("saturn", jd).longitude,
                "mars": calculate_planet("mars", jd).longitude,
                "moon": calculate_planet("moon", jd).longitude,
                "yoga": "bearish_aspects",
            }
        except Exception:
            return {"yoga": "unknown"}


async def run_bear_researcher(state: dict) -> dict:
    agent = BearResearcherAgent()
    result = await agent.run(state)
    return {"bear_researcher_signal": result.to_dict()}
