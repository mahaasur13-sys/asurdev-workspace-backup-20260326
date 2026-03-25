"""
HealthAstroAgent — Medical Astrology.
Медицинская астрология и выбор времени для операций.
"""
from __future__ import annotations
from datetime import datetime
from typing import Dict, Any
from ..base_agent import BaseAgent, AgentResponse, Signal
from ...src.swiss_ephemeris import swiss_ephemeris

class HealthAstroAgent(BaseAgent):
    """HealthAstroAgent — медицинская астрология. Вес: 0.08"""
    HEALTHY_SIGNS = ["Cancer", "Leo", "Virgo", "Pisces"]
    WEAK_SIGNS = ["Aries", "Scorpio", "Capricorn"]

    def __init__(self):
        super().__init__(
            name="HealthAstroAgent",
            system_prompt="Medical Astrology — health timing and analysis"
        )

    async def run(self, context: Dict[str, Any]) -> AgentResponse:
        now = datetime.utcnow()
        try:
            eph = swiss_ephemeris(
                date=now.strftime("%Y-%m-%d"),
                time=now.strftime("%H:%M:%S"),
                compute_panchanga=False
            )
        except Exception as e:
            return AgentResponse(
                agent_name=self.name, signal=Signal.NEUTRAL, confidence=0.3,
                reasoning=f"Health astro error: {e}", sources=["medical_astrology.md"],
            )

        moon = eph.get("planets", {}).get("moon", {}).get("sign", "Aries")
        sun = eph.get("planets", {}).get("sun", {}).get("sign", "Aries")

        score = 0.5
        if moon in self.HEALTHY_SIGNS:
            score += 0.2
        if sun in self.HEALTHY_SIGNS:
            score += 0.15
        if moon in self.WEAK_SIGNS:
            score -= 0.15

        signal = Signal.LONG if score > 0.6 else Signal.NEUTRAL
        return AgentResponse(
            agent_name=self.name, signal=signal, confidence=min(score, 0.9),
            reasoning=f"Health indicators: Moon={moon}, Sun={sun}",
            sources=["medical_astrology.md"],
            metadata={"moon_sign": moon, "sun_sign": sun, "score": score},
        )
