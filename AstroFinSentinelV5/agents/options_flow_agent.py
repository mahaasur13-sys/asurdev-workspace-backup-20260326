"""
AstroFin Sentinel v5 — Options Flow Agent
Анализ опционного потока: gamma exposure, unusual activity, squeeze detection.
Вес в гибридном сигнале: 15%
"""

import asyncio
import requests
from datetime import datetime
from typing import Dict, Any

from agents.base_agent import BaseAgent, AgentResponse, SignalDirection
from agents._impl.ephemeris_decorator import require_ephemeris


class OptionsFlowAgent(BaseAgent):
    """
    OptionsFlowAgent — анализ опционного потока.
    80% options data + 20% астрологический бонус.
    """

    def __init__(self):
        super().__init__(
            name="OptionsFlow",
            instructions_path=None,
            domain="options",
            weight=0.15,
        )

    @require_ephemeris
    async def run(self, state: Dict[str, Any]) -> AgentResponse:
        symbol = state.get("symbol", "BTC")
        dt = state.get("datetime") or datetime.utcnow()

        # 1. Астрологические данные
        eph = self._call_ephemeris(dt)

        # 2. Options flow данные
        flow_data = await self._fetch_options_flow(symbol)

        # 3. Гибридный скоринг
        score = self._calculate_options_score(flow_data, eph)

        # 4. Определение сигнала
        if score >= 80:
            signal = "STRONG_BUY"
        elif score >= 65:
            signal = "BUY"
        elif score >= 50:
            signal = "NEUTRAL"
        elif score >= 35:
            signal = "SELL"
        else:
            signal = "STRONG_SELL"

        return AgentResponse(
            agent_name="OptionsFlow",
            signal=signal,
            confidence=min(92, int(score)),
            reasoning=self._build_reasoning(flow_data, score),
            sources=["Unusual Whales", "Cheddar Flow", "Polygon Options"],
            metadata={
                "options_score": score,
                "unusual_activity": flow_data.get("unusual_volume"),
                "gamma_exposure": flow_data.get("gex"),
                "put_call_ratio": flow_data.get("pcr"),
                "squeeze": flow_data.get("squeeze"),
                "astro_influence": self._get_astro_influence(eph),
                "source": "options_api + astrological_bonus",
            },
        )

    def _call_ephemeris(self, dt: datetime) -> Dict:
        """Критичный вызов Swiss Ephemeris."""
        try:
            from core.ephemeris import calculate_planet, _julian_day, HAS_SWISS_EPHEMERIS

            if not HAS_SWISS_EPHEMERIS:
                return {"yoga": "unknown", "score": 50}

            jd = _julian_day(dt)
            mercury = calculate_planet("mercury", jd)
            venus = calculate_planet("venus", jd)
            jupiter = calculate_planet("jupiter", jd)
            moon = calculate_planet("moon", jd)

            # Mercury rules communications/trading
            score = 50
            merc_moon = abs(mercury.longitude - moon.longitude) % 360
            ven_jup = abs(venus.longitude - jupiter.longitude) % 360

            # Mercury trine Moon = good for trading
            if merc_moon < 30 or merc_moon > 330:
                score += 15
            elif 85 < merc_moon < 95:
                score -= 10

            # Venus-Jupiter trine = favorable
            if ven_jup < 30 or ven_jup > 330:
                score += 10

            return {
                "yoga": "mercury_venus_jupiter",
                "score": max(0, min(100, score)),
                "mercury": mercury.longitude,
                "venus": venus.longitude,
                "jupiter": jupiter.longitude,
            }
        except Exception:
            return {"yoga": "unknown", "score": 50}

    async def _fetch_options_flow(self, symbol: str) -> Dict:
        """
        Загрузка опционных данных.
        TODO: Заменить на реальный API (Unusual Whales, Cheddar Flow, Polygon Options)
        """
        # заглушка
        return {
            "unusual_volume": 1450,
            "gex": 1_250_000_000,
            "pcr": 0.68,
            "large_call_sweep": True,
            "squeeze": False,
        }

    def _calculate_options_score(self, flow: Dict, eph: Dict) -> float:
        """
        Гибридный скоринг: 80% options + 20% астрология.
        """
        base = 50.0

        # Large call sweeps = bullish
        if flow.get("large_call_sweep"):
            base += 25

        # Low put/call ratio = bullish
        pcr = flow.get("pcr", 1.0)
        if pcr < 0.5:
            base += 20
        elif pcr < 0.7:
            base += 10
        elif pcr > 1.2:
            base -= 15
        elif pcr > 1.5:
            base -= 25

        # Squeeze detection
        if flow.get("squeeze"):
            base -= 10  # Squeeze = volatility compression = risk

        # GEX (gamma exposure) — negative GEX = volatility spike risk
        gex = flow.get("gex", 0)
        if gex < -500_000_000:
            base -= 15
        elif gex > 500_000_000:
            base += 10

        # Unusual volume
        vol = flow.get("unusual_volume", 0)
        if vol > 2000:
            base += 10
        elif vol < 500:
            base -= 5

        # Астрологический бонус (20%)
        astro_score = eph.get("score", 50)
        astro_bonus = (astro_score - 50) * 0.4

        return max(0, min(100, base + astro_bonus))

    def _get_astro_influence(self, eph: Dict) -> str:
        return f"Yoga: {eph.get('yoga', 'unknown')}, score: {eph.get('score', 50)}"

    def _build_reasoning(self, flow: Dict, score: float) -> str:
        parts = []
        if flow.get("large_call_sweep"):
            parts.append("Call sweep detected")
        pcr = flow.get("pcr")
        if pcr:
            parts.append(f"PCR={pcr:.2f}")
        gex = flow.get("gex")
        if gex:
            parts.append(f"GEX=${gex/1e6:.0f}M")
        if flow.get("squeeze"):
            parts.append("SQUEEZE")
        parts.append(f"Options score={score:.0f}/100")
        return ", ".join(parts) if parts else f"Options score={score:.0f}/100"


async def run_options_flow_agent(state: dict) -> dict:
    """Runner для оркестратора."""
    agent = OptionsFlowAgent()
    result = await agent.run(state)
    return {"options_flow_signal": result.to_dict()}
