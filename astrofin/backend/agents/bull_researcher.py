"""
Bull Researcher Agent — бычий кейс с астрологией.
"""

from __future__ import annotations
from datetime import datetime
from typing import Dict, Any

from .base_agent import BaseAgent, AgentResponse
from backend.src.decorators import require_ephemeris


class BullResearcher(BaseAgent):
    """Бычий исследователь — ищет позитивные астрологические и рыночные факторы."""

    def __init__(self):
        super().__init__(
            name="BullResearcher",
            system_prompt="Ты — бычий аналитик. Ищи сильные позитивные сигналы."
        )

    @require_ephemeris
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        dt = context.get("datetime") or datetime.now()
        eph = await self._call_ephemeris(dt)

        panchanga = eph.get("panchanga", {})
        yoga_cat = panchanga.get("yoga_category", "Neutral")

        score = 75 if yoga_cat == "Auspicious" else 55 if yoga_cat == "Neutral" else 35

        return AgentResponse(
            agent_name="BullResearcher",
            signal="BUY" if score >= 60 else "NEUTRAL",
            confidence=score,
            reasoning=f"Bull case: {score}%",
            metadata={
                "yoga": panchanga.get("yoga"),
                "nakshatra": panchanga.get("nakshatra"),
                "vara": panchanga.get("vara")
            }
        )

    async def _call_ephemeris(self, dt: datetime) -> Dict:
        from backend.src.swiss_ephemeris import swiss_ephemeris

        date_str = dt.strftime("%Y-%m-%d")
        time_str = dt.strftime("%H:%M:%S")
        return swiss_ephemeris(
            date=date_str,
            time=time_str,
            lat=40.7128,
            lon=-74.0060,
            ayanamsa="lahiri",
            compute_panchanga=True
        )
