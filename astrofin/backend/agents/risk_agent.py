"""
RiskAgent — оценка уровня риска позиции.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Any

from .base_agent import BaseAgent, AgentResponse
from backend.src.decorators import require_ephemeris
from backend.src.swiss_ephemeris import swiss_ephemeris


class RiskAgent(BaseAgent):
    """
    RiskAgent — оценивает общий уровень риска позиции.
    Учитывает:
    - Астрологические факторы (Inauspicious Yoga, ретроградность, аштакаварга)
    - Рыночные факторы (VIX, ATR, волатильность)
    - Комбинированный риск (0-100)
    """

    def __init__(self):
        super().__init__(
            name="Risk",
            system_prompt=(
                "Ты — специалист по оценке рисков. "
                "Анализируй астрологические и рыночные факторы риска. "
                "Выдавай честную оценку опасности."
            )
        )

    @require_ephemeris
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        symbol = context.get("symbol", "BTC")
        dt = context.get("datetime") or datetime.now()
        price = context.get("price", 100.0)

        # 1. Критический вызов Swiss Ephemeris
        eph = await self._call_ephemeris(dt)

        # 2. Оценка астрологического риска
        astro_risk = self._calculate_astro_risk(eph)

        # 3. Оценка рыночного риска
        market_risk = self._calculate_market_risk(context)

        # 4. Итоговый риск (взвешенный)
        total_risk = int(0.65 * astro_risk + 0.35 * market_risk)

        # Определяем сигнал
        if total_risk >= 75:
            signal = "STRONG_SELL"
        elif total_risk >= 60:
            signal = "SELL"
        elif total_risk >= 45:
            signal = "NEUTRAL"
        else:
            signal = "HOLD"

        return AgentResponse(
            agent_name="Risk",
            signal=signal,
            confidence=min(95, total_risk),
            reasoning=f"Risk Assessment {symbol}: {signal} ({total_risk}%)",
            metadata={
                "total_risk_score": total_risk,
                "astro_risk": astro_risk,
                "market_risk": market_risk,
                "key_factors": self._get_key_risk_factors(eph),
                "recommendation": self._get_risk_recommendation(total_risk)
            }
        )

    async def _call_ephemeris(self, dt: datetime) -> Dict:
        """Критический вызов Swiss Ephemeris"""
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

    def _calculate_astro_risk(self, eph: Dict) -> int:
        """Астрологический риск (0-100)"""
        panchanga = eph.get("panchanga", {})
        yoga_cat = panchanga.get("yoga_category", "Neutral")
        positions = eph.get("positions", {})

        risk = 30  # базовый уровень

        # Inauspicious Yoga = сильный риск
        if yoga_cat == "Inauspicious":
            risk += 35
        elif yoga_cat == "Neutral":
            risk += 10

        # Ретроградные планеты
        retro_count = sum(1 for p in ["Mercury", "Mars", "Saturn"]
                         if positions.get(p, {}).get("retro", False))
        risk += retro_count * 12

        # Слабая аштакаварга
        ashtak = eph.get("ashtakavarga", {})
        if ashtak and "sarvashtakavarga" in ashtak:
            total_bindus = sum(ashtak["sarvashtakavarga"].values())
            if total_bindus < 320:
                risk += 18

        return min(100, risk)

    def _calculate_market_risk(self, context: Dict[str, Any]) -> int:
        """Рыночный риск"""
        vix = context.get("vix", 18.0)
        return min(100, int(vix * 2.8))

    def _get_key_risk_factors(self, eph: Dict) -> list:
        """Ключевые астрологические факторы риска"""
        factors = []
        panchanga = eph.get("panchanga", {})

        if panchanga.get("yoga_category") == "Inauspicious":
            factors.append(f"Inauspicious Yoga: {panchanga.get('yoga')}")
        if panchanga.get("karana") == "Vishti":
            factors.append("Vishti Karana (рискованный период)")

        positions = eph.get("positions", {})
        for planet in ["Mercury", "Mars", "Saturn"]:
            if positions.get(planet, {}).get("retro"):
                factors.append(f"{planet} retrograde")

        return factors or ["No major risk factors detected"]

    def _get_risk_recommendation(self, total_risk: int) -> str:
        if total_risk >= 80:
            return "Высокий риск. Рекомендуется сократить позицию или перейти в кэш."
        elif total_risk >= 60:
            return "Повышенный риск. Увеличьте стоп-лосс и будьте осторожны."
        elif total_risk >= 45:
            return "Средний риск. Можно держать позицию с осторожностью."
        else:
            return "Низкий риск. Можно рассматривать увеличение позиции."
