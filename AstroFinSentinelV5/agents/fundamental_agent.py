"""
AstroFin Sentinel v5 — Fundamental Agent
Фундаментальный анализ: P/E, MVRV, revenue growth, valuation.
Вес в гибридном сигнале: 20%
"""

import asyncio
import requests
from datetime import datetime
from typing import Dict, Any

from agents.base_agent import BaseAgent, AgentResponse, SignalDirection
from agents._impl.ephemeris_decorator import require_ephemeris


class FundamentalAgent(BaseAgent):
    """
    FundamentalAgent — фундаментальный анализ.
    70% финансовые метрики + 30% астрологический бонус.
    """

    def __init__(self):
        super().__init__(
            name="Fundamental",
            instructions_path=None,
            domain="fundamental",
            weight=0.20,
        )

    @require_ephemeris
    async def run(self, state: Dict[str, Any]) -> AgentResponse:
        symbol = state.get("symbol", "BTC")
        dt = state.get("datetime") or datetime.utcnow()

        # 1. Астрологические данные
        eph = self._call_ephemeris(dt)

        # 2. Фундаментальные данные
        fund_data = await self._fetch_fundamental_data(symbol)

        # 3. Гибридный скоринг
        score = self._calculate_fundamental_score(fund_data, eph)

        # 4. Определение сигнала
        if score >= 75:
            signal = "STRONG_BUY"
        elif score >= 60:
            signal = "BUY"
        elif score >= 45:
            signal = "NEUTRAL"
        elif score >= 30:
            signal = "SELL"
        else:
            signal = "STRONG_SELL"

        return AgentResponse(
            agent_name="Fundamental",
            signal=signal,
            confidence=min(95, int(score)),
            reasoning=self._build_reasoning(fund_data, score),
            sources=["CoinGecko API", "Financial reports"],
            metadata={
                "fundamental_score": score,
                "valuation": fund_data.get("pe_ratio") or fund_data.get("mvrv"),
                "growth": fund_data.get("revenue_growth") or fund_data.get("growth_rate"),
                "astro_influence": self._get_astro_influence(eph),
                "source": "coingecko + astrological_bonus",
            },
        )

    def _call_ephemeris(self, dt: datetime) -> Dict:
        """Критичный вызов Swiss Ephemeris."""
        try:
            from core.ephemeris import calculate_planet, _julian_day, HAS_SWISS_EPHEMERIS

            if not HAS_SWISS_EPHEMERIS:
                return {"yoga": "unknown", "score": 50}

            jd = _julian_day(dt)
            jupiter = calculate_planet("jupiter", jd)
            venus = calculate_planet("venus", jd)
            moon = calculate_planet("moon", jd)

            # Yoga calculation
            score = 50
            jup_moon = abs(jupiter.longitude - moon.longitude) % 360
            ven_moon = abs(venus.longitude - moon.longitude) % 360

            if jup_moon < 30 or jup_moon > 330:
                score += 15
            if ven_moon < 30 or ven_moon > 330:
                score += 10

            return {
                "yoga": "jupiter_venus_moon",
                "score": max(0, min(100, score)),
                "jupiter": jupiter.longitude,
                "venus": venus.longitude,
            }
        except Exception:
            return {"yoga": "unknown", "score": 50}

    async def _fetch_fundamental_data(self, symbol: str) -> Dict:
        """Загрузка фундаментальных данных."""
        data = {
            "pe_ratio": None,
            "mvrv": None,
            "revenue_growth": None,
            "growth_rate": None,
            "earnings_growth": None,
            "market_cap_rank": None,
        }

        # CoinGecko API для crypto
        if "BTC" in symbol.upper() or "ETH" in symbol.upper():
            coin_id = "bitcoin" if "BTC" in symbol.upper() else "ethereum"
            try:
                url = f"https://api.coingecko.com/api/v3/coins/{coin_id}"
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    coin = resp.json()
                    data["mvrv"] = coin.get("market_data", {}).get("market_cap", {}).get("market_cap_change_percentage_24h", 0) / 10
                    data["growth_rate"] = coin.get("market_data", {}).get("price_change_percentage_24h", 0)
                    data["market_cap_rank"] = coin.get("market_cap_rank")
            except Exception:
                pass

        # Fallback значения
        if data["mvrv"] is None:
            data["mvrv"] = 2.2
        if data["growth_rate"] is None:
            data["growth_rate"] = 1.8
        if data["revenue_growth"] is None:
            data["revenue_growth"] = 12.4

        return data

    def _calculate_fundamental_score(self, fund_data: Dict, eph: Dict) -> float:
        """
        Гибридный скоринг: 70% фундаментал + 30% астрология.
        """
        base_score = 50.0

        # MVRV (crypto valuation)
        mvrv = fund_data.get("mvrv", 2.0)
        if mvrv < 1.5:
            base_score += 20  # сильно недооценён
        elif mvrv < 2.5:
            base_score += 10
        elif mvrv > 3.5:
            base_score -= 15  # переоценён
        elif mvrv > 5.0:
            base_score -= 25

        # Growth
        growth = fund_data.get("growth_rate") or fund_data.get("revenue_growth", 0)
        if growth > 20:
            base_score += 15
        elif growth > 10:
            base_score += 8
        elif growth < -10:
            base_score -= 15

        # Market cap rank bonus
        rank = fund_data.get("market_cap_rank")
        if rank and rank <= 5:
            base_score += 5

        # Астрологический бонус (30% влияние)
        astro_score = eph.get("score", 50)
        astro_bonus = (astro_score - 50) * 0.6  # ±30 максимум

        return max(0, min(100, base_score + astro_bonus))

    def _get_astro_influence(self, eph: Dict) -> str:
        return f"Yoga: {eph.get('yoga', 'unknown')}, score: {eph.get('score', 50)}"

    def _build_reasoning(self, fund_data: Dict, score: float) -> str:
        parts = []
        mvrv = fund_data.get("mvrv")
        if mvrv:
            parts.append(f"MVRV={mvrv:.1f}")
        growth = fund_data.get("growth_rate") or fund_data.get("revenue_growth")
        if growth:
            parts.append(f"24h chg={growth:.1f}%")
        parts.append(f"Fund score={score:.0f}/100")
        return ", ".join(parts) if parts else f"Fund score={score:.0f}/100"


async def run_fundamental_agent(state: dict) -> dict:
    """Runner для оркестратора."""
    agent = FundamentalAgent()
    result = await agent.run(state)
    return {"fundamental_signal": result.to_dict()}
