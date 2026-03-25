"""
MerrimanAgent — 14-year cycle timing (Merriman).
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Any
from backend.agents.base_agent import BaseAgent, AgentResponse, Signal
from backend.src.decorators import require_ephemeris
from backend.src.swiss_ephemeris import swiss_ephemeris


class MerrimanAgent(BaseAgent):
    """Merriman seasonal timing (14-year cycle)."""

    def __init__(self):
        super().__init__(
            name="MerrimanAgent",
            system_prompt="Анализ по Merriman: 14-летний цикл, оптимальные месяцы для покупок/продаж.",
        )

    @require_ephemeris
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        dt = context.get("datetime") or datetime.now()

        date_str = dt.strftime("%Y-%m-%d")
        time_str = dt.strftime("%H:%M:%S")
        eph = swiss_ephemeris(date=date_str, time=time_str, lat=40.7128, lon=-74.0060, ayanamsa="lahiri")

        # Merriman months (Oct-Nov strongest, Apr-May weakest historically)
        month = dt.month

        # Best months: October, November
        # Worst months: April, May
        if month in (10, 11):
            signal = Signal.BUY
            confidence = 60
            summary = "Merriman: лучший месяц для покупок"
        elif month in (4, 5):
            signal = Signal.SELL
            confidence = 60
            summary = "Merriman: слабый месяц"
        else:
            signal = Signal.NEUTRAL
            confidence = 50
            summary = f"Merriman: нейтральный месяц ({month})"

        return AgentResponse(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=summary,
            metadata={"month": month, **eph},
        )
