"""
AstroFin Sentinel v5 — Bull Researcher Agent
Бычий нарратив + сильные астрологические факторы.
Вес в гибридном сигнале: 5%
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

from agents.base_agent import BaseAgent, AgentResponse
from agents._impl.ephemeris_decorator import require_ephemeris


class BullResearcherAgent(BaseAgent):
    """
    BullResearcher — ищет бычий кейс.
    """

    def __init__(self):
        super().__init__(
            name="BullResearcher",
            instructions_path=None,
            domain="trading",
            weight=0.05,
        )

    @require_ephemeris
    async def run(self, state: Dict[str, Any]) -> AgentResponse:
        symbol = state.get("symbol", "BTC")
        dt = state.get("datetime") or datetime.utcnow()

        eph = self._call_ephemeris(dt)

        # Bullish indicators
        score = 50.0

        # Check for bullish astro
        jupiter = eph.get("jupiter", 0)
        moon = eph.get("moon", 0)
        venus = eph.get("venus", 0)

        if jupiter and moon:
            jup_moon = abs(jupiter - moon) % 360
            if jup_moon < 30 or jup_moon > 330:
                score += 30

        if venus and moon:
            ven_moon = abs(venus - moon) % 360
            if ven_moon < 30 or ven_moon > 330:
                score += 20

        # Bullish market conditions
        current_price = state.get("current_price", 50000)
        if current_price < 55000:  # Assume discounted
            score += 10

        score = max(0, min(100, score))

        if score >= 75:
            signal = "STRONG_BUY"
        elif score >= 60:
            signal = "BUY"
        else:
            signal = "NEUTRAL"

        return AgentResponse(
            agent_name="BullResearcher",
            signal=signal,
            confidence=min(85, int(score)),
            reasoning=f"Bull researcher score: {score:.0f}/100. Jupiter-Moon aspects favorable.",
            sources=["Astro analysis"],
            metadata={
                "bull_score": score,
                "astro_influence": f"Yoga: {eph.get('yoga', 'unknown')}",
                "source": "astrological_bullish",
            },
        )

    def _call_ephemeris(self, dt: datetime) -> Dict:
        try:
            from core.ephemeris import calculate_planet, _julian_day, HAS_SWISS_EPHEMERIS
            if not HAS_SWISS_EPHEMERIS:
                return {"yoga": "unknown"}
            jd = _julian_day(dt)
            return {
                "jupiter": calculate_planet("jupiter", jd).longitude,
                "venus": calculate_planet("venus", jd).longitude,
                "moon": calculate_planet("moon", jd).longitude,
                "yoga": "bullish_aspects",
            }
        except Exception:
            return {"yoga": "unknown"}


async def run_bull_researcher(state: dict) -> dict:
    agent = BullResearcherAgent()
    result = await agent.run(state)
    return {"bull_researcher_signal": result.to_dict()}
