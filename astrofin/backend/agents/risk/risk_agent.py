"""RiskAgent — Risk assessment and position sizing."""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from backend.agents.base_agent import AgentResponse, Signal, BaseAgent
from backend.src.decorators import require_ephemeris
from backend.src.swiss_ephemeris import swiss_ephemeris


class RiskAgent(BaseAgent):
    """Risk assessment agent. WEIGHT: 5%."""

    def __init__(self) -> None:
        super().__init__(name="RiskAgent", system_prompt="Risk assessment and position sizing.")

    @require_ephemeris
    async def run(self, context: dict[str, Any]) -> AgentResponse:
        symbol = context.get("symbol", "BTC")
        price = context.get("price", 50000)
        eph = await self._get_ephemeris(context.get("datetime"))

        risk = self._assess_risk(price, eph)

        return AgentResponse(
            agent_name=self.name,
            signal=risk["signal"],
            confidence=risk["confidence"],
            reasoning=risk["reasoning"],
            sources=["swiss_ephemeris"],
            metadata={
                "symbol": symbol,
                "position_size": risk.get("position_size", 0.05),
                "stop_loss": risk.get("stop_loss", price * 0.97),
                "yoga": eph.get("panchanga", {}).get("yoga", "Unknown"),
            },
        )

    async def _get_ephemeris(self, dt):
        try:
            dt = dt or datetime.now()
            return swiss_ephemeris(dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S"), compute_panchanga=True)
        except Exception:
            return {"panchanga": {"yoga": "Unknown"}}

    def _assess_risk(self, price: float, eph: dict[str, Any]) -> dict[str, Any]:
        yoga = eph.get("panchanga", {}).get("yoga", "Neutral")

        risk_score = 0.5
        if yoga in ["Ganda", "Shoola", "Vyatipata"]:
            risk_score += 0.2
        elif yoga in ["Amrita", "Shobhana"]:
            risk_score -= 0.1

        position_size = 0.05 if risk_score < 0.6 else 0.03
        stop_loss = price * (0.97 if risk_score < 0.6 else 0.95)

        if risk_score > 0.7:
            return {
                "signal": Signal.AVOID,
                "confidence": 0.7,
                "reasoning": f"High risk (score={risk_score:.2f}, yoga={yoga})",
                "position_size": position_size * 0.5,
                "stop_loss": price * 0.95,
            }
        return {
            "signal": Signal.NEUTRAL,
            "confidence": 0.6,
            "reasoning": f"Risk acceptable (score={risk_score:.2f})",
            "position_size": position_size,
            "stop_loss": stop_loss,
        }
