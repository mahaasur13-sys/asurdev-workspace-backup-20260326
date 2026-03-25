"""
FinancialAstroAgent — AstroFinance.
Астрология для финансов, акций, крипты.
"""
from __future__ import annotations
from datetime import datetime
from typing import Dict, Any
from ..base_agent import BaseAgent, AgentResponse, Signal
from ...src.swiss_ephemeris import swiss_ephemeris

class FinancialAstroAgent(BaseAgent):
    """
    FinancialAstroAgent — финансовая астрология.
    Вес: 0.11
    """
    BULLISH_SIGNS = ["Cancer", "Leo", "Virgo", "Scorpio", "Pisces"]
    BEARISH_SIGNS = ["Aries", "Gemini", "Libra", "Capricorn", "Aquarius"]

    def __init__(self):
        super().__init__(
            name="FinancialAstroAgent",
            system_prompt="Financial Astrology — astro analysis for markets"
        )

    async def run(self, context: Dict[str, Any]) -> AgentResponse:
        symbol = context.get("symbol", "BTC")
        now = datetime.utcnow()
        
        try:
            eph = swiss_ephemeris(
                date=now.strftime("%Y-%m-%d"),
                time=now.strftime("%H:%M:%S"),
                compute_panchanga=False
            )
        except Exception as e:
            return AgentResponse(
                agent_name=self.name, signal=Signal.NEUTRAL, confidence=0.3,
                reasoning=f"Financial astro error: {e}", sources=["financial_astrology.md"],
            )

        moon_sign = eph.get("planets", {}).get("moon", {}).get("sign", "Aries")
        sun_sign = eph.get("planets", {}).get("sun", {}).get("sign", "Aries")
        venus_sign = eph.get("planets", {}).get("venus", {}).get("sign", "Taurus")
        jupiter_sign = eph.get("planets", {}).get("jupiter", {}).get("sign", "Sagittarius")

        bullish_count = sum(1 for s in [moon_sign, sun_sign, venus_sign, jupiter_sign] if s in self.BULLISH_SIGNS)
        bearish_count = sum(1 for s in [moon_sign, sun_sign, venus_sign, jupiter_sign] if s in self.BEARISH_SIGNS)

        score = (bullish_count - bearish_count) / 4 + 0.5

        if score > 0.6:
            signal, confidence = Signal.LONG, score
        elif score < 0.4:
            signal, confidence = Signal.SHORT, 1 - score
        else:
            signal, confidence = Signal.NEUTRAL, 0.5

        return AgentResponse(
            agent_name=self.name, signal=signal, confidence=confidence,
            reasoning=f"Moon: {moon_sign}, Venus: {venus_sign}, Jupiter: {jupiter_sign}",
            sources=["financial_astrology.md", "bradley_model.md"],
            metadata={"moon_sign": moon_sign, "sun_sign": sun_sign, "venus_sign": venus_sign, "jupiter_sign": jupiter_sign, "score": score},
        )
