"""Astrologer Agent - Financial Astrology"""
import math
from datetime import datetime
from typing import Dict, Any, Tuple
from .base_agent import BaseAgent, AgentResponse

MOON_PHASES = ["New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
               "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent"]
NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra"]
TITHIS = ["Shukla Prathama", "Shukla Dvitiya", "Poornima", "Krishna Prathama", "Amavasya"]


class AstrologerAgent(BaseAgent):
    def __init__(self, lat: float = 28.6139, lon: float = 77.2090, **kwargs):
        super().__init__(name="Astrologer", system_prompt="Финансовая астрология", temperature=0.3, **kwargs)
        self.lat = lat
        self.lon = lon
    
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        now = datetime.now()
        moon_phase = self._get_moon_phase(now)
        
        bullish_phases = ["New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous"]
        bearish_phases = ["Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent"]
        
        if moon_phase in bullish_phases:
            signal, confidence = "BULLISH", 55
        elif moon_phase in bearish_phases:
            signal, confidence = "BEARISH", 55
        else:
            signal, confidence = "NEUTRAL", 50
        
        return AgentResponse(
            agent_name="Astrologer",
            signal=signal,
            confidence=confidence,
            summary=f"Moon: {moon_phase}",
            details={"moon_phase": moon_phase, "nakshatra": self._get_nakshatra(now)}
        )
    
    def _get_moon_phase(self, dt: datetime) -> str:
        jd = dt.toordinal() + 1721424.5
        age = (jd - 2451550.1) % 29.530588853
        idx = int((age / 29.530588853) * 8) % 8
        return MOON_PHASES[idx]
    
    def _get_nakshatra(self, dt: datetime) -> str:
        jd = dt.toordinal() + 1721424.5
        age = (jd - 2451550.1) % 29.530588853
        idx = int((age / 29.530588853) * 27) % 27
        return NAKSHATRAS[idx % len(NAKSHATRAS)]
