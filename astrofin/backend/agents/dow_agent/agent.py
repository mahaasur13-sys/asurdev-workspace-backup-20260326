"""
Dow Agent — Dow Theory confirmation.
"""

import asyncio
from typing import Dict, Any, List

from backend.agents.base_agent import BaseAgent
from backend.agents.base_agent import AgentResponse, Signal
from backend.core.decorators import require_ephemeris


class DowAgent(BaseAgent):
    """
    Dow Theory confirmation.
    Вес: 3%
    """

    def __init__(self):
        super().__init__(
            name="DowAgent",
            domain="dow",
            weight=0.03,
            instructions="Dow Theory analysis agent",
        )

    @require_ephemeris
    async def run(self, state: Dict[str, Any]) -> AgentResponse:
        btc_data = await self._fetch_data("BTCUSDT")
        eth_data = await self._fetch_data("ETHUSDT")

        confirmation = self._check_confirmation(btc_data, eth_data)

        score = 50
        if confirmation["confirmed"]:
            score += 40
        if confirmation["strong"]:
            score += 10

        score = min(100, score)

        if score >= 70:
            final_signal = Signal.STRONG_BUY
        elif score >= 55:
            final_signal = Signal.BUY
        else:
            final_signal = Signal.NEUTRAL

        reasoning = (
            f"Dow confirmation: {'Yes' if confirmation['confirmed'] else 'No'}. "
            f"Strong confirm: {'Yes' if confirmation['strong'] else 'No'}. "
            f"Average trend: {confirmation['avg_trend']}."
        )

        return AgentResponse(
            agent_name=self.name,
            signal=final_signal,
            confidence=score / 100,
            score=score,
            reasoning=reasoning,
            sources=["dow/theory.md"],
            metadata={"confirmation": confirmation},
        )

    async def _fetch_data(self, symbol: str) -> List[float]:
        try:
            import requests
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&limit=30"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            return [float(x[4]) for x in data]
        except Exception:
            return []

    def _check_confirmation(self, btc: List[float], eth: List[float]) -> Dict:
        """Check if BTC and ETH confirm each other."""
        if len(btc) < 20 or len(eth) < 20:
            return {"confirmed": False, "strong": False, "avg_trend": "unknown"}

        btc_trend = btc[-1] > btc[-10]
        eth_trend = eth[-1] > eth[-10]

        btc_strength = (btc[-1] - btc[-10]) / btc[-10]
        eth_strength = (eth[-1] - eth[-10]) / eth[-10]

        confirmed = btc_trend == eth_trend
        strong = abs(btc_strength - eth_strength) < 0.02

        avg_trend = "bullish" if btc_trend else "bearish"

        return {
            "confirmed": confirmed,
            "strong": strong,
            "avg_trend": avg_trend,
            "btc_strength": btc_strength,
            "eth_strength": eth_strength,
        }
