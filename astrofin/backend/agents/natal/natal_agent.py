"""
NatalChartAgent — Natal Analysis.
Построение и интерпретация натальной карты.
"""
from __future__ import annotations
from datetime import datetime
from typing import Dict, Any
from ..base_agent import BaseAgent, AgentResponse, Signal
from ...src.swiss_ephemeris import swiss_ephemeris, SIGNS

class NatalChartAgent(BaseAgent):
    """
    NatalChartAgent — построение и интерпретация натальной карты.
    Вес: 0.10
    """
    def __init__(self):
        super().__init__(
            name="NatalChartAgent",
            system_prompt="Natal Chart Analysis"
        )

    async def run(self, context: Dict[str, Any]) -> AgentResponse:
        birth_date = context.get("birth_date", "1990-01-01")
        birth_time = context.get("birth_time", "12:00:00")
        lat = context.get("lat", 40.7128)
        lon = context.get("lon", -74.0060)

        try:
            eph = swiss_ephemeris(
                date=birth_date,
                time=birth_time,
                lat=lat, lon=lon,
                compute_panchanga=True
            )
        except Exception as e:
            return AgentResponse(
                agent_name=self.name, signal=Signal.NEUTRAL, confidence=0.3,
                reasoning=f"Chart calculation error: {e}", sources=["natal_astrology.md"],
            )

        planets = eph.get("planets", {})
        panchanga = eph.get("panchanga", {})

        # Calculate basic dignities
        sun_dignity = self._get_dignity(planets.get("sun", {}).get("sign", ""))
        moon_dignity = self._get_dignity(planets.get("moon", {}).get("sign", ""))

        avg_dignity = (sun_dignity + moon_dignity) / 2

        if avg_dignity > 0.7:
            signal, confidence = Signal.LONG, avg_dignity
        elif avg_dignity < 0.4:
            signal, confidence = Signal.SHORT, 1 - avg_dignity
        else:
            signal, confidence = Signal.NEUTRAL, 0.5

        return AgentResponse(
            agent_name=self.name, signal=signal, confidence=confidence,
            reasoning=f"Sun: {planets.get('sun',{}).get('sign')}, Moon: {planets.get('moon',{}).get('sign')}, Dignity: {avg_dignity:.2f}",
            sources=["natal_astrology.md", "western_astrology.md"],
            metadata={"planets": planets, "panchanga": panchanga, "dignity_score": avg_dignity},
        )

    def _get_dignity(self, sign: str) -> float:
        exalted = {"Sun": 1.0, "Moon": 1.0, "Mercury": 1.0, "Jupiter": 1.0, "Mars": 1.0}
        domicile = {"Sun": 0.9, "Moon": 0.9, "Mercury": 0.85, "Venus": 0.9, "Mars": 0.85, "Jupiter": 0.9, "Saturn": 0.85}
        debilitated = {"Sun": 0.1, "Moon": 0.1, "Mars": 0.1, "Jupiter": 0.1}
        
        for planet, signs in [("exalted", exalted), ("domicile", domicile), ("debilitated", debilitated)]:
            if sign in signs:
                return signs[sign]
        return 0.5
