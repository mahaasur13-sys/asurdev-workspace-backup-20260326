"""
Merriman Agent — Merriman 14-year cycle, seasonal timing.
"""

import asyncio
from datetime import datetime
from typing import Dict, Any

from backend.agents.base_agent import BaseAgent
from backend.agents.base_agent import AgentResponse, Signal
from backend.core.decorators import require_ephemeris


class MerrimanAgent(BaseAgent):
    """
    Merriman 14-year cycle, seasonal timing.
    Вес: 3%
    """

    def __init__(self):
        super().__init__(
            name="MerrimanAgent",
            domain="merriman",
            weight=0.03,
            instructions="Merriman cycle analysis agent",
        )

    @require_ephemeris
    async def run(self, state: Dict[str, Any]) -> AgentResponse:
        now = datetime.now()
        cycle = self._calculate_merriman_cycle(now)

        score = 50
        if cycle["in_buy_zone"]:
            score += 40
        if cycle["seasonality"] == "bullish":
            score += 10

        score = min(100, score)

        if score >= 70:
            final_signal = Signal.STRONG_BUY
        elif score >= 55:
            final_signal = Signal.BUY
        else:
            final_signal = Signal.NEUTRAL

        reasoning = (
            f"Merriman cycle: Year {cycle['year_in_cycle']}/14. "
            f"Buy zone: {'Yes' if cycle['in_buy_zone'] else 'No'}. "
            f"Seasonality: {cycle['seasonality']}."
        )

        return AgentResponse(
            agent_name=self.name,
            signal=final_signal,
            confidence=score / 100,
            score=score,
            reasoning=reasoning,
            sources=["merriman/cycles.md"],
            metadata={"cycle": cycle},
        )

    def _calculate_merriman_cycle(self, dt: datetime) -> Dict:
        """Calculate Merriman 14-year cycle position."""
        # 14-year cycle: years 1-4 (spring), 5-8 (summer), 9-11 (autumn), 12-14 (winter)
        year = dt.year
        cycle_year = (year - 2000) % 14 + 1

        buy_zones = [1, 2, 3, 4, 5, 12, 13, 14]
        in_buy_zone = cycle_year in buy_zones

        if cycle_year <= 4:
            seasonality = "bullish"
        elif cycle_year <= 8:
            seasonality = "mixed"
        elif cycle_year <= 11:
            seasonality = "bearish"
        else:
            seasonality = "bullish"

        return {
            "year_in_cycle": cycle_year,
            "in_buy_zone": in_buy_zone,
            "seasonality": seasonality,
            "cycle_name": "spring" if cycle_year <= 4 else "summer" if cycle_year <= 8 else "autumn" if cycle_year <= 11 else "winter",
        }
