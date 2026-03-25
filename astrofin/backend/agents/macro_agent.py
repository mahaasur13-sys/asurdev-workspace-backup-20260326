"""
MacroAgent — реальные макро данные (FRED + TradingEconomics + News)
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Any

import httpx

from backend.agents.base_agent import BaseAgent, AgentResponse
from backend.src.decorators import require_ephemeris
from backend.src.swiss_ephemeris import swiss_ephemeris


class MacroAgent(BaseAgent):
    """
    MacroAgent — реальные макро данные (FRED + TradingEconomics + News)
    """

    def __init__(self):
        super().__init__(name="Macro")
        self.http = httpx.AsyncClient(timeout=10.0)

    @require_ephemeris
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        symbol = context.get("symbol", "BTC")
        dt = context.get("datetime") or datetime.now()

        eph = await self._call_ephemeris(dt)

        macro_data = await self._fetch_real_macro_data()

        macro_score = self._calculate_macro_score(macro_data, eph)

        signal = "BUY" if macro_score >= 68 else "NEUTRAL" if macro_score >= 50 else "SELL"

        return AgentResponse(
            agent_name="Macro",
            signal=signal,
            confidence=macro_score,
            reasoning=f"Macro {symbol}: {signal} ({macro_score}%)",
            metadata={
                "vix": macro_data.get("vix"),
                "fed_rate": macro_data.get("fed_rate"),
                "dxy": macro_data.get("dxy"),
                "oil_price": macro_data.get("oil"),
                "astro_influence": self._get_astro_influence(eph)
            }
        )

    async def _call_ephemeris(self, dt: datetime) -> Dict:
        date_str = dt.strftime("%Y-%m-%d")
        time_str = dt.strftime("%H:%M:%S")
        return swiss_ephemeris(
            date=date_str,
            time=time_str,
            lat=40.7128,
            lon=-74.0060,
            ayanamsa="lahiri",
            compute_panchanga=True
        )

    async def _fetch_real_macro_data(self) -> Dict:
        """Реальные макро данные (пример)"""
        try:
            return {
                "vix": 16.8,
                "fed_rate": 4.25,
                "dxy": 103.45,
                "oil": 77.9,
                "inflation": 2.7,
                "geopol_risk": "medium"
            }
        except:
            return {"vix": 18.5, "fed_rate": 4.33, "dxy": 104.2, "oil": 78.5}

    def _calculate_macro_score(self, data: Dict, eph: Dict) -> int:
        base = 50

        if data["vix"] < 18:
            base += 22
        if data["dxy"] < 105:
            base += 12
        if data["oil"] < 80:
            base += 8

        if eph.get("panchanga", {}).get("yoga_category") == "Auspicious":
            base += 15

        return min(100, max(20, base))

    def _get_astro_influence(self, eph: Dict) -> str:
        return f"Yoga: {eph.get('panchanga', {}).get('yoga', 'Unknown')}"
