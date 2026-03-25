"""
TransitSentinelAgent — Transit Analyzer.
Анализ текущих транзитов и их влияния на рынки.
"""
from __future__ import annotations
from datetime import datetime
from typing import Dict, Any, List
from ..base_agent import BaseAgent, AgentResponse, Signal
from ...src.swiss_ephemeris import swiss_ephemeris, SIGNS

class TransitSentinelAgent(BaseAgent):
    """
    TransitSentinelAgent — анализ текущих транзитов.
    Вес: 0.12
    """
    # Transit impact scores
    TRANSIT_IMPACT = {
        "Jupiter": {"conjunction": 0.3, "trine": 0.25, "square": -0.15, "opposition": -0.2},
        "Saturn": {"conjunction": -0.2, "trine": 0.1, "square": -0.25, "opposition": -0.3},
        "Mars": {"conjunction": -0.15, "trine": 0.1, "square": -0.2, "opposition": -0.25},
        "Venus": {"conjunction": 0.25, "trine": 0.2, "square": 0.05, "opposition": 0.1},
        "Mercury": {"conjunction": 0.1, "trine": 0.1, "square": -0.1, "opposition": -0.1},
    }

    def __init__(self):
        super().__init__(
            name="TransitSentinelAgent",
            system_prompt="Transit Analysis — planetary transits and market impact"
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
                reasoning=f"Ephemeris error: {e}", sources=["transit_analysis.md"],
            )

        transits = self._analyze_transits(eph, symbol)
        total_impact = sum(t["impact"] for t in transits)
        
        if total_impact > 0.3:
            signal, confidence = Signal.LONG, min(0.85, 0.5 + abs(total_impact))
        elif total_impact < -0.3:
            signal, confidence = Signal.SHORT, min(0.85, 0.5 + abs(total_impact))
        else:
            signal, confidence = Signal.NEUTRAL, 0.5 - abs(total_impact)

        return AgentResponse(
            agent_name=self.name, signal=signal, confidence=confidence,
            reasoning=f"Transit impact: {total_impact:.2f}. Key: {transits[0]['planet'] if transits else 'N/A'}",
            sources=["transit_analysis.md", "financial_astrology.md"],
            metadata={"transits": transits, "total_impact": total_impact},
        )

    def _analyze_transits(self, eph: Dict, symbol: str) -> List[Dict]:
        planets = eph.get("planets", {})
        transits = []
        
        # Simplified: analyze Moon transits (fastest, most influential for markets)
        moon_sign = planets.get("moon", {}).get("sign", "Aries")
        
        # Moon in fixed signs (Taurus, Leo, Scorpio, Aquarius) often indicates trend continuation
        if moon_sign in ["Taurus", "Leo", "Scorpio", "Aquarius"]:
            transits.append({"planet": "Moon", "sign": moon_sign, "aspect": "fixed", "impact": 0.15})
        
        # Check for ingresses
        sun_sign = planets.get("sun", {}).get("sign", "Aries")
        if sun_sign in ["Taurus", "Libra", "Capricorn", "Aquarius"]:
            transits.append({"planet": "Sun", "sign": sun_sign, "aspect": "ingress", "impact": 0.2})
        
        return transits
