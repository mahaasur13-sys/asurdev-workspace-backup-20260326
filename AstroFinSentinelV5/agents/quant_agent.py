"""
AstroFin Sentinel v5 — Quant Agent
ML-модели, бэктестирование, предсказание волатильности.
Вес в гибридном сигнале: 20%
"""

import asyncio
import numpy as np
from datetime import datetime
from typing import Dict, Any

from agents.base_agent import BaseAgent, AgentResponse
from agents._impl.ephemeris_decorator import require_ephemeris


class QuantAgent(BaseAgent):
    """
    QuantAgent — количественный анализ и ML.
    80% quant models + 20% астрологический бонус.
    """

    def __init__(self):
        super().__init__(
            name="Quant",
            instructions_path=None,
            domain="quant",
            weight=0.20,
        )

    @require_ephemeris
    async def run(self, state: Dict[str, Any]) -> AgentResponse:
        symbol = state.get("symbol", "BTCUSDT")
        current_price = state.get("current_price") or state.get("price") or 50000
        timeframe = state.get("timeframe_requested", "SWING")
        dt = state.get("datetime") or datetime.utcnow()

        # 1. Астрологические данные
        eph = self._call_ephemeris(dt)

        # 2. Загрузка исторических данных
        price_data = await self._fetch_price_history(symbol, timeframe)

        if len(price_data) < 30:
            return AgentResponse(
                agent_name="Quant",
                signal="NEUTRAL",
                confidence=30,
                reasoning="Insufficient data for quant analysis",
                sources=[],
                metadata={"error": "insufficient_data"},
            )

        # 3. Quant модели
        momentum = self._momentum_analysis(price_data)
        mean_reversion = self._mean_reversion_analysis(price_data, current_price)
        volatility_regime = self._volatility_regime(price_data)

        # 4. Гибридный скоринг
        score = self._calculate_quant_score(momentum, mean_reversion, volatility_regime, eph)

        # 5. Определение сигнала
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
            agent_name="Quant",
            signal=signal,
            confidence=min(92, int(score)),
            reasoning=self._build_reasoning(momentum, mean_reversion, volatility_regime, score),
            sources=["Binance API", "Quant models"],
            metadata={
                "quant_score": score,
                "momentum": momentum,
                "mean_reversion": mean_reversion,
                "volatility_regime": volatility_regime,
                "astro_influence": self._get_astro_influence(eph),
                "source": "binance + quant_models + astrological_bonus",
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
            saturn = calculate_planet("saturn", jd)
            moon = calculate_planet("moon", jd)

            # Jupiter = expansion, Saturn = contraction
            score = 50
            jup_moon = abs(jupiter.longitude - moon.longitude) % 360
            sat_moon = abs(saturn.longitude - moon.longitude) % 360

            if jup_moon < 30 or jup_moon > 330:
                score += 15
            elif 85 < jup_moon < 95:
                score -= 10

            if sat_moon < 30 or sat_moon > 330:
                score += 10  # Saturn trine Moon = stability
            elif 85 < sat_moon < 95:
                score -= 10

            return {
                "yoga": "jupiter_saturn_moon",
                "score": max(0, min(100, score)),
                "jupiter": round(jupiter.longitude, 2),
                "saturn": round(saturn.longitude, 2),
            }
        except Exception:
            return {"yoga": "unknown", "score": 50}

    async def _fetch_price_history(self, symbol: str, timeframe: str) -> list:
        """Загрузка OHLCV с Binance."""
        try:
            import requests
            interval_map = {"1H": "1h", "4H": "4h", "1D": "1d", "1W": "1w", "SWING": "1d", "INTRADAY": "1h"}
            interval = interval_map.get(timeframe, "1d")
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=100"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            return [[float(x[4]), float(x[5])] for x in data]  # [close, volume]
        except Exception:
            return []

    def _momentum_analysis(self, data: list) -> Dict:
        """Анализ моментума."""
        closes = [d[0] for d in data]
        if len(closes) < 20:
            return {"score": 0.5, "summary": "insufficient data", "mom_20": 0}

        mom_20 = (closes[-1] - closes[-20]) / closes[-20] if len(closes) >= 20 else 0
        mom_10 = (closes[-1] - closes[-10]) / closes[-10] if len(closes) >= 10 else 0

        # Normalize to 0-1
        mom_score = 0.5 + mom_20 * 3

        if mom_score > 0.7:
            summary = f"Strong momentum +{mom_20*100:.1f}%"
        elif mom_score > 0.55:
            summary = f"Weak momentum +{mom_20*100:.1f}%"
        elif mom_score > 0.45:
            summary = f"Neutral momentum {mom_20*100:.1f}%"
        elif mom_score > 0.3:
            summary = f"Weak bearish {mom_20*100:.1f}%"
        else:
            summary = f"Strong bearish {mom_20*100:.1f}%"

        return {"score": min(max(mom_score, 0), 1), "summary": summary, "mom_20": mom_20, "mom_10": mom_10}

    def _mean_reversion_analysis(self, data: list, current_price: float) -> Dict:
        """Mean reversion с z-score."""
        closes = [d[0] for d in data]
        if len(closes) < 20:
            return {"signal": "neutral", "z_score": 0}

        mean = np.mean(closes[-20:])
        std = np.std(closes[-20:])
        z_score = (current_price - mean) / std if std > 0 else 0

        if z_score < -2:
            signal = "oversold"
            score = 0.7
        elif z_score < -1:
            signal = "bullish"
            score = 0.6
        elif z_score > 2:
            signal = "overbought"
            score = 0.7
        elif z_score > 1:
            signal = "bearish"
            score = 0.6
        else:
            signal = "neutral"
            score = 0.5

        return {"signal": signal, "z_score": round(z_score, 2), "score": score}

    def _volatility_regime(self, data: list) -> Dict:
        """Определение режима волатильности."""
        closes = [d[0] for d in data]
        if len(closes) < 30:
            return {"regime": "unknown", "vol_pct": 0}

        returns = [np.log(closes[i] / closes[i-1]) for i in range(1, len(closes))]
        vol_10 = np.std(returns[-10:]) * np.sqrt(365) if len(returns) >= 10 else 0
        vol_30 = np.std(returns[-30:]) * np.sqrt(365) if len(returns) >= 30 else vol_10

        if vol_10 > vol_30 * 1.5:
            regime = "high_vol_expanding"
            regime_score = 0.35
        elif vol_10 < vol_30 * 0.7:
            regime = "low_vol_compression"
            regime_score = 0.65
        else:
            regime = "normal"
            regime_score = 0.50

        return {
            "regime": regime,
            "vol_pct": round(vol_30 * 100, 1),
            "score": regime_score,
            "vol_10": round(vol_10 * 100, 1),
        }

    def _calculate_quant_score(self, momentum: Dict, mean_rev: Dict, vol_reg: Dict, eph: Dict) -> float:
        """
        Гибридный скоринг: 80% quant + 20% астрология.
        """
        score = 50.0

        # Momentum (40% weight)
        mom_score = momentum.get("score", 0.5)
        if mom_score > 0.6:
            score += 25
        elif mom_score > 0.55:
            score += 15
        elif mom_score < 0.4:
            score -= 20
        elif mom_score < 0.45:
            score -= 10

        # Mean reversion (30% weight)
        mr_signal = mean_rev.get("signal", "neutral")
        if mr_signal == "oversold":
            score += 20
        elif mr_signal == "bullish":
            score += 10
        elif mr_signal == "overbought":
            score -= 20
        elif mr_signal == "bearish":
            score -= 10

        # Volatility regime (30% weight)
        vol_score = vol_reg.get("score", 0.5)
        if vol_reg.get("regime") == "low_vol_compression":
            score += 10  # Compression = setup for move
        elif vol_reg.get("regime") == "high_vol_expanding":
            score -= 15  # High vol = risky

        # Астрологический бонус (20%)
        astro_score = eph.get("score", 50)
        astro_bonus = (astro_score - 50) * 0.4

        return max(0, min(100, score + astro_bonus))

    def _get_astro_influence(self, eph: Dict) -> str:
        return f"Yoga: {eph.get('yoga', 'unknown')}, score: {eph.get('score', 50)}"

    def _build_reasoning(self, momentum: Dict, mean_rev: Dict, vol_reg: Dict, score: float) -> str:
        parts = []
        parts.append(f"Momentum: {momentum.get('summary', 'N/A')}")
        parts.append(f"MeanRev: {mean_rev.get('signal', 'N/A')} ({mean_rev.get('z_score', 0):.1f}σ)")
        parts.append(f"Vol: {vol_reg.get('regime', 'N/A')} ({vol_reg.get('vol_pct', 0):.1f}% ann)")
        parts.append(f"Quant score={score:.0f}/100")
        return ", ".join(parts)


async def run_quant_agent(state: dict) -> dict:
    """Runner для оркестратора."""
    agent = QuantAgent()
    result = await agent.run(state)
    return {"quant_signal": result.to_dict()}
