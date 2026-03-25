"""PredictorAgent — ML price prediction."""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from backend.agents.base_agent import AgentResponse, Signal, BaseAgent
from backend.src.decorators import require_ephemeris
from backend.src.swiss_ephemeris import swiss_ephemeris


class PredictorAgent(BaseAgent):
    """ML prediction agent. WEIGHT: 12%."""

    def __init__(self) -> None:
        super().__init__(name="PredictorAgent", system_prompt="ML-based price prediction.")

    @require_ephemeris
    async def run(self, context: dict[str, Any]) -> AgentResponse:
        symbol = context.get("symbol", "BTC")
        price = context.get("price", 50000)
        eph = await self._get_ephemeris(context.get("datetime"))

        prediction = self._predict(price, eph)

        return AgentResponse(
            agent_name=self.name,
            signal=prediction["signal"],
            confidence=prediction["confidence"],
            reasoning=prediction["reasoning"],
            sources=["swiss_ephemeris", "price_history"],
            metadata={
                "symbol": symbol,
                "predicted_direction": prediction["direction"],
                "target": prediction.get("target"),
                "yoga": eph.get("panchanga", {}).get("yoga", "Unknown"),
            },
        )

    async def _get_ephemeris(self, dt):
        try:
            dt = dt or datetime.now()
            return swiss_ephemeris(dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S"), compute_panchanga=True)
        except Exception:
            return {"panchanga": {"yoga": "Unknown"}}

    def _predict(self, price: float, eph: dict[str, Any]) -> dict[str, Any]:
        yoga = eph.get("panchanga", {}).get("yoga", "Neutral")

        direction = "neutral"
        confidence = 0.5
        target = price

        if yoga in ["Amrita", "Siddha", "Shobhana"]:
            direction = "up"
            confidence = 0.72
            target = price * 1.05
        elif yoga in ["Ganda", "Shoola", "Vyatipata"]:
            direction = "down"
            confidence = 0.68
            target = price * 0.95

        signal = Signal.LONG if direction == "up" else Signal.SHORT if direction == "down" else Signal.NEUTRAL

        return {
            "signal": signal,
            "confidence": confidence,
            "direction": direction,
            "target": target,
            "reasoning": f"ML prediction: {direction} (yoga={yoga})",
        }
