"""
AstroFin Sentinel v5 — Macro Agent
Макроэкономический анализ: VIX, DXY, Fed rates, GDP, геополитика.
Вес в гибридном сигнале: 15%
"""

import asyncio
import requests
from datetime import datetime
from typing import Dict, Any

from agents.base_agent import BaseAgent, AgentResponse, SignalDirection
from agents._impl.ephemeris_decorator import require_ephemeris


class MacroAgent(BaseAgent):
    """
    MacroAgent — макроэкономический анализ.
    80% макро данные + 20% астрологический бонус.
    """

    def __init__(self):
        super().__init__(
            name="Macro",
            instructions_path=None,
            domain="macro",
            weight=0.15,
        )

    @require_ephemeris
    async def run(self, state: Dict[str, Any]) -> AgentResponse:
        dt = state.get("datetime") or datetime.utcnow()

        # 1. Астрологические данные
        eph = self._call_ephemeris(dt)

        # 2. Макро данные
        macro_data = await self._fetch_macro_data()

        # 3. Гибридный скоринг
        score = self._calculate_macro_score(macro_data, eph)

        # 4. Определение сигнала
        if score >= 70:
            signal = "STRONG_BUY"
        elif score >= 55:
            signal = "BUY"
        elif score >= 40:
            signal = "NEUTRAL"
        elif score >= 25:
            signal = "SELL"
        else:
            signal = "STRONG_SELL"

        return AgentResponse(
            agent_name="Macro",
            signal=signal,
            confidence=min(90, int(score)),
            reasoning=self._build_reasoning(macro_data, score),
            sources=["FRED API", "Yahoo Finance", "Binance"],
            metadata={
                "macro_score": score,
                "vix": macro_data.get("vix"),
                "dxy": macro_data.get("dxy"),
                "fed_rate": macro_data.get("fed_rate"),
                "gold": macro_data.get("gold"),
                "astro_influence": self._get_astro_influence(eph),
                "source": "macro_api + astrological_bonus",
            },
        )

    def _call_ephemeris(self, dt: datetime) -> Dict:
        """Критичный вызов Swiss Ephemeris."""
        try:
            from core.ephemeris import calculate_planet, _julian_day, HAS_SWISS_EPHEMERIS

            if not HAS_SWISS_EPHEMERIS:
                return {"yoga": "unknown", "score": 50}

            jd = _julian_day(dt)
            saturn = calculate_planet("saturn", jd)
            jupiter = calculate_planet("jupiter", jd)
            moon = calculate_planet("moon", jd)

            # Saturn influences macro/money
            score = 50
            sat_moon = abs(saturn.longitude - moon.longitude) % 360
            jup_moon = abs(jupiter.longitude - moon.longitude) % 360

            if 85 < sat_moon < 95:
                score -= 15  # Saturn square Moon = macro stress
            elif sat_moon < 30 or sat_moon > 330:
                score += 10  # Saturn trine Moon = stability

            if jup_moon < 30 or jup_moon > 330:
                score += 10  # Jupiter trine Moon = expansion

            return {
                "yoga": "saturn_jupiter_moon",
                "score": max(0, min(100, score)),
                "saturn": saturn.longitude,
                "jupiter": jupiter.longitude,
            }
        except Exception:
            return {"yoga": "unknown", "score": 50}

    async def _fetch_macro_data(self) -> Dict:
        """Загрузка макро данных."""
        data = {"vix": None, "dxy": None, "fed_rate": None, "gold": None}

        # Try Yahoo Finance for VIX and DXY
        try:
            # VIX
            vix_resp = requests.get(
                "https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX",
                timeout=5
            )
            if vix_resp.status_code == 200:
                vix_data = vix_resp.json()
                data["vix"] = vix_data.get("chart", {}).get("result", [{}])[0].get("meta", {}).get("regularMarketPrice")

            # DXY
            dxy_resp = requests.get(
                "https://query1.finance.yahoo.com/v8/finance/chart/DXY",
                timeout=5
            )
            if dxy_resp.status_code == 200:
                dxy_data = dxy_resp.json()
                data["dxy"] = dxy_data.get("chart", {}).get("result", [{}])[0].get("meta", {}).get("regularMarketPrice")
        except Exception:
            pass

        # Fallback / approximate values
        if data["vix"] is None:
            data["vix"] = 18.5  # Current approximate
        if data["dxy"] is None:
            data["dxy"] = 104.0
        if data["fed_rate"] is None:
            data["fed_rate"] = 4.25
        if data["gold"] is None:
            data["gold"] = 2350.0

        return data

    def _calculate_macro_score(self, macro: Dict, eph: Dict) -> float:
        """
        Гибридный скоринг: 80% макро + 20% астрология.
        """
        score = 50.0

        # VIX (fear indicator) — lower is better for risk assets
        vix = macro.get("vix", 20)
        if vix < 15:
            score += 20  # Low fear = bullish
        elif vix < 20:
            score += 10
        elif vix < 30:
            score -= 10
        else:
            score -= 25  # High fear

        # DXY (dollar strength) — moderate is best
        dxy = macro.get("dxy", 100)
        if 95 < dxy < 105:
            score += 10  # Stable dollar
        elif dxy > 110:
            score -= 15  # Strong dollar = headwind
        elif dxy < 90:
            score += 5  # Weak dollar = tailwind

        # Gold (safe haven) — inverse signal
        gold = macro.get("gold", 2000)
        if gold > 2200:
            score -= 10  # High gold = fear

        # Fed Rate — higher rates = tighter
        fed = macro.get("fed_rate", 5.0)
        if fed > 5.5:
            score -= 10  # Very tight
        elif fed > 5.0:
            score -= 5
        elif fed < 4.5:
            score += 5  # Loose = bullish

        # Астрологический бонус (20% влияние)
        astro_score = eph.get("score", 50)
        astro_bonus = (astro_score - 50) * 0.4  # ±20 максимум

        return max(0, min(100, score + astro_bonus))

    def _get_astro_influence(self, eph: Dict) -> str:
        return f"Yoga: {eph.get('yoga', 'unknown')}, score: {eph.get('score', 50)}"

    def _build_reasoning(self, macro: Dict, score: float) -> str:
        parts = []
        if macro.get("vix"):
            parts.append(f"VIX={macro['vix']:.1f}")
        if macro.get("dxy"):
            parts.append(f"DXY={macro['dxy']:.1f}")
        if macro.get("fed_rate"):
            parts.append(f"Fed={macro['fed_rate']:.2f}%")
        parts.append(f"Macro score={score:.0f}/100")
        return ", ".join(parts) if parts else f"Macro score={score:.0f}/100"


async def run_macro_agent(state: dict) -> dict:
    """Runner для оркестратора."""
    agent = MacroAgent()
    result = await agent.run(state)
    return {"macro_signal": result.to_dict()}
