"""
PlanetaryHourAgent — расчёт планетарных часов.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Dict, Any
from ..base_agent import BaseAgent, AgentResponse, Signal
from ...src.swiss_ephemeris import swiss_ephemeris, VARAS

class PlanetaryHourAgent(BaseAgent):
    """PlanetaryHourAgent — планетарные часы. Вес: 0.03"""
    PLANETS = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]
    PLANET_QUALITY = {
        "Sun": {"favorable": ["business", "leadership"], "unfavorable": []},
        "Venus": {"favorable": ["love", "creative", "art"], "unfavorable": []},
        "Mercury": {"favorable": ["communication", "learning"], "unfavorable": []},
        "Moon": {"favorable": ["emotions", "intuition"], "unfavorable": []},
        "Saturn": {"favorable": ["work", "structure"], "unfavorable": ["rush"]},
        "Jupiter": {"favorable": ["expansion", "wisdom"], "unfavorable": []},
        "Mars": {"favorable": ["action", "energy"], "unfavorable": ["patience"]},
    }

    def __init__(self):
        super().__init__(
            name="PlanetaryHourAgent",
            system_prompt="Planetary Hours calculation"
        )

    async def run(self, context: Dict[str, Any]) -> AgentResponse:
        activity = context.get("activity", "general")
        now = datetime.utcnow()
        
        current_planet = self._get_current_planet_hour(now)
        next_hours = self._get_next_planetary_hours(now, count=3)
        
        favorable = self.PLANET_QUALITY.get(current_planet, {}).get("favorable", [])
        is_favorable = any(f in activity.lower() for f in favorable) if favorable else True

        if is_favorable:
            signal, confidence = Signal.LONG, 0.65
        else:
            signal, confidence = Signal.NEUTRAL, 0.45

        return AgentResponse(
            agent_name=self.name, signal=signal, confidence=confidence,
            reasoning=f"Current hour: {current_planet}",
            sources=["planetary_hours.md"],
            metadata={"current_planet": current_planet, "next_hours": next_hours, "activity": activity},
        )

    def _get_current_planet_hour(self, dt: datetime) -> str:
        sunrise_hour = 6  # Simplified
        day_var = VARAS[dt.weekday()]
        
        # Calculate planetary hour
        day_index = list(VARAS).index(day_var)
        planet_index = (day_index + dt.hour - sunrise_hour) % 7
        
        return self.PLANETS[planet_index]

    def _get_next_planetary_hours(self, dt: datetime, count: int = 3) -> list:
        hours = []
        for h in range(count):
            next_dt = dt + timedelta(hours=h)
            planet = self._get_current_planet_hour(next_dt)
            hours.append({"hour": next_dt.hour, "planet": planet})
        return hours
