"""
Technical Agent — классический технический анализ как фильтр.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Any

from .base_agent import BaseAgent, AgentResponse
from backend.src.decorators import require_ephemeris


class TechnicalAgent(BaseAgent):
    """
    TechnicalAgent — выполняет классический технический анализ как фильтр.
    Использует данные из Polygon.io + астрологические подтверждения.
    """

    def __init__(self):
        super().__init__(
            name="Technical",
            system_prompt="Ты — технический аналитик. Анализируй price action, индикаторы и объёмы."
        )

    @require_ephemeris
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        symbol = context.get("symbol", "BTC")
        dt = context.get("datetime") or datetime.now()

        eph = await self._call_ephemeris(dt)
        price_data = await self._fetch_price_data(symbol)
        tech_score = self._calculate_technical_score(price_data, eph)

        signal = "BUY" if tech_score >= 65 else "NEUTRAL" if tech_score >= 45 else "SELL"

        return AgentResponse(
            agent_name="Technical",
            signal=signal,
            confidence=int(tech_score),
            reasoning=f"Технический анализ {symbol}: {signal}",
            metadata={
                "rsi": price_data.get("rsi", 52),
                "macd_signal": price_data.get("macd_signal", "neutral"),
                "volume_trend": price_data.get("volume_trend", "normal"),
                "astro_influence": self._get_astro_influence(eph)
            }
        )

    async def _call_ephemeris(self, dt: datetime) -> Dict:
        from backend.src.swiss_ephemeris import swiss_ephemeris

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

    async def _fetch_price_data(self, symbol: str) -> Dict:
        """Заглушка. В продакшене — реальный вызов Polygon.io"""
        return {
            "rsi": 58,
            "macd_signal": "bullish",
            "volume_trend": "increasing",
            "support": 62000,
            "resistance": 68500
        }

    def _calculate_technical_score(self, data: Dict, eph: Dict) -> float:
        base = 50
        if data["macd_signal"] == "bullish":
            base += 20
        if data["volume_trend"] == "increasing":
            base += 15

        yoga_cat = eph.get("panchanga", {}).get("yoga_category")
        if yoga_cat == "Auspicious":
            base += 12
        elif yoga_cat == "Inauspicious":
            base -= 10

        return max(20, min(100, base))

    def _get_astro_influence(self, eph: Dict) -> str:
        return f"Yoga: {eph.get('panchanga', {}).get('yoga', 'Unknown')}"
