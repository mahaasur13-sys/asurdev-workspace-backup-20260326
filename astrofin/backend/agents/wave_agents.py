"""
Wave Agents — Gann, Elliott, Bradley.
"""

from __future__ import annotations

from typing import Dict, Any
from backend.agents.base_agent import BaseAgent, AgentResponse, Signal
from backend.src.decorators import require_ephemeris
from backend.src.swiss_ephemeris import swiss_ephemeris


class GannAgent(BaseAgent):
    """Gann angles, price squares, time cycles."""

    def __init__(self):
        super().__init__(
            name="GannAgent",
            system_prompt="Анализ по методам Ганна: углы 1x1, 1x2, 2x1, ценовые квадраты, time cycles.",
        )

    @require_ephemeris
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        price = context.get("price", 100.0)
        dt = context.get("datetime")

        if dt is None:
            from datetime import datetime
            dt = datetime.now()

        date_str = dt.strftime("%Y-%m-%d")
        time_str = dt.strftime("%H:%M:%S")
        eph = swiss_ephemeris(date=date_str, time=time_str, lat=40.7128, lon=-74.0060, ayanamsa="lahiri")

        # Gann angle calculation (simplified 1x1 = 45°)
        gann_1x1_slope = price / 100  # Approximate
        current_angle = 45  # Placeholder

        # Price square calculation
        sqrt_price = price ** 0.5
        rounded_sqrt = round(sqrt_price, 1)
        next_square = (rounded_sqrt + 0.5) ** 2

        # Decision
        if current_angle >= 45:
            signal = Signal.BUY
            confidence = 60
            summary = f"Gann: угол {current_angle}° — бычий"
        else:
            signal = Signal.NEUTRAL
            confidence = 50
            summary = f"Gann: угол {current_angle}° — нейтральный"

        return AgentResponse(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=summary,
            metadata={"gann_angle": current_angle, "price_square": next_square, **eph},
        )


class ElliotAgent(BaseAgent):
    """Elliott Wave analysis (Impulse, Corrective)."""

    def __init__(self):
        super().__init__(
            name="ElliotAgent",
            system_prompt="Анализ по Эллиотту: волны импульса (1-5), коррекции (A-B-C).",
        )

    @require_ephemeris
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        price = context.get("price", 100.0)
        dt = context.get("datetime")

        if dt is None:
            from datetime import datetime
            dt = datetime.now()

        date_str = dt.strftime("%Y-%m-%d")
        time_str = dt.strftime("%H:%M:%S")
        eph = swiss_ephemeris(date=date_str, time=time_str, lat=40.7128, lon=-74.0060, ayanamsa="lahiri")

        # Simplified wave detection (placeholder)
        wave_count = 3  # Placeholder
        wave_type = "Impulse Wave 3" if wave_count >= 3 else "Wave 1-2"

        if wave_count == 3:
            signal = Signal.BUY
            confidence = 65
            summary = f"Elliot: {wave_type} — ожидается движение вверх"
        elif wave_count == 5:
            signal = Signal.SELL
            confidence = 60
            summary = f"Elliot: {wave_type} — завершение импульса"
        else:
            signal = Signal.NEUTRAL
            confidence = 50
            summary = f"Elliot: {wave_type} — коррекция"

        return AgentResponse(
            agent_name=self.name,
            signal=signal,
            metadata={"wave_count": wave_count, "wave_type": wave_type, **eph},
        )


class BradleyAgent(BaseAgent):
    """Bradley Model — S&P 500 astro-price model."""

    def __init__(self):
        super().__init__(
            name="BradleyAgent",
            system_prompt="Модель Брэдли: астро-плановая модель для S&P 500.",
        )

    @require_ephemeris
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        dt = context.get("datetime")

        if dt is None:
            from datetime import datetime
            dt = datetime.now()

        date_str = dt.strftime("%Y-%m-%d")
        time_str = dt.strftime("%H:%M:%S")
        eph = swiss_ephemeris(date=date_str, time=time_str, lat=40.7128, lon=-74.0060, ayanamsa="lahiri")

        # Bradley formula: aspects between planets create turning points
        bradley_score = 50  # Neutral

        moon_phase = eph.get("panchanga", {}).get("tithi", 15)
        if 8 <= moon_phase <= 12:
            bradley_score = 70  # Potentially bullish
        elif 20 <= moon_phase <= 24:
            bradley_score = 30  # Potentially bearish

        if bradley_score > 55:
            signal = Signal.BUY
            confidence = 55
            summary = "Bradley: благоприятная фаза для покупок"
        elif bradley_score < 45:
            signal = Signal.SELL
            confidence = 55
            summary = "Bradley: благоприятная фаза для продаж"
        else:
            signal = Signal.NEUTRAL
            confidence = 50
            summary = "Bradley: нейтральная фаза"

        return AgentResponse(
            agent_name=self.name,
            signal=signal,
            metadata={"bradley_score": bradley_score, "moon_phase": moon_phase, **eph},
        )
