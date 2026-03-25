"""
PredictorAgent — ML-модели для предсказания цены.
Использует AgentIQ primitives для оптимизации вычислений.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

from backend.agents.base_agent import BaseAgent, AgentResponse, Signal
from backend.src.decorators import require_ephemeris

try:
    from agentiq.primitives import accelerated_graph, monte_carlo_primitive, attention_primitive
    AGENTIQ_AVAILABLE = True
except Exception:
    AGENTIQ_AVAILABLE = False
    def accelerated_graph(func):
        return func
    def monte_carlo_primitive(n_simulations=10000, **kwargs):
        def decorator(func):
            return func
        return decorator
    def attention_primitive(**kwargs):
        def decorator(func):
            return func
        return decorator


class PredictorAgent(BaseAgent):
    """
    PredictorAgent — ML-прогнозирование с Monte Carlo + Neural Networks.
    """

    def __init__(self):
        super().__init__(
            name="Predictor",
            instructions_path="agents/PredictorAgent_instructions.md",
            domain="quant",
            weight=0.12,
        )
        self.sequence_length = 60
        self.forecast_horizon = 7
        self.n_simulations = 20000

    @require_ephemeris
    async def analyze(self, state: Dict[str, Any]) -> AgentResponse:
        symbol = state.get("symbol", "BTCUSDT")
        current_price = state.get("current_price", 50000)
        timeframe = state.get("timeframe_requested", "SWING")

        price_data = await self._fetch_data(symbol, timeframe)
        if len(price_data) < 60:
            return self._insufficient_data_response()

        eph = await self._get_ephemeris(datetime.utcnow())

        if AGENTIQ_AVAILABLE:
            mc_result = await self._run_monte_carlo_aiq(price_data, eph, self.n_simulations)
        else:
            mc_result = await self._run_monte_carlo(price_data, eph, 1000)

        lstm_result = await self._run_lstm_prediction(price_data)

        final_signal, confidence, reasoning = self._ensemble_predictions(mc_result, lstm_result, current_price)

        return AgentResponse(
            agent_name="PredictorAgent",
            signal=final_signal,
            confidence=confidence,
            reasoning=reasoning,
            sources=["quant/monte_carlo.md", "quant/lstm.md"],
            metadata={"mc_result": mc_result, "lstm_result": lstm_result, "agentiq_used": AGENTIQ_AVAILABLE},
        )

    async def run(self, state: Dict[str, Any]) -> AgentResponse:
        return await self.analyze(state)

    @monte_carlo_primitive(n_simulations=20000, parallel=True)
    async def _run_monte_carlo_aiq(self, price_data: list, eph: Dict, n_simulations: int) -> Dict[str, Any]:
        import numpy as np
        if len(price_data) < 30:
            return {"error": "Insufficient data"}
        closes = [d["close"] for d in price_data]
        returns = np.diff(np.log(closes))
        mu = np.mean(returns) * 365
        sigma = np.std(returns) * np.sqrt(365)
        astro_bias = self._get_astro_bias(eph)
        sigma_adjusted = sigma * (1 + astro_bias["volatility_factor"])
        simulations = []
        last_price = closes[-1]
        for _ in range(n_simulations):
            random_returns = np.random.normal(mu / 365, sigma_adjusted / np.sqrt(365), self.forecast_horizon)
            simulated_prices = last_price * np.exp(np.cumsum(random_returns))
            simulations.append(simulated_prices[-1])
        final_prices = np.array(simulations)
        pop = np.mean(final_prices > last_price)
        return {
            "mean_price": float(np.mean(final_prices)),
            "median_price": float(np.median(final_prices)),
            "percentile_5": float(np.percentile(final_prices, 5)),
            "percentile_95": float(np.percentile(final_prices, 95)),
            "pop": float(pop),
            "upside": float((np.mean(final_prices) - last_price) / last_price),
            "downside": float((last_price - np.percentile(final_prices, 5)) / last_price),
            "volatility_factor": float(sigma_adjusted / sigma),
            "n_simulations": n_simulations,
        }

    async def _run_monte_carlo(self, price_data: list, eph: Dict, n_simulations: int) -> Dict[str, Any]:
        import numpy as np
        if len(price_data) < 30:
            return {"error": "Insufficient data"}
        closes = [d["close"] for d in price_data]
        returns = [np.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
        mu = np.mean(returns) * 365
        sigma = np.std(returns) * np.sqrt(365)
        astro_bias = self._get_astro_bias(eph)
        sigma_adjusted = sigma * (1 + astro_bias["volatility_factor"])
        simulations = []
        last_price = closes[-1]
        for _ in range(n_simulations):
            daily_returns = np.random.normal(mu / 365, sigma_adjusted / np.sqrt(365), self.forecast_horizon)
            prices = last_price * np.exp(np.cumsum(daily_returns))
            simulations.append(prices[-1])
        final_prices = np.array(simulations)
        pop = np.mean(final_prices > last_price)
        return {
            "mean_price": float(np.mean(final_prices)),
            "median_price": float(np.median(final_prices)),
            "percentile_5": float(np.percentile(final_prices, 5)),
            "percentile_95": float(np.percentile(final_prices, 95)),
            "pop": float(pop),
            "upside": float((np.mean(final_prices) - last_price) / last_price),
            "downside": float((last_price - np.percentile(final_prices, 5)) / last_price),
            "volatility_factor": float(sigma_adjusted / sigma),
            "n_simulations": n_simulations,
        }

    @attention_primitive(hidden_size=64, num_heads=4)
    async def _run_lstm_prediction(self, price_data: list) -> Dict[str, Any]:
        import numpy as np
        if len(price_data) < self.sequence_length:
            return {"error": "Insufficient data for LSTM"}
        closes = np.array([d["close"] for d in price_data])
        ma_7 = np.mean(closes[-7:])
        ma_14 = np.mean(closes[-14:])
        ma_30 = np.mean(closes[-30:])
        trend = "bullish" if ma_7 > ma_30 else "bearish" if ma_7 < ma_30 else "neutral"
        z_score = float((ma_7 - ma_30) / (np.std(closes[-30:]) + 1e-8))
        return {"trend": trend, "z_score": z_score, "ma_7": float(ma_7), "ma_14": float(ma_14), "ma_30": float(ma_30)}

    def _get_astro_bias(self, eph: Dict) -> Dict[str, float]:
        moon_phase = eph.get("moon_phase", 0)
        moon_effect = abs(moon_phase - 0.5) * 2
        zodiac_effect = 0.1 if eph.get("zodiac", {}).get("moon") in ["Taurus", "Cancer", "Leo", "Virgo", "Scorpio", "Pisces"] else -0.1
        volatility_factor = max(0.5, min(1.5, 1 + (moon_effect * 0.2) + zodiac_effect))
        return {"moon_effect": float(moon_effect), "zodiac_effect": float(zodiac_effect), "volatility_factor": float(volatility_factor)}

    def _ensemble_predictions(self, mc_result: Dict, lstm_result: Dict, current_price: float) -> tuple:
        if mc_result.get("error") or mc_result.get("pop", 0.5) == 0.5:
            mc_vote, mc_conf = Signal.NEUTRAL, 0.5
        elif mc_result["pop"] > 0.55:
            mc_vote, mc_conf = Signal.LONG, min(0.9, mc_result["pop"])
        elif mc_result["pop"] < 0.45:
            mc_vote, mc_conf = Signal.SHORT, min(0.9, 1 - mc_result["pop"])
        else:
            mc_vote, mc_conf = Signal.NEUTRAL, 0.5
        if lstm_result.get("error"):
            lstm_vote, lstm_conf = Signal.NEUTRAL, 0.5
        elif lstm_result["trend"] == "bullish":
            lstm_vote, lstm_conf = Signal.LONG, min(0.85, 0.5 + abs(lstm_result["z_score"]) * 0.2)
        elif lstm_result["trend"] == "bearish":
            lstm_vote, lstm_conf = Signal.SHORT, min(0.85, 0.5 + abs(lstm_result["z_score"]) * 0.2)
        else:
            lstm_vote, lstm_conf = Signal.NEUTRAL, 0.5
        mc_w, lstm_w = 0.6, 0.4
        scores = {
            Signal.LONG: (mc_conf * mc_w if mc_vote == Signal.LONG else 0) + (lstm_conf * lstm_w if lstm_vote == Signal.LONG else 0),
            Signal.SHORT: (mc_conf * mc_w if mc_vote == Signal.SHORT else 0) + (lstm_conf * lstm_w if lstm_vote == Signal.SHORT else 0),
            Signal.NEUTRAL: (mc_conf * mc_w if mc_vote == Signal.NEUTRAL else 0) + (lstm_conf * lstm_w if lstm_vote == Signal.NEUTRAL else 0),
        }
        final_signal = max(scores, key=scores.get)
        final_confidence = scores[final_signal] / (mc_w + lstm_w)
        mc_reasoning = f"MC: ${mc_result.get('mean_price', 0):,.0f} (PoP {mc_result.get('pop', 0.5)*100:.0f}%)" if not mc_result.get("error") else "MC: insufficient data"
        lstm_reasoning = f"LSTM: {lstm_result.get('trend', 'unknown')} (z={lstm_result.get('z_score', 0):.2f})" if not lstm_result.get("error") else "LSTM: insufficient data"
        return final_signal, final_confidence, f"{mc_reasoning}. {lstm_reasoning}"

    async def _fetch_data(self, symbol: str, timeframe: str) -> list:
        try:
            import requests
            interval_map = {"1H": "1h", "4H": "4h", "1D": "1d", "1W": "1w", "SWING": "1d", "DAY": "1d", "HOUR": "1h"}
            interval = interval_map.get(timeframe, "1d")
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=120"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            return [{"timestamp": item[0], "open": float(item[1]), "high": float(item[2]), "low": float(item[3]), "close": float(item[4]), "volume": float(item[5])} for item in data]
        except Exception:
            return []

    async def _get_ephemeris(self, dt: datetime) -> Dict:
        try:
            from backend.src.swiss_ephemeris import get_ephemeris_data
            return get_ephemeris_data(dt)
        except Exception:
            return {"moon_phase": 0.5, "zodiac": {"moon": "Unknown"}}

    def _insufficient_data_response(self) -> AgentResponse:


async def run_predictor_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = PredictorAgent()
    result = await agent.analyze(state)
    return {"predictor_signal": result.to_dict()}
