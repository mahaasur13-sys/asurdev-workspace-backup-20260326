"""BearResearcherAgent — Bearish case research."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from backend.agents.base_agent import AgentResponse, Signal, BaseAgent
from backend.src.decorators import require_ephemeris
from backend.src.swiss_ephemeris import swiss_ephemeris


class BearResearcherAgent(BaseAgent):
    """Bear researcher agent. WEIGHT: 5%."""

    def __init__(self) -> None:
        super().__init__(name="BearResearcherAgent", system_prompt="Research bearish case and risk thesis.")

    @require_ephemeris
    async def run(self, context: dict[str, Any]) -> AgentResponse:
        symbol = context.get("symbol", "BTC")
        price = context.get("price", 50000)
        eph = await self._get_ephemeris(context.get("datetime"))

        thesis = self._research_bearish(price, eph)

        return AgentResponse(
            agent_name=self.name,
            signal=thesis["signal"],
            confidence=thesis["confidence"],
            reasoning=thesis["reasoning"],
            sources=["swiss_ephemeris"],
            metadata={
                "symbol": symbol,
                "yoga": eph.get("panchanga", {}).get("yoga", "Unknown"),
            },
        )

    async def _get_ephemeris(self, dt):
        try:
            dt = dt or datetime.now()
            return swiss_ephemeris(dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S"), compute_panchanga=True)
        except Exception:
            return {"panchanga": {"yoga": "Unknown"}}

    def _research_bearish(self, price: float, eph: dict[str, Any]) -> dict[str, Any]:
        yoga = eph.get("panchanga", {}).get("yoga", "Neutral")

        if yoga in ["Ganda", "Shoola", "Vyatipata", "Atiganda"]:
            return {
                "signal": Signal.SHORT,
                "confidence": 0.65,
                "reasoning": f"Bearish thesis supported (yoga={yoga})",
            }
        return {
            "signal": Signal.NEUTRAL,
            "confidence": 0.45,
            "reasoning": f"Bearish thesis neutral (yoga={yoga})",
        }
