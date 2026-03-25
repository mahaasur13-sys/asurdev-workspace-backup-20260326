"""
Gann Agent — Gann angles, price squares, time cycles.
"""

import asyncio
import numpy as np
from typing import Dict, Any

from backend.agents.base_agent import BaseAgent
from backend.agents.base_agent import AgentResponse, Signal
from backend.core.decorators import require_ephemeris


class GannAgent(BaseAgent):
    """
    Gann angles, ценовые квадраты, time cycles.
    Вес: 3%
    """

    def __init__(self):
        super().__init__(
            name="GannAgent",
            domain="gann",
            weight=0.03,
            instructions="Gann analysis agent",
        )

    @require_ephemeris
    async def run(self, state: Dict[str, Any]) -> AgentResponse:
        current_price = state.get("current_price", 50000)

        # Gann angles calculation
        angles = self._calculate_gann_angles(current_price)
        squares = self._price_squares(current_price)
        time_cycle = self._time_cycle()

        score = 50
        if angles["at_angle"]:
            score += 30
        if squares["at_square"]:
            score += 20

        score = min(100, score)

        if score >= 70:
            final_signal = Signal.STRONG_BUY
        elif score >= 55:
            final_signal = Signal.BUY
        else:
            final_signal = Signal.NEUTRAL

        reasoning = (
            f"Price at 1x1 Gann angle: {'Yes' if angles['at_angle'] else 'No'}. "
            f"Price square: {squares['current_square']}. "
            f"Time cycle: {time_cycle['position']}."
        )

        return AgentResponse(
            agent_name=self.name,
            signal=final_signal,
            confidence=score / 100,
            score=score,
            reasoning=reasoning,
            sources=["gann/angles.md", "gann/squares.md"],
            metadata={"angles": angles, "squares": squares, "time_cycle": time_cycle},
        )

    def _calculate_gann_angles(self, price: float) -> Dict:
        """Calculate if price is at Gann angle."""
        # 1x1 angle = 45 degrees = 1 unit price per 1 unit time
        sqrt_price = price ** 0.5
        next_square = (int(sqrt_price) + 1) ** 2
        return {
            "at_angle": abs(price - next_square) < price * 0.02,
            "sqrt_price": sqrt_price,
            "next_square": next_square,
        }

    def _price_squares(self, price: float) -> Dict:
        """Price square analysis."""
        sqrt_price = price ** 0.5
        current_square = int(sqrt_price) ** 2
        next_square = (int(sqrt_price) + 1) ** 2
        return {
            "at_square": abs(price - current_square) < price * 0.01,
            "current_square": current_square,
            "next_square": next_square,
            "progress": (price - current_square) / (next_square - current_square) if next_square > current_square else 0,
        }

    def _time_cycle(self) -> Dict:
        """Simple time cycle (360 degrees = 1 year)."""
        import datetime
        now = datetime.datetime.now()
        day_of_year = now.timetuple().tm_yday
        degree = (day_of_year / 365) * 360
        return {
            "degree": degree,
            "position": "first_half" if degree < 180 else "second_half",
        }
