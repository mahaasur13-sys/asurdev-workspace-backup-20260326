"""
Elliot Agent — Elliott Wave (Impulse, Corrective).
"""

import asyncio
import numpy as np
from typing import Dict, Any, List

from backend.agents.base_agent import BaseAgent
from backend.agents.base_agent import AgentResponse, Signal
from backend.core.decorators import require_ephemeris


class ElliotAgent(BaseAgent):
    """
    Эллиотт волны (Impulse, Corrective).
    Вес: 3%
    """

    def __init__(self):
        super().__init__(
            name="ElliotAgent",
            domain="elliot",
            weight=0.03,
            instructions="Elliott Wave analysis agent",
        )

    @require_ephemeris
    async def run(self, state: Dict[str, Any]) -> AgentResponse:
        symbol = state.get("symbol", "BTCUSDT")

        data = await self._fetch_data(symbol)
        waves = self._identify_waves(data)

        score = 50
        if waves["current_wave"] in [1, 3, 5]:
            score += 35
        elif waves["current_wave"] in [2, 4]:
            score += 15

        if waves["impulse"]:
            score += 15

        score = min(100, score)

        if score >= 70:
            final_signal = Signal.STRONG_BUY
        elif score >= 55:
            final_signal = Signal.BUY
        else:
            final_signal = Signal.NEUTRAL

        reasoning = (
            f"Current wave: {waves['current_wave']} ({waves['wave_name']}). "
            f"Impulse: {'Yes' if waves['impulse'] else 'No'}. "
            f"Wave structure: {waves['structure']}."
        )

        return AgentResponse(
            agent_name=self.name,
            signal=final_signal,
            confidence=score / 100,
            score=score,
            reasoning=reasoning,
            sources=["elliot/waves.md"],
            metadata={"waves": waves},
        )

    async def _fetch_data(self, symbol: str) -> List[float]:
        try:
            import requests
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&limit=100"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            return [float(x[4]) for x in data]
        except Exception:
            return []

    def _identify_waves(self, data: List[float]) -> Dict:
        """Simplified wave identification."""
        if len(data) < 30:
            return {"current_wave": 0, "wave_name": "unknown", "impulse": False, "structure": "unclear"}

        # Find swing highs/lows
        highs = []
        lows = []
        for i in range(2, len(data) - 2):
            if data[i] > data[i-1] and data[i] > data[i+1] and data[i] > data[i-2] and data[i] > data[i+2]:
                highs.append(i)
            if data[i] < data[i-1] and data[i] < data[i+1] and data[i] < data[i-2] and data[i] < data[i+2]:
                lows.append(i)

        if not highs or not lows:
            return {"current_wave": 0, "wave_name": "unknown", "impulse": False, "structure": "no_clear_swings"}

        # Current position
        last_idx = len(data) - 1
        if highs and highs[-1] > lows[-1]:
            wave_num = 3 if (len(highs) - 1) % 5 < 2 else 5
            wave_name = ["1", "2", "3", "4", "5"][wave_num] if wave_num < 5 else "5"
        else:
            wave_num = 2 if len(lows) % 2 == 0 else 4
            wave_name = ["1", "2", "3", "4", "5"][wave_num]

        return {
            "current_wave": wave_num,
            "wave_name": wave_name,
            "impulse": wave_num in [1, 3, 5],
            "structure": f"{len(highs)} highs, {len(lows)} lows identified",
        }
