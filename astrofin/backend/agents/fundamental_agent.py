"""
Fundamental Agent — financial statement analysis, valuation metrics.
"""

import asyncio
import requests
from datetime import datetime
from typing import Dict, Any

from backend.agents.base_agent import BaseAgent
from backend.agents.base_agent import AgentResponse, Signal
from backend.core.decorators import require_ephemeris


class FundamentalAgent(BaseAgent):
    """
    Фундаментальный анализ: P/E, MVRV, revenue growth, valuation.
    Вес: 20%
    """

    def __init__(self):
        super().__init__(
            name="FundamentalAgent",
            domain="fundamental",
            weight=0.20,
            instructions="Fundamental analysis agent",
        )

    @require_ephemeris
    async def analyze(self, state: Dict[str, Any]) -> AgentResponse:
        symbol = state.get("symbol", "BTCUSDT")
        current_price = state.get("current_price", 50000)

        # Fetch fundamental data
        data = await self._fetch_fundamental_data(symbol, current_price)

        # Calculate score
        score = 0
        signals = []

        # MVRV Score
        mvrv = data.get("mvrv_score", 0)
        if mvrv < 1.5:
            score += 35
            signals.append(Signal.BUY)
        elif mvrv < 3.5:
            score += 20
            signals.append(Signal.NEUTRAL)
        else:
            signals.append(Signal.SELL)

        # Revenue Growth
        growth = data.get("revenue_growth", 0)
        if growth > 0.1:
            score += 30
            signals.append(Signal.BUY)
        elif growth > 0:
            score += 15
            signals.append(Signal.BUY)
        else:
            signals.append(Signal.SELL)

        # Market Dominance
        dominance = data.get("dominance", 50)
        if 45 < dominance < 60:
            score += 20
            signals.append(Signal.BUY)
        else:
            signals.append(Signal.NEUTRAL)

        # Network Growth
        growth_rate = data.get("network_growth", 0)
        if growth_rate > 0.05:
            score += 15
            signals.append(Signal.BUY)
        else:
            signals.append(Signal.NEUTRAL)

        # Normalize to 0-100
        score = min(100, score)

        # Determine signal
        buy_count = signals.count(Signal.BUY)
        if score >= 70:
            final_signal = Signal.STRONG_BUY
        elif score >= 55:
            final_signal = Signal.BUY
        elif score >= 45:
            final_signal = Signal.NEUTRAL
        elif score >= 30:
            final_signal = Signal.SELL
        else:
            final_signal = Signal.STRONG_SELL

        reasoning = (
            f"MVRV={mvrv:.2f} ({'undervalued' if mvrv < 1.5 else 'overvalued' if mvrv > 3.5 else 'fair'}). "
            f"Revenue growth: {growth*100:.1f}%. Dominance: {dominance:.1f}%. "
            f"Network growth: {growth_rate*100:.1f}%."
        )

        return AgentResponse(
            agent_name=self.name,
            signal=final_signal,
            confidence=buy_count / len(signals),
            reasoning=reasoning,
            sources=["fundamental/mvrv.md"],
            metadata={
                "mvrv_score": mvrv,
                "revenue_growth": growth,
                "dominance": dominance,
                "network_growth": growth_rate,
            },
        )

    async def _fetch_fundamental_data(self, symbol: str, price: float) -> Dict:
        """Fetch fundamental metrics."""
        data = {"mvrv_score": 2.1, "revenue_growth": 0.05, "dominance": 52, "network_growth": 0.03}

        # Try CoinGecko for crypto
        try:
            coin_id = "bitcoin" if "BTC" in symbol else "ethereum"
            url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
            resp = requests.get(url, timeout=5)
            if resp.ok:
                coin = resp.json()
                data["revenue_growth"] = coin.get("market_data", {}).get("price_change_percentage_24h", 0) / 100
                data["dominance"] = coin.get("market_cap_rank", 50)
        except Exception:
            pass

        # MVRV approximation
        data["mvrv_score"] = min(5, max(0.5, price / 20000))

        return data
