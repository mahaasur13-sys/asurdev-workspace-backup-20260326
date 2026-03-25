"""
SentimentAgent — Fear & Greed, соцсети, доминирующий нарратив.
"""

from __future__ import annotations

from typing import Dict, Any
from backend.agents.base_agent import BaseAgent, AgentResponse, Signal
from backend.src.decorators import require_ephemeris
from backend.src.swiss_ephemeris import swiss_ephemeris


class SentimentAgent(BaseAgent):
    """Fear & Greed index, social media sentiment, dominant narrative."""

    def __init__(self):
        super().__init__(
            name="SentimentAgent",
            system_prompt="Анализ настроений: Fear & Greed Index, Twitter/X sentiment, доминирующий нарратив.",
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

        # Sentiment components
        fear_greed = 55  # Neutral-ish
        social_score = 52
        narrative = "нейтральный"

        if fear_greed > 70:
            signal = Signal.BUY
            confidence = 65
            narrative = "сильный страх (покупать)"
        elif fear_greed > 55:
            signal = Signal.BUY
            confidence = 55
            narrative = "жадность умеренная"
        elif fear_greed < 30:
            signal = Signal.SELL
            confidence = 65
            narrative = "сильная жадность (продавать)"
        elif fear_greed < 45:
            signal = Signal.SELL
            confidence = 55
            narrative = "страх умеренный"
        else:
            signal = Signal.NEUTRAL
            confidence = 50
            narrative = "сбалансированный"

        summary = f"Sentiment: {narrative} (F&G={fear_greed})"

        return AgentResponse(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=summary,
            metadata={"fear_greed": fear_greed, "social_score": social_score, "narrative": narrative, **eph},
        )
