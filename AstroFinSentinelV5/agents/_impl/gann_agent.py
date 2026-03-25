"""
Gann Agent — Gann angles and time/price analysis.
"""

import asyncio
from agents.base_agent import BaseAgent, AgentResponse, SignalDirection
from agents._impl.ephemeris_decorator import require_ephemeris


class GannAgent(BaseAgent[AgentResponse]):
    """
    GannAgent — анализ по методам Ганна.

    Responsibilities:
    1. Calculate Gann angles (1x1, 1x2, 2x1, etc.)
    2. Identify support/resistance at angle intersections
    3. Time forecasts using Gann date clusters
    4. Square of price and time

    Weight: 3% (minor agent)
    """

    def __init__(self):
        super().__init__(
            name="GannAgent",
            instructions_path=None,
            domain="technical",
            weight=0.03,
        )

    @require_ephemeris
    async def analyze(self, state: dict) -> AgentResponse:
        """
        Analyze using Gann's mathematical techniques.
        """
        symbol = state.get("symbol", "BTCUSDT")
        current_price = state.get("current_price", 50000)

        price_data = await self._fetch_ohlcv(symbol, "1d", 90)
        if not price_data:
            return AgentResponse(
                agent_name="GannAgent",
                signal=SignalDirection.NEUTRAL,
                confidence=0.20,
                reasoning="No market data for Gann analysis",
                sources=[],
            )

        closes = [d[0] for d in price_data]
        highs = [d[1] for d in price_data]
        lows = [d[2] for d in price_data]

        # Gann angle analysis
        angles = self._calculate_gann_angles(lows[-1], highs[-1], closes[-1])
        price_square = self._check_price_square(closes[-1])
        time_clusters = self._find_time_clusters(closes)
        astro_dates = await self._check_astro_time_dates(state)

        # Combine signals
        gann_score = (
            angles["score"] * 0.40 +
            price_square["score"] * 0.25 +
            time_clusters["score"] * 0.20 +
            astro_dates["score"] * 0.15
        )

        if gann_score >= 0.60:
            signal = SignalDirection.LONG
            confidence = min(gann_score, 0.75)
        elif gann_score <= 0.35:
            signal = SignalDirection.SHORT
            confidence = min(1 - gann_score, 0.75)
        else:
            signal = SignalDirection.NEUTRAL
            confidence = 0.40

        reasoning = (
            f"Gann angles: {angles['summary']}. "
            f"Price square: {price_square['summary']}. "
            f"Time clusters: {time_clusters['summary']}. "
            f"Astro dates: {astro_dates['summary']}. "
            f"Gann score: {gann_score:.2f}"
        )

        return AgentResponse(
            agent_name="GannAgent",
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            sources=["technical/gann_analysis.md"],
            metadata={
                "gann_score": gann_score,
                "angles": angles,
                "price_square": price_square,
                "time_clusters": time_clusters,
                "astro_dates": astro_dates,
            },
        )

    async def run(self, state: dict) -> AgentResponse:
        return await self.analyze(state)

    async def _fetch_ohlcv(self, symbol: str, interval: str, limit: int) -> list:
        try:
            import requests
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
            resp = requests.get(url, timeout=10)
            data = resp.json()
            return [[float(x[4]), float(x[2]), float(x[3])] for x in data]
        except Exception:
            return []

    def _calculate_gann_angles(self, low: float, high: float, close: float) -> dict:
        """
        Calculate Gann angles from price data.
        1x1 = 45°, 1x2 = 26.5°, 2x1 = 63.25°
        """
        range_price = high - low
        if range_price == 0:
            return {"score": 0.5, "summary": "no range data"}

        # Price position within range
        position = (close - low) / range_price

        # Simplified Gann angle interpretation
        if position > 0.75:
            score = 0.70
            summary = "price above 3x1 angle (strong bullish)"
        elif position > 0.50:
            score = 0.60
            summary = "price at 1x1 angle (balanced)"
        elif position > 0.25:
            score = 0.45
            summary = "price at 1x2 angle (bearish lean)"
        else:
            score = 0.35
            summary = "price below 2x1 angle (strong bearish)"

        return {"score": score, "summary": summary, "position": position}

    def _check_price_square(self, price: float) -> dict:
        """
        Check if price is at a square number (Gann's square of 9 concept).
        """
        import math

        root = math.sqrt(price)
        nearest_square = round(root) ** 2
        distance_pct = abs(price - nearest_square) / price * 100

        if distance_pct < 1:
            score = 0.70
            summary = f"price ${price:,.0f} is square of {round(root)}"
        elif distance_pct < 3:
            score = 0.55
            summary = f"price near square ({(1-distance_pct/3)*100:.0f}% close)"
        else:
            score = 0.45
            summary = f"price not at key square ({distance_pct:.1f}% from nearest)"

        return {"score": score, "summary": summary, "distance_pct": distance_pct}

    def _find_time_clusters(self, closes: list) -> dict:
        """
        Find Gann date clusters (7, 14, 21, 28, 365 days).
        """
        if len(closes) < 30:
            return {"score": 0.5, "summary": "insufficient data"}

        # Simple check — current bar number
        bar_num = len(closes)

        # Check for Gann number anniversaries
        gann_numbers = [7, 14, 21, 28, 30, 45, 60, 90, 120, 180, 270, 365]
        hits = [n for n in gann_numbers if bar_num % n == 0 or n % bar_num == 0]

        if len(hits) >= 2:
            score = 0.65
            summary = f"Gann time cluster: bar {bar_num} aligns with {hits}"
        elif hits:
            score = 0.55
            summary = f"Gann time: bar {bar_num} near {hits[0]}"
        else:
            score = 0.45
            summary = f"no Gann time cluster at bar {bar_num}"

        return {"score": score, "summary": summary, "hits": hits}

    async def _check_astro_time_dates(self, state: dict) -> dict:
        """Check for Gann-style astro time dates."""
        from core.ephemeris import calculate_planet, _julian_day, HAS_SWISS_EPHEMERIS
        from datetime import datetime

        if not HAS_SWISS_EPHEMERIS:
            return {"score": 0.5, "summary": "ephemeris unavailable"}

        now = datetime.utcnow()
        jd = _julian_day(now)

        # Check if any major planet is at a Gann degree (0°, 90°, 180°, 270°)
        planets_to_check = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]
        gann_degrees = [0, 90, 180, 270]
        hits = []

        for planet_name in planets_to_check:
            planet = calculate_planet(planet_name, jd)
            deg_in_sign = planet.longitude % 30

            for gd in gann_degrees:
                if abs(deg_in_sign - gd) < 3:  # within 3 degrees
                    hits.append(f"{planet_name.capitalize()} at {gd}°")

        if len(hits) >= 2:
            score = 0.65
            summary = f"Astro time cluster: {', '.join(hits)}"
        elif hits:
            score = 0.55
            summary = f"Astro time: {hits[0]}"
        else:
            score = 0.45
            summary = "no astro time cluster"

        return {"score": score, "summary": summary, "hits": hits}


async def run_gann_agent(state: dict) -> dict:
    """Runner for orchestrator."""
    agent = GannAgent()
    result = await agent.analyze(state)
    return {"gann_signal": result.to_dict()}
