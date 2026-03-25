"""
DowAgent — Dow Theory confirmation.
"""

from __future__ import annotations

from typing import Dict, Any
from backend.agents.base_agent import BaseAgent, AgentResponse, Signal
from backend.src.decorators import require_ephemeris
from backend.src.swiss_ephemeris import swiss_ephemeris


class DowAgent(BaseAgent):
    """Dow Theory — trend confirmation."""

    def __init__(self):
        super().__init__(
            name="DowAgent",
            system_prompt="Подтверждение по Dow Theory: Higher Highs/Lows, index correlation.",
        )

    @require_ephemeris
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        dt = context.get("datetime")

        if dt is None:
            from datetime import datetime
            dt = datetime.now()

        date_str = dt.strftime("%Y-%m-%d")
        time_str = dt.strftime("%H:%M:%S")
        eph = swiss_ephemeris(date=date_str, time=time_str, lat=40.7128, lon=-74.0060, ayanamsa="lahiri")

        # Dow Theory signals (simplified)
        trend = "uptrend"  # Placeholder
        confirmation = True

        if trend == "uptrend" and confirmation:
            signal = Signal.BUY
            confidence = 60
            summary = "Dow: подтверждённый восходящий тренд"
        elif trend == "downtrend" and confirmation:
            signal = Signal.SELL
            confidence = 60
            summary = "Dow: подтверждённый нисходящий тренд"
        else:
            signal = Signal.NEUTRAL
            confidence = 50
            summary = "Dow: нет подтверждения тренда"

        return AgentResponse(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=summary,
            metadata={"trend": trend, "confirmation": confirmation, **eph},
        )
