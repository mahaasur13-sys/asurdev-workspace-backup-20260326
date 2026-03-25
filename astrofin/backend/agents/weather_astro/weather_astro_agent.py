"""
WeatherAstroAgent — Astro-Meteorology.
Астрологический прогноз погоды.
"""
from __future__ import annotations
from datetime import datetime
from typing import Dict, Any
from ..base_agent import BaseAgent, AgentResponse, Signal
from ...src.swiss_ephemeris import swiss_ephemeris

class WeatherAstroAgent(BaseAgent):
    """WeatherAstroAgent — астрологическая метеорология. Вес: 0.05"""
    WEATHER_INDICATORS = {
        "rain": ["Moon", "Neptune", "Venus"],
        "storm": ["Mars", "Jupiter", "Uranus"],
        "clear": ["Sun", "Mercury", "Saturn"],
        "cloudy": ["Venus", "Saturn"],
    }

    def __init__(self):
        super().__init__(
            name="WeatherAstroAgent",
            system_prompt="Astro-Meteorology — weather prediction"
        )

    async def run(self, context: Dict[str, Any]) -> AgentResponse:
        try:
            eph = swiss_ephemeris(
                date=datetime.utcnow().strftime("%Y-%m-%d"),
                time=datetime.utcnow().strftime("%H:%M:%S"),
                compute_panchanga=False
            )
        except Exception as e:
            return AgentResponse(
                agent_name=self.name, signal=Signal.NEUTRAL, confidence=0.3,
                reasoning=f"Weather astro error: {e}", sources=["weather_astrology.md"],
            )

        planets = eph.get("planets", {})
        moon_sign = planets.get("moon", {}).get("sign", "Aries")
        
        weather = self._predict_weather(planets)
        return AgentResponse(
            agent_name=self.name, signal=Signal.NEUTRAL, confidence=0.5,
            reasoning=f"Weather: {weather}",
            sources=["weather_astrology.md"],
            metadata={"moon_sign": moon_sign, "weather_prediction": weather},
        )

    def _predict_weather(self, planets: Dict) -> str:
        moon = planets.get("moon", {}).get("sign", "")
        if moon in ["Pisces", "Cancer", "Scorpio"]:
            return "rainy"
        elif moon in ["Aries", "Leo", "Sagittarius"]:
            return "clear"
        return "variable"
