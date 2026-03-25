"""
AspectAnalyzerAgent — Aspects & Synastry.
Анализ аспектов, синастрии, композитов.
"""
from __future__ import annotations
from datetime import datetime
from typing import Dict, Any, List, Tuple
from ..base_agent import BaseAgent, AgentResponse, Signal
from ...src.swiss_ephemeris import swiss_ephemeris

class AspectAnalyzerAgent(BaseAgent):
    """
    AspectAnalyzerAgent — анализ аспектов и синастрии.
    Вес: 0.09
    """
    ASPECTS = {
        "conjunction": 0,    # 0°
        "sextile": 60,       # 60°
        "square": 90,        # 90°
        "trine": 120,       # 120°
        "opposition": 180,   # 180°
    }
    ASPECT_ORBS = {
        "conjunction": 10,
        "sextile": 6,
        "square": 8,
        "trine": 8,
        "opposition": 10,
    }
    ASPECT_SCORES = {
        "conjunction": 0.3,
        "sextile": 0.3,
        "square": -0.4,
        "trine": 0.5,
        "opposition": -0.4,
    }

    def __init__(self):
        super().__init__(
            name="AspectAnalyzerAgent",
            system_prompt="Aspect & Synastry Analysis"
        )

    async def run(self, context: Dict[str, Any]) -> AgentResponse:
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
                reasoning=f"Aspect calculation error: {e}", sources=["aspects.md"],
            )

        aspects = self._calculate_aspects(eph)
        total_score = sum(a["score"] for a in aspects)
        num_aspects = len(aspects)

        # Normalize
        if num_aspects > 0:
            avg_score = total_score / num_aspects
        else:
            avg_score = 0.5

        if avg_score > 0.2:
            signal, confidence = Signal.LONG, min(0.85, 0.6 + avg_score)
        elif avg_score < -0.2:
            signal, confidence = Signal.SHORT, min(0.85, 0.6 + abs(avg_score))
        else:
            signal, confidence = Signal.NEUTRAL, 0.5

        return AgentResponse(
            agent_name=self.name, signal=signal, confidence=confidence,
            reasoning=f"Current aspects score: {avg_score:.2f} ({num_aspects} active aspects)",
            sources=["aspects.md", "western_astrology.md"],
            metadata={"aspects": aspects[:10], "avg_score": avg_score},
        )

    def _calculate_aspects(self, eph: Dict) -> List[Dict]:
        aspects = []
        planets = eph.get("planets", {})
        planet_list = list(planets.keys())

        for i, p1 in enumerate(planet_list):
            for p2 in planet_list[i+1:]:
                lon1 = planets[p1].get("longitude", 0)
                lon2 = planets[p2].get("longitude", 0)
                
                diff = abs(lon1 - lon2) % 360
                if diff > 180:
                    diff = 360 - diff

                for aspect_name, aspect_angle in self.ASPECTS.items():
                    orb = abs(diff - aspect_angle)
                    if orb <= self.ASPECT_ORBS[aspect_name]:
                        score = self.ASPECT_SCORES[aspect_name] * (1 - orb / self.ASPECT_ORBS[aspect_name])
                        aspects.append({
                            "planet1": p1,
                            "planet2": p2,
                            "aspect": aspect_name,
                            "exactness": 1 - orb / self.ASPECT_ORBS[aspect_name],
                            "score": score,
                        })

        aspects.sort(key=lambda x: abs(x["score"]), reverse=True)
        return aspects
