"""
QuantAgent — ML-модели, бэктестирование, Polygon.io данные.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Any

import numpy as np

from backend.agents.base_agent import BaseAgent, AgentResponse, Signal
from backend.src.decorators import require_ephemeris
from backend.src.swiss_ephemeris import swiss_ephemeris
from backend.utils.polygon_client import get_polygon_client


class QuantAgent(BaseAgent):
    """
    QuantAgent — количественный анализ (ML + бэктестирование).

    Responsibilities:
    - Загрузка исторических данных с Polygon.io
    - Бэктестирование простых стратегий
    - ML-прогноз (линейная регрессия по тренду)
    - Определение волатильности иregime detection
    - Astro-бонус ( благоприятные планетные конфигурации)
    """

    def __init__(self):
        super().__init__(name="Quant")

    @require_ephemeris
    async def analyze(self, state: Dict[str, Any]) -> AgentResponse:
        symbol = state.get("symbol", "AAPL")
        price = state.get("price", 170.0)
        days = state.get("days", 365)

        # 1) Polygon.io real data
        polygon = get_polygon_client()
        
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        try:
            aggs = await polygon.get_aggs(symbol, "1", "day", from_date, to_date)
            results = aggs.get("results", [])
        except Exception:
            results = []

        if len(results) < 30:
            return AgentResponse(
                agent_name=self.name,
                signal=Signal.NEUTRAL,
                confidence=30,
                reasoning="Недостаточно данных для анализа",
            )

        closes = [r["c"] for r in results]
        volumes = [r["v"] for r in results]
        highs = [r["h"] for r in results]
        lows = [r["l"] for r in results]

        # 2) Technical indicators
        momentum_score = self._momentum(closes)
        mean_reversion_score = self._mean_reversion(closes, price)
        volatility_regime = self._volatility_regime(closes)

        # 3) ML prediction (simple linear regression)
        ml_signal, ml_confidence = self._ml_prediction(closes)

        # 4) Backtest simple strategy
        backtest_score = self._backtest(results)

        # 5) Combine
        combined_score = (
            momentum_score * 0.25
            + mean_reversion_score * 0.20
            + ml_signal * 0.30
            + backtest_score * 0.25
        )

        if combined_score > 65:
            direction = Signal.STRONG_BUY
            confidence = min(90, int(combined_score))
        elif combined_score > 55:
            direction = Signal.BUY
            confidence = int(combined_score)
        elif combined_score < 35:
            direction = Signal.SELL
            confidence = int(100 - combined_score)
        elif combined_score < 45:
            direction = Signal.STRONG_SELL
            confidence = min(85, int(100 - combined_score))
        else:
            direction = Signal.NEUTRAL
            confidence = 50

        reasoning = (
            f"Momentum={momentum_score:.0f}%, "
            f"MeanRev={mean_reversion_score:.0f}%, "
            f"Backtest={backtest_score:.0f}%, "
            f"VolRegime={volatility_regime}"
        )

        return AgentResponse(
            agent_name=self.name,
            signal=direction,
            metadata={
                "ml_signal": ml_signal,
                "ml_confidence": ml_confidence,
                "momentum_score": momentum_score,
                "mean_reversion_score": mean_reversion_score,
                "backtest_score": backtest_score,
                "volatility_regime": volatility_regime,
                "data_points": len(results),
            },
        )

    def _ml_prediction(self, closes: list) -> tuple[float, float]:
        """Simple linear regression on last 30 days."""
        if len(closes) < 30:
            return 50.0, 30.0

        y = np.array(closes[-30:])
        x = np.arange(len(y))
        x_mean = x.mean()
        y_mean = y.mean()

        slope = np.sum((x - x_mean) * (y - y_mean)) / (np.sum((x - x_mean) ** 2) + 1e-9)
        intercept = y_mean - slope * x_mean

        next_pred = slope * len(y) + intercept
        current = closes[-1]
        change_pct = ((next_pred - current) / current) * 100

        # R-squared
        y_pred = slope * x + intercept
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y_mean) ** 2)
        r_squared = max(0, 1 - ss_res / (ss_tot + 1e-9))

        if change_pct > 3:
            signal = 75 + min(abs(change_pct) * 3, 15)
        elif change_pct > 1:
            signal = 60 + change_pct * 3
        elif change_pct < -3:
            signal = 25 - min(abs(change_pct) * 3, 15)
        elif change_pct < -1:
            signal = 40 + change_pct * 3
        else:
            signal = 50 + change_pct * 2

        confidence = r_squared * 80 + 20
        return signal, confidence

    def _momentum(self, closes: list) -> float:
        """Momentum score (% change over dataset)."""
        if len(closes) < 20:
            return 50.0
        mom_20 = ((closes[-1] - closes[-20]) / closes[-20]) * 100
        mom_score = 50 + mom_20 * 5
        return max(0, min(100, mom_score))

    def _mean_reversion(self, closes: list, current_price: float) -> float:
        """Mean reversion using Z-score."""
        if len(closes) < 20:
            return 50.0
        recent = closes[-20:]
        mean = np.mean(recent)
        std = np.std(recent)
        z_score = (current_price - mean) / (std + 1e-9)
        if z_score < -2:
            return 75  # oversold
        elif z_score < -1:
            return 60
        elif z_score > 2:
            return 25  # overbought
        elif z_score > 1:
            return 40
        return 50

    def _volatility_regime(self, closes: list) -> str:
        """Detect volatility regime."""
        if len(closes) < 30:
            return "unknown"
        returns = np.diff(np.log(closes))
        vol_10 = np.std(returns[-10:]) * np.sqrt(365) if len(returns) >= 10 else 0
        vol_30 = np.std(returns[-30:]) * np.sqrt(365) if len(returns) >= 30 else vol_10
        ratio = vol_10 / (vol_30 + 1e-9)
        if ratio > 1.5:
            return "high_vol_expanding"
        elif ratio < 0.7:
            return "low_vol_contracts"
        return "normal"

    def _backtest(self, results: list) -> float:
        """Simple moving average crossover backtest."""
        if len(results) < 50:
            return 50.0
        closes = [r["c"] for r in results]
        ma10 = np.mean(closes[-10:])
        ma30 = np.mean(closes[-30:])
        if ma10 > ma30 * 1.02:
            return 70
        elif ma10 < ma30 * 0.98:
            return 30
        return 50
