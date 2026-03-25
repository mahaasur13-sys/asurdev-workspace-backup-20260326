"""
MacroAgent — Macroeconomic analysis.
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from backend.agents.base_agent import AgentResponse, Signal, BaseAgent
from backend.src.decorators import require_ephemeris
from backend.src.swiss_ephemeris import swiss_ephemeris


class MacroAgent(BaseAgent):
    """Macroeconomic analysis agent. WEIGHT: 13%."""

    def __init__(self) -> None:
        super().__init__(name="MacroAgent", system_prompt="Analyze macroeconomic indicators.")

    @require_ephemeris
    async def run(self, context: dict[str, Any]) -> AgentResponse:
        """Run macro analysis."""
        symbol = context.get("symbol", "BTC")
        price = context.get("price", 50000)
        eph = await self._get_ephemeris(context.get("datetime"))

        data = await self._fetch_macro_data()
        signal, confidence, reasoning = self._analyze(data, price, eph)

        return AgentResponse(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            sources=["swiss_ephemeris", "macro_indicators"],
            metadata={
                "symbol": symbol,
                "vix": data.get("vix", 20),
                "dxy": data.get("dxy", 104),
                "fed_rate": data.get("fed_rate", 5.25),
                "yoga": eph.get("panchanga", {}).get("yoga", "Unknown"),
            },
        )

    async def _get_ephemeris(self, dt):
        try:
            dt = dt or datetime.now()
            return swiss_ephemeris(dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S"), compute_panchanga=True)
        except Exception:
            return {"panchanga": {"yoga": "Unknown"}}

    async def _fetch_macro_data(self) -> dict[str, Any]:
        await asyncio.sleep(0.01)
        return {"vix": 18.5, "dxy": 104.2, "fed_rate": 5.25, "us10y": 4.3}

    def _analyze(self, data, price, eph) -> tuple[Signal, float, str]:
        vix = data.get("vix", 20)
        dxy = data.get("dxy", 104)
        yoga = eph.get("panchanga", {}).get("yoga", "Neutral")

        score = 0.5
        if vix < 20:
            score += 0.15
        elif vix > 30:
            score -= 0.15

        if dxy > 105:
            score -= 0.1

        if yoga in ["Amrita", "Shubha"]:
            score = min(1.0, score + 0.05)

        if score > 0.6:
            return Signal.LONG, 0.6, f"Macro favorable (VIX={vix}, DXY={dxy}, yoga={yoga})"
        elif score < 0.4:
            return Signal.SHORT, 0.6, f"Macro unfavorable (VIX={vix}, DXY={dxy})"
        return Signal.NEUTRAL, 0.5, f"Macro neutral (VIX={vix}, DXY={dxy})"
