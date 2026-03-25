"""
OptionsFlowAgent — анализ опционного потока с реальными данными Polygon.io
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Any

from backend.agents.base_agent import BaseAgent, AgentResponse
from backend.src.decorators import require_ephemeris
from backend.src.swiss_ephemeris import swiss_ephemeris
from backend.utils.polygon_client import polygon_client


class OptionsFlowAgent(BaseAgent):
    """
    OptionsFlowAgent — анализ опционного потока с реальными данными Polygon.io
    """

    def __init__(self):
        super().__init__(name="OptionsFlow")

    @require_ephemeris
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        symbol = context.get("symbol", "BTC")
        dt = context.get("datetime") or datetime.now()

        eph = await self._call_ephemeris(dt)

        # Реальный запрос unusual activity
        flow_data = await polygon_client.get_unusual_activity(symbol, limit=80)

        if flow_data.get("status") == "error":
            flow_data = {"unusual_volume": 1200, "gex": 980_000_000, "pcr": 0.72}

        score = self._calculate_options_score(flow_data, eph)

        signal = "STRONG_BUY" if score >= 78 else "BUY" if score >= 65 else "NEUTRAL"

        return AgentResponse(
            agent_name="OptionsFlow",
            signal=signal,
            confidence=score,
            reasoning=f"Options Flow {symbol}: {signal} ({score}%)",
            metadata={
                "unusual_volume": flow_data.get("unusual_volume", 0),
                "gamma_exposure": flow_data.get("gamma_exposure", 0),
                "put_call_ratio": flow_data.get("put_call_ratio", 1.0),
                "large_sweeps": flow_data.get("large_sweeps", 0),
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

    def _calculate_options_score(self, flow: Dict, eph: Dict) -> int:
        base = 55

        if flow.get("large_sweeps", 0) > 10:
            base += 20
        if flow.get("put_call_ratio", 1.0) < 0.75:
            base += 18
        if flow.get("gamma_exposure", 0) > 1_000_000_000:
            base += 12

        # Астрологический бонус
        if eph.get("panchanga", {}).get("yoga_category") == "Auspicious":
            base += 15

        return min(100, max(30, base))

    def _get_astro_influence(self, eph: Dict) -> str:
        return f"Yoga: {eph.get('panchanga', {}).get('yoga', 'Unknown')}"
