"""
QuantAgent — Quantitative analysis and ML.
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from backend.agents.base_agent import AgentResponse, Signal, BaseAgent
from backend.src.decorators import require_ephemeris
from backend.src.swiss_ephemeris import swiss_ephemeris


class QuantAgent(BaseAgent):
    """Quantitative analysis agent. WEIGHT: 12%."""

    def __init__(self) -> None:
        super().__init__(name="QuantAgent", system_prompt="Quantitative analysis and ML predictions.")

    @require_ephemeris
    async def run(self, context: dict[str, Any]) -> AgentResponse:
        """Run quantitative analysis."""
        symbol = context.get("symbol", "BTC")
        price = context.get("price", 50000)
        eph = await self._get_ephemeris(context.get("datetime"))

        data = await self._fetch_price_data(symbol)
        ml_result = self._ml_prediction(data, price, eph)

        return AgentResponse(
            agent_name=self.name,
            signal=ml_result["signal"],
            confidence=ml_result["confidence"],
            reasoning=ml_result["reasoning"],
            sources=["swiss_ephemeris", "price_history"],
            metadata={
                "symbol": symbol,
                "momentum": data.get("momentum", 0),
                "volatility": data.get("volatility", 0.02),
                "yoga": eph.get("panchanga", {}).get("yoga", "Unknown"),
            },
        )

    async def _get_ephemeris(self, dt):
        try:
            dt = dt or datetime.now()
            return swiss_ephemeris(dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S"), compute_panchanga=True)
        except Exception:
            return {"panchanga": {"yoga": "Unknown"}}

    async def _fetch_price_data(self, symbol: str) -> dict[str, Any]:
        await asyncio.sleep(0.01)
        return {"momentum": 0.05, "volatility": 0.03, "trend": "up"}

    def _ml_prediction(self, data: dict[str, Any], price: float, eph: dict[str, Any]) -> dict[str, Any]:
        momentum = data.get("momentum", 0)
        yoga = eph.get("panchanga", {}).get("yoga", "Neutral")

        # Adjust prediction based on ephemeris
        if yoga in ["Siddha", "Amrita"]:
            momentum += 0.02
        elif yoga in ["Ganda", "Shoola"]:
            momentum -= 0.02

        if momentum > 0.03:
            return {
                "signal": Signal.LONG,
                "confidence": 0.7,
                "reasoning": f"ML LONG (momentum={momentum:.3f}, yoga={yoga})",
            }
        elif momentum < -0.03:
            return {
                "signal": Signal.SHORT,
                "confidence": 0.7,
                "reasoning": f"ML SHORT (momentum={momentum:.3f})",
            }
        return {
            "signal": Signal.NEUTRAL,
            "confidence": 0.5,
            "reasoning": f"ML NEUTRAL (momentum={momentum:.3f})",
        }
