"""
MeridianAgent — Meridian trend lines.
"""

from __future__ import annotations

from typing import Dict, Any
from backend.agents.base_agent import BaseAgent, AgentResponse, Signal
from backend.src.decorators import require_ephemeris
from backend.src.swiss_ephemeris import swiss_ephemeris


class MeridianAgent(BaseAgent):
    """Meridian trend line analysis."""

    def __init__(self):
        super().__init__(
            name="MeridianAgent",
            system_prompt="Анализ меридианных линий тренда.",
        )

    @require_ephemeris
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        price = context.get("price", 100.0)
        dt = context.get("datetime")

        if dt is None:
            from datetime import datetime
            dt = datetime.now()

        date_str = dt.strftime("%Y-%m-%d")
        time_str = dt.strftime("%H:%M:%S")
        eph = swiss_ephemeris(date=date_str, time=time_str, lat=40.7128, lon=-74.0060, ayanamsa="lahiri")

        # Meridian levels (simplified)
        support = price * 0.97
        resistance = price * 1.03

        if price <= support:
            signal = Signal.BUY
            confidence = 55
            summary = "Meridian: поддержка на уровне"
        elif price >= resistance:
            signal = Signal.SELL
            confidence = 55
            summary = "Meridian: сопротивление"
        else:
            signal = Signal.NEUTRAL
            confidence = 50
            summary = "Meridian: в диапазоне"

        return AgentResponse(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=summary,
            metadata={"support": support, "resistance": resistance, **eph},
        )
