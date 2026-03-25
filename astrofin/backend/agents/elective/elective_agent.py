"""
ElectivePredictorAgent — Western Electional Astrology.
Поиск лучших элективных окон для начинания.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Dict, Any, List
from ..base_agent import BaseAgent, AgentResponse, Signal
from ...src.swiss_ephemeris import swiss_ephemeris


class ElectivePredictorAgent(BaseAgent):
    """
    ElectivePredictorAgent — поиск лучших элективных окон (Западная традиция).
    Вес: 0.13
    """
    
    def __init__(self):
        super().__init__(
            name="ElectivePredictorAgent",
            system_prompt="Western Electional Astrology — finding optimal electional windows"
        )
        self.weights = {
            "sun_house": 0.20,
            "moon_sign": 0.20,
            "ascendant_dignity": 0.25,
            "aspects_quality": 0.20,
            "benefics": 0.15,
        }
    
    async def run(self, context: Dict[str, Any]) -> AgentResponse:
        query = context.get("user_query", context.get("query", "general"))
        venture_type = self._classify_venture(query)
        windows = await self._find_best_windows(days_ahead=7, venture_type=venture_type)
        
        if not windows:
            return AgentResponse(
                agent_name=self.name,
                signal=Signal.NEUTRAL,
                confidence=0.3,
                reasoning="No suitable elective windows found",
                sources=["elective_principles.md"],
            )
        
        best = windows[0]
        score = best["score"]
        
        if score > 0.7:
            signal, confidence = Signal.LONG, score
        elif score > 0.5:
            signal, confidence = Signal.NEUTRAL, score
        else:
            signal, confidence = Signal.NEUTRAL, max(0.4, score)
        
        return AgentResponse(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            reasoning=f"Best window for {venture_type}: {best['datetime']} (score: {score:.2f})",
            sources=["elective_principles.md", "western_astrology.md"],
            metadata={"venture_type": venture_type, "best_window": best, "all_windows": windows[:5]},
        )
    
    def _classify_venture(self, query: str) -> str:
        q = query.lower()
        if any(w in q for w in ["business", "startup", "career"]):
            return "business_career"
        elif any(w in q for w in ["love", "relationship", "marriage"]):
            return "relationships"
        elif any(w in q for w in ["buy", "purchase", "investment"]):
            return "financial"
        return "general"
    
    async def _find_best_windows(self, days_ahead: int, venture_type: str) -> List[Dict]:
        windows = []
        base = datetime.utcnow()
        
        for d in range(days_ahead):
            for h in [8, 10, 12, 14, 16, 18, 20]:
                dt = base + timedelta(days=d, hours=h)
                try:
                    eph = swiss_ephemeris(
                        date=dt.strftime("%Y-%m-%d"),
                        time=dt.strftime("%H:%M:%S"),
                        compute_panchanga=False
                    )
                except Exception:
                    continue
                
                score = self._score_window(eph)
                if score > 0.5:
                    windows.append({
                        "datetime": dt.isoformat(),
                        "score": score,
                        "moon_sign": eph.get("planets", {}).get("moon", {}).get("sign", "?"),
                        "sun_sign": eph.get("planets", {}).get("sun", {}).get("sign", "?"),
                    })
        
        windows.sort(key=lambda x: x["score"], reverse=True)
        return windows[:10]
    
    def _score_window(self, eph: Dict) -> float:
        planets = eph.get("planets", {})
        moon = planets.get("moon", {}).get("sign", "")
        sun = planets.get("sun", {}).get("sign", "")
        
        score = 0.5
        if moon in ["Cancer", "Taurus", "Libra", "Pisces"]:
            score += 0.2
        if sun in ["Leo", "Aries", "Sagittarius"]:
            score += 0.15
        if moon in ["Cancer", "Pisces", "Scorpio"]:
            score += 0.15
        
        return min(score, 1.0)
