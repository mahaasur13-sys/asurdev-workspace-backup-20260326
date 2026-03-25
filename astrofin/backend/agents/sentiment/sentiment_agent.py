"""SentimentAgent — Market sentiment analysis."""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from backend.agents.base_agent import AgentResponse, Signal, BaseAgent
from backend.src.decorators import require_ephemeris
from backend.src.swiss_ephemeris import swiss_ephemeris


class SentimentAgent(BaseAgent):
    """Market sentiment agent. WEIGHT: 8%."""

    def __init__(self) -> None:
        super().__init__(name="SentimentAgent", system_prompt="Analyze market sentiment and Fear & Greed index.")

    @require_ephemeris
    async def run(self, context: dict[str, Any]) -> AgentResponse:
        symbol = context.get("symbol", "BTC")
        price = context.get("price", 50000)
        eph = await self._get_ephemeris(context.get("datetime"))

        data = await self._fetch_sentiment_data()
        result = self._analyze(data, eph)

        return AgentResponse(
            agent_name=self.name,
            signal=result["signal"],
            confidence=result["confidence"],
            reasoning=result["reasoning"],
            sources=["swiss_ephemeris", "fear_greed"],
            metadata={
                "fear_greed": data.get("fear_greed", 50),
                "social_volume": data.get("social_volume", 0),
                "yoga": eph.get("panchanga", {}).get("yoga", "Unknown"),
            },
        )

    async def _get_ephemeris(self, dt):
        try:
            dt = dt or datetime.now()
            return swiss_ephemeris(dt.strftime("%Y-%m-%d"), dt.strftime("%H:%M:%S"), compute_panchanga=True)
        except Exception:
            return {"panchanga": {"yoga": "Unknown"}}

    async def _fetch_sentiment_data(self) -> dict[str, Any]:
        await asyncio.sleep(0.01)
        return {"fear_greed": 55, "social_volume": 1000, "trend": "improving"}

    def _analyze(self, data, eph) -> dict[str, Any]:
        fg = data.get("fear_greed", 50)
        yoga = eph.get("panchanga", {}).get("yoga", "Neutral")

        score = fg / 100.0
        if yoga in ["Amrita", "Shubha"]:
            score = min(1.0, score + 0.05)

        if score > 0.6:
            return {"signal": Signal.LONG, "confidence": 0.6, "reasoning": f"Sentiment bullish (F&G={fg})"}
        elif score < 0.4:
            return {"signal": Signal.SHORT, "confidence": 0.6, "reasoning": f"Sentiment bearish (F&G={fg})"}
        return {"signal": Signal.NEUTRAL, "confidence": 0.5, "reasoning": f"Sentiment neutral (F&G={fg})"}
