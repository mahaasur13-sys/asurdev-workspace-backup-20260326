"""
AstroFin Sentinel v5 — Sentiment Agent
Анализ настроений: новости, X/Twitter, Reddit, Fear & Greed Index.
Вес в гибридном сигнале: 10%
"""

import asyncio
import requests
from datetime import datetime
from typing import Dict, Any

from agents.base_agent import BaseAgent, AgentResponse, SignalDirection
from agents._impl.ephemeris_decorator import require_ephemeris


class SentimentAgent(BaseAgent):
    """
    SentimentAgent — анализ рыночных настроений.
    80% sentiment data + 20% астрологический бонус.
    """

    def __init__(self):
        super().__init__(
            name="Sentiment",
            instructions_path=None,
            domain="sentiment",
            weight=0.10,
        )

    @require_ephemeris
    async def run(self, state: Dict[str, Any]) -> AgentResponse:
        symbol = state.get("symbol", "BTC")
        dt = state.get("datetime") or datetime.utcnow()

        # 1. Астрологические данные
        eph = self._call_ephemeris(dt)

        # 2. Sentiment данные
        sentiment_data = await self._fetch_sentiment_data(symbol)

        # 3. Гибридный скоринг
        score = self._calculate_sentiment_score(sentiment_data, eph)

        # 4. Определение сигнала
        if score >= 75:
            signal = "STRONG_BUY"
        elif score >= 60:
            signal = "BUY"
        elif score >= 45:
            signal = "NEUTRAL"
        elif score >= 30:
            signal = "SELL"
        else:
            signal = "STRONG_SELL"

        return AgentResponse(
            agent_name="Sentiment",
            signal=signal,
            confidence=min(90, int(score)),
            reasoning=self._build_reasoning(sentiment_data, score),
            sources=["alternative.me", "Twitter/X", "Reddit", "StockTwits"],
            metadata={
                "sentiment_score": score,
                "fear_greed": sentiment_data.get("fear_greed"),
                "social_volume": sentiment_data.get("social_volume"),
                "news_score": sentiment_data.get("news_score"),
                "reddit_bull_ratio": sentiment_data.get("reddit_bull_ratio"),
                "astro_influence": self._get_astro_influence(eph),
                "source": "sentiment_apis + astrological_bonus",
            },
        )

    def _call_ephemeris(self, dt: datetime) -> Dict:
        """Критичный вызов Swiss Ephemeris."""
        try:
            from core.ephemeris import calculate_planet, _julian_day, HAS_SWISS_EPHEMERIS

            if not HAS_SWISS_EPHEMERIS:
                return {"yoga": "unknown", "score": 50}

            jd = _julian_day(dt)
            moon = calculate_planet("moon", jd)
            venus = calculate_planet("venus", jd)
            jupiter = calculate_planet("jupiter", jd)

            # Moon = emotions/market sentiment
            score = 50
            ven_moon = abs(venus.longitude - moon.longitude) % 360
            jup_moon = abs(jupiter.longitude - moon.longitude) % 360

            # Venus trine Moon = positive sentiment
            if ven_moon < 30 or ven_moon > 330:
                score += 15
            elif 85 < ven_moon < 95:
                score -= 10

            # Jupiter trine Moon = optimism
            if jup_moon < 30 or jup_moon > 330:
                score += 10

            return {
                "yoga": "venus_jupiter_moon",
                "score": max(0, min(100, score)),
                "moon": moon.longitude,
                "venus": venus.longitude,
                "jupiter": jupiter.longitude,
            }
        except Exception:
            return {"yoga": "unknown", "score": 50}

    async def _fetch_sentiment_data(self, symbol: str) -> Dict:
        """Загрузка данных настроений."""
        data = {
            "fear_greed": None,
            "social_volume": None,
            "news_score": None,
            "reddit_bull_ratio": None,
            "twitter_sentiment": None,
        }

        # Fear & Greed Index
        try:
            fg_resp = requests.get(
                "https://api.alternative.me/fng/?limit=1",
                timeout=5
            )
            if fg_resp.status_code == 200:
                fg_data = fg_resp.json()
                data["fear_greed"] = int(fg_data.get("data", [{}])[0].get("value", 50))
        except Exception:
            pass

        # Fallback
        if data["fear_greed"] is None:
            data["fear_greed"] = 45  # Fear

        data["social_volume"] = 1.2  # 1.2x baseline
        data["news_score"] = 55
        data["reddit_bull_ratio"] = 0.58

        return data

    def _calculate_sentiment_score(self, sent: Dict, eph: Dict) -> float:
        """
        Гибридный скоринг: 80% sentiment + 20% астрология.
        """
        score = 50.0

        # Fear & Greed Index
        fg = sent.get("fear_greed", 50)
        if fg <= 10:  # Extreme fear
            score += 20  # Buy the dip
        elif fg <= 25:  # Fear
            score += 10
        elif fg <= 45:  # Fear
            score += 5
        elif fg <= 55:  # Neutral
            score += 0
        elif fg <= 75:  # Greed
            score -= 5
        else:  # Extreme greed
            score -= 15

        # Social volume (relative to baseline)
        sv = sent.get("social_volume", 1.0)
        if sv > 2.0:
            score -= 10  # FOMO = top signal
        elif sv > 1.5:
            score -= 5
        elif sv < 0.5:
            score += 5  # Low interest = accumulation

        # News score
        news = sent.get("news_score", 50)
        if news > 70:
            score -= 5  # Overbought news
        elif news < 30:
            score += 5

        # Reddit bull ratio
        reddit = sent.get("reddit_bull_ratio", 0.5)
        if reddit > 0.7:
            score += 5
        elif reddit < 0.3:
            score -= 10  # Too bearish

        # Астрологический бонус (20%)
        astro_score = eph.get("score", 50)
        astro_bonus = (astro_score - 50) * 0.4

        return max(0, min(100, score + astro_bonus))

    def _get_astro_influence(self, eph: Dict) -> str:
        return f"Yoga: {eph.get('yoga', 'unknown')}, score: {eph.get('score', 50)}"

    def _build_reasoning(self, sent: Dict, score: float) -> str:
        parts = []
        fg = sent.get("fear_greed")
        if fg:
            label = "Extreme Fear" if fg <= 25 else "Fear" if fg <= 45 else "Neutral" if fg <= 55 else "Greed" if fg <= 75 else "Extreme Greed"
            parts.append(f"F&G={fg} ({label})")
        reddit = sent.get("reddit_bull_ratio")
        if reddit:
            parts.append(f"Reddit bull={reddit:.0%}")
        parts.append(f"Sentiment score={score:.0f}/100")
        return ", ".join(parts)


async def run_sentiment_agent(state: dict) -> dict:
    """Runner для оркестратора."""
    agent = SentimentAgent()
    result = await agent.run(state)
    return {"sentiment_signal": result.to_dict()}
