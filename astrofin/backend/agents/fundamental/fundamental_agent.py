"""
FundamentalAgent — Financial statement analysis.
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from backend.agents.base_agent import AgentResponse, Signal, BaseAgent
from backend.src.decorators import require_ephemeris
from backend.src.swiss_ephemeris import swiss_ephemeris


class FundamentalAgent(BaseAgent):
    """
    Fundamental analysis agent.

    Analyzes financial statements, on-chain data, and valuation metrics.
    WEIGHT: 18%
    """

    def __init__(self) -> None:
        super().__init__(
            name="FundamentalAgent",
            system_prompt="Analyze financial fundamentals and valuation.",
        )

    @require_ephemeris
    async def run(self, context: dict[str, Any]) -> AgentResponse:
        """Run fundamental analysis."""
        symbol = context.get("symbol", "BTC")
        price = context.get("price", context.get("current_price", 50000))

        # Get ephemeris for timing adjustment
        eph = await self._get_ephemeris(context.get("datetime"))

        # Fetch market data
        data = await self._fetch_data(symbol)

        # Analyze fundamentals
        signal, confidence, reasoning = self._analyze(data, price, eph)

        return AgentResponse(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            sources=["swiss_ephemeris", f"market_data_{symbol}"],
            metadata={
                "symbol": symbol,
                "price": price,
                "fundamental_score": data.get("score", 0.5),
                "yoga": eph.get("panchanga", {}).get("yoga", "Unknown"),
                "ephemeris_used": True,
            },
        )

    async def _get_ephemeris(self, dt: datetime | None) -> dict[str, Any]:
        """Get ephemeris data."""
        dt = dt or datetime.now()
        try:
            return swiss_ephemeris(
                date=dt.strftime("%Y-%m-%d"),
                time=dt.strftime("%H:%M:%S"),
                lat=40.7128,
                lon=-74.0060,
                compute_panchanga=True,
            )
        except Exception:
            return {"panchanga": {"yoga": "Unknown"}}

    async def _fetch_data(self, symbol: str) -> dict[str, Any]:
        """Fetch fundamental data."""
        # In production: fetch from CoinGecko, on-chain APIs, etc.
        await asyncio.sleep(0.01)  # Simulate API call
        return {
            "score": 0.55,
            "market_cap": 1200000000000,
            "volume_24h": 30000000000,
            "price_change_24h": 2.5,
        }

    def _analyze(
        self, data: dict[str, Any], price: float, eph: dict[str, Any]
    ) -> tuple[Signal, float, str]:
        """Analyze fundamental data."""
        score = data.get("score", 0.5)

        # Ephemeris timing adjustment
        yoga = eph.get("panchanga", {}).get("yoga", "Neutral")
        if yoga in ["Amrita", "Shobhana", "Siddha", "Shubha"]:
            score = min(1.0, score + 0.1)
        elif yoga in ["Atiganda", "Ganda", "Shoola", "Vyatipata"]:
            score = max(0.0, score - 0.1)

        if score > 0.6:
            signal = Signal.LONG
            confidence = 0.65
            reasoning = f"Fundamentals strong (score={score:.2f}, yoga={yoga})"
        elif score < 0.4:
            signal = Signal.SHORT
            confidence = 0.65
            reasoning = f"Fundamentals weak (score={score:.2f}, yoga={yoga})"
        else:
            signal = Signal.NEUTRAL
            confidence = 0.5
            reasoning = f"Fundamentals neutral (score={score:.2f})"

        return signal, confidence, reasoning
