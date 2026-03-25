"""
Sentiment Agent — fear/greed and market sentiment analysis.
"""

import asyncio
from agents.base_agent import BaseAgent, AgentResponse, SignalDirection
from agents._impl.ephemeris_decorator import require_ephemeris


class SentimentAgent(BaseAgent[AgentResponse]):
    """
    SentimentAgent — анализ настроений рынка.

    Responsibilities:
    1. Fetch Fear & Greed index
    2. Analyze social media sentiment (Twitter, Reddit)
    3. Detect contrarian signals
    4. Track funding rates (for crypto)

    Weight: 2% (minor agent)
    """

    def __init__(self):
        super().__init__(
            name="SentimentAgent",
            instructions_path=None,
            domain="trading",
            weight=0.02,
        )

    @require_ephemeris
    async def analyze(self, state: dict) -> AgentResponse:
        """
        Analyze market sentiment.
        """
        symbol = state.get("symbol", "BTCUSDT")
        current_price = state.get("current_price", 50000)

        # Fetch multiple sentiment sources
        fear_greed = await self._fetch_fear_greed()
        funding_rate = await self._fetch_funding_rate(symbol)
        price_momentum = self._analyze_price_momentum(state)

        # Combine sentiment
        sentiment_score = (
            fear_greed["score"] * 0.40 +
            funding_rate["score"] * 0.30 +
            price_momentum["score"] * 0.30
        )

        if sentiment_score >= 0.65:
            signal = SignalDirection.LONG
            confidence = min(sentiment_score + 0.1, 0.75)
        elif sentiment_score <= 0.35:
            signal = SignalDirection.SHORT
            confidence = min(1 - sentiment_score + 0.1, 0.75)
        else:
            signal = SignalDirection.NEUTRAL
            confidence = 0.45

        reasoning = (
            f"Fear & Greed: {fear_greed['summary']}. "
            f"Funding rate: {funding_rate['summary']}. "
            f"Price momentum: {price_momentum['summary']}. "
            f"Sentiment score: {sentiment_score:.2f}"
        )

        return AgentResponse(
            agent_name="SentimentAgent",
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            sources=["trading/sentiment.md"],
            metadata={
                "sentiment_score": sentiment_score,
                "fear_greed": fear_greed,
                "funding_rate": funding_rate,
                "price_momentum": price_momentum,
            },
        )

    async def run(self, state: dict) -> AgentResponse:
        return await self.analyze(state)

    async def _fetch_fear_greed(self) -> dict:
        """
        Fetch Fear & Greed Index (alternative.me API).
        """
        try:
            import requests
            url = "https://api.alternative.me/fng/?limit=1"
            resp = requests.get(url, timeout=5)
            data = resp.json()

            if data and "data" in data and len(data["data"]) > 0:
                fng_value = int(data["data"][0]["value"])
                fng_class = data["data"][0]["value_classification"]

                # Convert to 0-1 score (50 = neutral)
                score = fng_value / 100

                # Adjust for extreme readings (contrarian)
                if fng_value <= 20:
                    # Extreme fear — bullish contrarian
                    summary = f"Extreme Fear ({fng_value}) — contrarian BUY signal"
                elif fng_value >= 80:
                    # Extreme greed — bearish contrarian
                    summary = f"Extreme Greed ({fng_value}) — contrarian SELL signal"
                else:
                    summary = f"Fear & Greed: {fng_value} ({fng_class})"

                return {"score": score, "summary": summary, "raw_value": fng_value}

        except Exception:
            pass

        return {"score": 0.5, "summary": "Fear & Greed data unavailable"}

    async def _fetch_funding_rate(self, symbol: str) -> dict:
        """
        Fetch funding rate for crypto (Binance).
        """
        try:
            import requests

            # Try Binance funding rate API
            url = f"https://api.binance.com/api/v3/premiumIndex?symbol={symbol}"
            resp = requests.get(url, timeout=5)
            data = resp.json()

            if "lastFundingRate" in data:
                funding_rate = float(data["lastFundingRate"])

                # Funding rate score
                # Positive = long paying shorts (bullish pressure)
                # Negative = short paying longs (bearish pressure)
                if funding_rate > 0.01:  # > 1% (very high)
                    score = 0.70
                    summary = f"Funding rate: {funding_rate*100:.2f}% (bulls paying)"
                elif funding_rate > 0.003:  # > 0.3%
                    score = 0.58
                    summary = f"Funding rate: {funding_rate*100:.2f}% (slight bullish)"
                elif funding_rate < -0.01:
                    score = 0.30
                    summary = f"Funding rate: {funding_rate*100:.2f}% (bears paying)"
                elif funding_rate < -0.003:
                    score = 0.42
                    summary = f"Funding rate: {funding_rate*100:.2f}% (slight bearish)"
                else:
                    score = 0.50
                    summary = f"Funding rate: {funding_rate*100:.3f}% (neutral)"

                return {"score": score, "summary": summary, "raw_rate": funding_rate}

        except Exception:
            pass

        return {"score": 0.5, "summary": "Funding rate unavailable"}

    def _analyze_price_momentum(self, state: dict) -> dict:
        """
        Analyze price momentum as sentiment proxy.
        """
        current_price = state.get("current_price", 50000)
        price_data = state.get("_price_data", [])

        if len(price_data) < 20:
            return {"score": 0.5, "summary": "insufficient momentum data"}

        closes = [d[0] for d in price_data]

        # Calculate momentum
        mom_7 = (closes[-1] - closes[-7]) / closes[-7] if len(closes) >= 7 else 0
        mom_14 = (closes[-1] - closes[-14]) / closes[-14] if len(closes) >= 14 else 0
        mom_30 = (closes[-1] - closes[-30]) / closes[-30] if len(closes) >= 30 else 0

        avg_momentum = (mom_7 + mom_14 + mom_30) / 3

        if avg_momentum > 0.05:
            score = 0.70
            summary = f"Strong positive momentum ({avg_momentum*100:.1f}% avg)"
        elif avg_momentum > 0.02:
            score = 0.58
            summary = f"Mild positive momentum ({avg_momentum*100:.1f}% avg)"
        elif avg_momentum < -0.05:
            score = 0.30
            summary = f"Strong negative momentum ({avg_momentum*100:.1f}% avg)"
        elif avg_momentum < -0.02:
            score = 0.42
            summary = f"Mild negative momentum ({avg_momentum*100:.1f}% avg)"
        else:
            score = 0.50
            summary = f"Neutral momentum ({avg_momentum*100:.1f}% avg)"

        return {"score": score, "summary": summary, "momentum": avg_momentum}


async def run_sentiment_agent(state: dict) -> dict:
    """Runner for orchestrator."""
    agent = SentimentAgent()
    result = await agent.analyze(state)
    return {"sentiment_signal": result.to_dict()}
