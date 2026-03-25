"""
Meridian Agent — Meridian trend lines + astro confirmation.
"""

import asyncio
from typing import Dict, Any, List

from backend.agents.base_agent import BaseAgent
from backend.agents.base_agent import AgentResponse, Signal
from backend.core.decorators import require_ephemeris


class MeridianAgent(BaseAgent):
    """
    Meridian trend lines + astro confirmation.
    Вес: 3%
    """

    def __init__(self):
        super().__init__(
            name="MeridianAgent",
            domain="meridian",
            weight=0.03,
            instructions="Meridian trend line analysis agent",
        )

    @require_ephemeris
    async def run(self, state: Dict[str, Any]) -> AgentResponse:
        symbol = state.get("symbol", "BTCUSDT")
        current_price = state.get("current_price", 50000)

        data = await self._fetch_data(symbol)
        lines = self._calculate_meridian_lines(data, current_price)

        score = 50
        if lines["at_support"]:
            score += 30
        if lines["at_resistance"]:
            score -= 20
        if lines["trend"] == "bullish":
            score += 20

        score = max(0, min(100, score))

        if score >= 70:
            final_signal = Signal.STRONG_BUY
        elif score >= 55:
            final_signal = Signal.BUY
        elif score >= 45:
            final_signal = Signal.NEUTRAL
        else:
            final_signal = Signal.SELL

        reasoning = (
            f"Trend: {lines['trend']}. "
            f"Support: {'Yes' if lines['at_support'] else 'No'}. "
            f"Resistance: {'Yes' if lines['at_resistance'] else 'No'}. "
            f"Support: ${lines['support']:.0f}, Resistance: ${lines['resistance']:.0f}."
        )

        return AgentResponse(
            agent_name=self.name,
            signal=final_signal,
            confidence=score / 100,
            score=score,
            reasoning=reasoning,
            sources=["meridian/lines.md"],
            metadata={"lines": lines},
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

    def _calculate_meridian_lines(self, data: List[float], current_price: float) -> Dict:
        """Calculate support/resistance using meridian lines."""
        if len(data) < 30:
            return {"trend": "unknown", "at_support": False, "at_resistance": False, "support": 0, "resistance": 0}

        recent = data[-30:]
        highs = sorted(recent, reverse=True)[:5]
        lows = sorted(recent)[:5]

        resistance = sum(highs) / len(highs)
        support = sum(lows) / len(lows)

        at_support = abs(current_price - support) / support < 0.03
        at_resistance = abs(current_price - resistance) / resistance < 0.03

        trend = "bullish" if current_price > support + (resistance - support) * 0.5 else "bearish"

        return {
            "trend": trend,
            "at_support": at_support,
            "at_resistance": at_resistance,
            "support": support,
            "resistance": resistance,
        }
