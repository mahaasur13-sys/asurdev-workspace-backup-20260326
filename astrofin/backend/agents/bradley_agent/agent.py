"""
Bradley Agent — Bradley Model (astro-price model).
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

from backend.agents.base_agent import BaseAgent
from backend.agents.base_agent import AgentResponse, Signal
from backend.core.decorators import require_ephemeris


class BradleyAgent(BaseAgent):
    """
    Bradley Model (astro-price model).
    Вес: 3%
    """

    def __init__(self):
        super().__init__(
            name="BradleyAgent",
            domain="bradley",
            weight=0.03,
            instructions="Bradley Model analysis agent",
        )

    @require_ephemeris
    async def run(self, state: Dict[str, Any]) -> AgentResponse:
        now = datetime.now()
        bradley = self._calculate_bradley(now)

        score = 50
        if bradley["squat"]:
            score += 30
        if bradley["aspect_quality"] == "strong":
            score += 20

        score = min(100, score)

        if score >= 70:
            final_signal = Signal.STRONG_BUY
        elif score >= 55:
            final_signal = Signal.BUY
        else:
            final_signal = Signal.NEUTRAL

        reasoning = (
            f"Bradley model: {bradley['phase']}. "
            f"Squat: {'Yes' if bradley['squat'] else 'No'}. "
            f"Aspect quality: {bradley['aspect_quality']}."
        )

        return AgentResponse(
            agent_name=self.name,
            signal=final_signal,
            confidence=score / 100,
            score=score,
            reasoning=reasoning,
            sources=["bradley/model.md"],
            metadata={"bradley": bradley},
        )

    def _calculate_bradley(self, dt: datetime) -> Dict:
        """Calculate Bradley model values."""
        # Simplified Bradley calculation
        # Based on planetary aspects creating price turning points
        jd = self._to_julian_day(dt)

        # Simplified planetary positions
        sun = (jd * 360 / 365.25) % 360  # Simplified
        moon = (jd * 360 / 27.32) % 360  # Draconic month

        # Key aspects (conjunction, opposition, square, trine)
        diff = abs(sun - moon) % 360
        if diff < 15 or abs(diff - 180) < 15:
            aspect = "strong"
        elif diff < 30 or abs(diff - 180) < 30:
            aspect = "moderate"
        else:
            aspect = "weak"

        # Phase
        if diff < 90:
            phase = "waxing"
        elif diff < 180:
            phase = "full"
        elif diff < 270:
            phase = "waning"
        else:
            phase = "new"

        return {
            "aspect": aspect,
            "aspect_quality": "strong" if aspect == "strong" else "moderate",
            "phase": phase,
            "squat": aspect == "strong" and phase in ["waxing", "full"],
            "julian_day": jd,
        }

    def _to_julian_day(self, dt: datetime) -> float:
        """Convert datetime to Julian Day."""
        a = (14 - dt.month) // 12
        y = dt.year + 4800 - a
        m = dt.month + 12 * a - 3
        jdn = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
        return jdn + (dt.hour - 12) / 24.0 + dt.minute / 1440.0 + dt.second / 86400.0
