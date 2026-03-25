"""
Andrews Agent — Andrews Pitchfork analysis.
"""

import asyncio
import numpy as np
from typing import Dict, Any, List

from backend.agents.base_agent import BaseAgent
from backend.agents.base_agent import AgentResponse, Signal
from backend.core.decorators import require_ephemeris


class AndrewsAgent(BaseAgent):
    """
    Andrews Pitchfork analysis.
    Вес: 3%
    """

    def __init__(self):
        super().__init__(
            name="AndrewsAgent",
            domain="andrews",
            weight=0.03,
            instructions="Andrews Pitchfork analysis agent",
        )

    @require_ephemeris
    async def run(self, state: Dict[str, Any]) -> AgentResponse:
        symbol = state.get("symbol", "BTCUSDT")
        current_price = state.get("current_price", 50000)

        data = await self._fetch_data(symbol)
        pitchfork = self._calculate_pitchfork(data, current_price)

        score = 50
        if pitchfork["at_median"]:
            score += 25
        if pitchfork["trend"] == "bullish":
            score += 25

        score = min(100, score)

        if score >= 70:
            final_signal = Signal.STRONG_BUY
        elif score >= 55:
            final_signal = Signal.BUY
        else:
            final_signal = Signal.NEUTRAL

        reasoning = (
            f"Price at median line: {'Yes' if pitchfork['at_median'] else 'No'}. "
            f"Trend: {pitchfork['trend']}. "
            f"Upper: ${pitchfork['upper']:.0f}, Lower: ${pitchfork['lower']:.0f}."
        )

        return AgentResponse(
            agent_name=self.name,
            signal=final_signal,
            confidence=score / 100,
            score=score,
            reasoning=reasoning,
            sources=["andrews/pitchfork.md"],
            metadata={"pitchfork": pitchfork},
        )

    async def _fetch_data(self, symbol: str) -> List[float]:
        try:
            import requests
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&limit=60"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            return [float(x[4]) for x in data]
        except Exception:
            return []

    def _calculate_pitchfork(self, data: List[float], current_price: float) -> Dict:
        """Simplified Andrews Pitchfork calculation."""
        if len(data) < 30:
            return {"at_median": False, "trend": "unknown", "upper": 0, "lower": 0, "median": 0}

        recent = data[-30:]
        high = max(recent)
        low = min(recent)
        median = (high + low) / 2
        current = recent[-1]

        return {
            "at_median": abs(current - median) / median < 0.02,
            "trend": "bullish" if current > median else "bearish",
            "upper": high,
            "lower": low,
            "median": median,
        }
