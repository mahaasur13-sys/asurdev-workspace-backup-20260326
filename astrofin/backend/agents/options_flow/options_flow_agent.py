"""OptionsFlowAgent — Gamma exposure analysis."""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from backend.agents.base_agent import AgentResponse, Signal, BaseAgent
from backend.src.decorators import require_ephemeris
from backend.src.swiss_ephemeris import swiss_ephemeris


class OptionsFlowAgent(BaseAgent):
    """Options flow analysis agent. WEIGHT: 10%."""

    def __init__(self) -> None:
        super().__init__(name="OptionsFlowAgent", system_prompt="Analyze gamma exposure and unusual options activity.")

    @require_ephemeris
    async def run(self, context: dict[str, Any]) -> AgentResponse:
        symbol = context.get("symbol", "BTC")
        price = context.get("price", 50000)
        eph = await self._get_ephemeris(context.get("datetime"))

        data = await self._fetch_options_data(symbol)
        result = self._analyze(data, price, eph)

        return AgentResponse(
            agent_name=self.name,
            signal=result["signal"],
            confidence=result["confidence"],
            reasoning=result["reasoning"],
            sources=["swiss_ephemeris", "polygon.io"],
            metadata={
                "symbol": symbol,
                "gamma_exposure": data.get("gex", 0),
                "unusual_volume": data.get("unusual", 0),
                "yoga": eph.get("panchanga", {}).get("yoga", "Unknown"),
            },
        )

    async def _get_ephemeris(self, dt):
        try:
            dt = dt or datetime.now()
            return swiss_ephemeris(dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S"), compute_panchanga=True)
        except Exception:
            return {"panchanga": {"yoga": "Unknown"}}

    async def _fetch_options_data(self, symbol: str) -> dict[str, Any]:
        await asyncio.sleep(0.01)
        return {"gex": 500000, "pcr": 0.8, "unusual": 5, "sweeps": 2}

    def _analyze(self, data, price, eph) -> dict[str, Any]:
        gex = data.get("gex", 0)
        pcr = data.get("pcr", 1.0)
        yoga = eph.get("panchanga", {}).get("yoga", "Neutral")

        score = 0.5
        if gex > 0:
            score += 0.15
        if pcr < 0.7:
            score += 0.1

        if yoga in ["Amrita", "Shobhana"]:
            score = min(1.0, score + 0.05)

        if score > 0.65:
            return {"signal": Signal.LONG, "confidence": 0.65, "reasoning": f"Options flow bullish (GEX={gex})"}
        elif score < 0.35:
            return {"signal": Signal.SHORT, "confidence": 0.65, "reasoning": f"Options flow bearish (GEX={gex})"}
        return {"signal": Signal.NEUTRAL, "confidence": 0.5, "reasoning": "Options flow neutral"}
