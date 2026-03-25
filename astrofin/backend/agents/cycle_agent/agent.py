"""
Cycle Agent — FFT decomposition, harmonics, market cycles.
"""

import asyncio
import numpy as np
from typing import Dict, Any

from backend.agents.base_agent import BaseAgent
from backend.agents.base_agent import AgentResponse, Signal
from backend.core.decorators import require_ephemeris


class CycleAgent(BaseAgent):
    """
    Рыночные циклы: FFT-декомпозиция, гармоники.
    Вес: 5%
    """

    def __init__(self):
        super().__init__(
            name="CycleAgent",
            domain="cycles",
            weight=0.05,
            instructions="Market cycles analysis agent",
        )

    @require_ephemeris
    async def run(self, state: Dict[str, Any]) -> AgentResponse:
        symbol = state.get("symbol", "BTCUSDT")
        timeframe = state.get("timeframe", "SWING")

        data = await self._fetch_data(symbol, timeframe)
        if len(data) < 60:
            return self._neutral("Insufficient data for cycle analysis")

        cycles = self._fft_decomposition(data)
        harmonics = self._detect_harmonics(data)

        # Score based on cycle alignment
        score = 50
        if cycles["bullish_phase"]:
            score += 30
        if harmonics["strong"]:
            score += 20

        score = min(100, score)

        if score >= 70:
            final_signal = Signal.STRONG_BUY
        elif score >= 55:
            final_signal = Signal.BUY
        elif score >= 45:
            final_signal = Signal.NEUTRAL
        else:
            final_signal = Signal.SELL

        reasoning = (
            f"Cycle phase: {cycles['phase']}. "
            f"Dominant cycle: {cycles['dominant_period']:.0f} bars. "
            f"Harmonics: {'Strong' if harmonics['strong'] else 'Weak'}."
        )

        return AgentResponse(
            agent_name=self.name,
            signal=final_signal,
            confidence=score / 100,
            score=score,
            reasoning=reasoning,
            sources=["cycles/fft.md"],
            metadata={"cycles": cycles, "harmonics": harmonics},
        )

    async def _fetch_data(self, symbol: str, timeframe: str) -> list:
        try:
            import requests
            interval_map = {"1H": "1h", "4H": "4h", "1D": "1d", "SWING": "1d"}
            interval = interval_map.get(timeframe, "1d")
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=200"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            return [float(x[4]) for x in data]
        except Exception:
            return []

    def _fft_decomposition(self, data: list) -> Dict:
        """Simple FFT for dominant cycle detection."""
        if len(data) < 30:
            return {"bullish_phase": False, "dominant_period": 0, "phase": "unknown"}

        closes = np.array(data[-60:])
        # Detrend
        detrended = closes - np.mean(closes)

        # Simple period estimation via autocorrelation
        n = len(detrended)
        autocorr = [np.corrcoef(detrended[:-lag], detrended[lag:])[0, 1] for lag in range(5, n//2)]

        if not autocorr or max(autocorr) <= 0:
            return {"bullish_phase": False, "dominant_period": 20, "phase": "unknown"}

        dominant_lag = autocorr.index(max(autocorr)) + 5

        # Phase estimation
        phase = "ascending" if detrended[-1] > np.mean(detrended[-dominant_lag:]) else "descending"

        return {
            "bullish_phase": phase == "ascending",
            "dominant_period": dominant_lag,
            "phase": phase,
        }

    def _detect_harmonics(self, data: list) -> Dict:
        """Detect harmonic patterns."""
        if len(data) < 20:
            return {"strong": False, "pattern": "none"}

        returns = np.diff(data[-20:]) / data[-21:-1]
        volatility = np.std(returns)

        return {
            "strong": volatility > 0.02,
            "pattern": "volatile" if volatility > 0.02 else "calm",
        }

    def _neutral(self, reason: str) -> AgentResponse:
        return AgentResponse(
            agent_name=self.name,
            signal=Signal.NEUTRAL,
            confidence=0.3,
            score=50,
            reasoning=reason,
        )
