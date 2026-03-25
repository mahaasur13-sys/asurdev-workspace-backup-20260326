"""
AndrewsAgent — Andrews Pitchfork.
"""

from __future__ import annotations

from typing import Dict, Any
from backend.agents.base_agent import BaseAgent, AgentResponse, Signal
from backend.src.decorators import require_ephemeris
from backend.src.swiss_ephemeris import swiss_ephemeris


class AndrewsAgent(BaseAgent):
    """Andrews Pitchfork — median line analysis."""

    def __init__(self):
        super().__init__(
            name="AndrewsAgent",
            system_prompt="Анализ по Andrews Pitchfork: медианная линия, сигналы отскока.",
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

        # Pitchfork levels (simplified)
        median_line = price * 1.02
        upper_quarter = price * 1.05
        lower_quarter = price * 0.95

        if price < median_line:
            signal = Signal.BUY
            confidence = 55
            summary = f"Andrews: цена ниже медианы — ожидается отскок вверх"
        elif price > upper_quarter:
            signal = Signal.SELL
            confidence = 55
            summary = f"Andrews: цена у верхней границы"
        else:
            signal = Signal.NEUTRAL
            confidence = 50
            summary = f"Andrews: цена в канале"

        return AgentResponse(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=summary,
            metadata={"median_line": median_line, "upper": upper_quarter, "lower": lower_quarter, **eph},
        )
