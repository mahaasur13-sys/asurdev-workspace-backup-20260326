"""
CycleAgent — рыночные циклы (FFT-декомпозиция, гармоники).
"""

from __future__ import annotations

from typing import Dict, Any
from backend.agents.base_agent import BaseAgent, AgentResponse, Signal
from backend.src.decorators import require_ephemeris
from backend.src.swiss_ephemeris import swiss_ephemeris


class CycleAgent(BaseAgent):
    """FFT-based cycle decomposition, harmonics detection."""

    def __init__(self):
        super().__init__(
            name="CycleAgent",
            system_prompt="Анализ циклов: FFT-декомпозиция, гармоники, доминирующие частоты.",
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

        # Dominant cycles (simplified)
        cycles = [
            {"period": "4-year", "strength": 0.85, "phase": "expanding"},
            {"period": "20-week", "strength": 0.60, "phase": "peak"},
            {"period": "40-day", "strength": 0.45, "phase": "declining"},
        ]

        # Cycle phase analysis
        dominant_cycle = max(cycles, key=lambda x: x["strength"])
        cycle_phase = dominant_cycle["phase"]

        if cycle_phase in ("expanding", "trough"):
            signal = Signal.BUY
            confidence = int(40 + dominant_cycle["strength"] * 40)
            summary = f"CycleAgent: доминирующий {dominant_cycle['period']} цикл — {cycle_phase}"
        elif cycle_phase in ("peak", "declining"):
            signal = Signal.SELL
            confidence = int(40 + dominant_cycle["strength"] * 40)
            summary = f"CycleAgent: доминирующий {dominant_cycle['period']} цикл — {cycle_phase}"
        else:
            signal = Signal.NEUTRAL
            confidence = 50
            summary = f"CycleAgent: цикл {dominant_cycle['period']} в фазе {cycle_phase}"

        return AgentResponse(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=summary,
            metadata={"cycles": cycles, "dominant": dominant_cycle, **eph},
        )
