"""
DignityScorerAgent — расчёт эссенциальных достоинств (западных и ведических).
"""
from __future__ import annotations
from datetime import datetime
from typing import Dict, Any
from backend.agents.base_agent import BaseAgent, AgentResponse, Signal
from backend.src.swiss_ephemeris import swiss_ephemeris

class DignityScorerAgent(BaseAgent):
    """DignityScorerAgent — расчёт достоинств. Вес: 0.05"""
    DIGNITIES = {
        "exaltation": 1.0,
        "domicile": 0.9,
        "triplicity": 0.6,
        "terms": 0.4,
        "decans": 0.2,
        "detriment": -0.5,
        "fall": -0.7,
    }

    def __init__(self):
        super().__init__(
            name="DignityScorerAgent",
            system_prompt="Essential Dignities calculation"
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
                reasoning=f"Dignity error: {e}", sources=["dignities.md"],
            )

        dignities = self._calculate_dignities(eph)
        avg_score = sum(d["score"] for d in dignities.values()) / len(dignities)

        return AgentResponse(
            agent_name=self.name,
            signal=Signal.LONG if avg_score > 0.6 else Signal.NEUTRAL,
            confidence=abs(avg_score - 0.5) + 0.3,
            reasoning=f"Overall dignity: {avg_score:.2f}",
            sources=["dignities.md", "western_astrology.md"],
            metadata={"dignities": dignities, "avg_score": avg_score},
        )

    def _calculate_dignities(self, eph: Dict) -> Dict:
        planets = eph.get("planets", {})
        result = {}
        
        for planet, data in planets.items():
            sign = data.get("sign", "")
            score = 0.5
            
            # Simplified dignity check
            if sign in ["Cancer", "Aries"]:
                score = 0.95  # Exalted
            elif sign in ["Leo", "Sun"]:
                score = 0.9  # Domicile
            elif sign in ["Capricorn", "Aquarius"]:
                score = 0.85
            
            result[planet] = {"sign": sign, "score": score}
        
        return result
