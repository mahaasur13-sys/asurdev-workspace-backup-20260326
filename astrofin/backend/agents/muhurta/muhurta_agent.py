"""
MuhurtaPredictorAgent — Vedic Muhurta (Classical Indian Electional Astrology).
Накшатры, титхи, чара, мухурта,Yoga и йога-карта.
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Dict, Any, List
from ..base_agent import BaseAgent, AgentResponse, Signal
from ...src.swiss_ephemeris import swiss_ephemeris, NAKSHATRAS

class MuhurtaPredictorAgent(BaseAgent):
    """
    MuhurtaPredictorAgent — Vedic Muhurta analysis.
    Вес: ~0.15
    """
    # Auspicious nakshatras (padas)
    GOOD_NAKSHATRAS = {
        "Rohini": 0.9, "Mrigashirsha": 0.8, "Uttara Phalguni": 0.85,
        "Hasta": 0.9, "Swati": 0.8, "Shravana": 0.85,
        "Dhanishtha": 0.75, "Purva Bhadrapada": 0.8, "Revati": 0.9,
    }
    # Inauspicious nakshatras
    BAD_NAKSHATRAS = {
        "Ashlesha": 0.2, "Magha": 0.3, "Mula": 0.25,
        "Jyeshtha": 0.3, "Purva Ashadha": 0.4,
    }

    def __init__(self):
        super().__init__(
            name="MuhurtaPredictorAgent",
            system_prompt="Vedic Muhurta — Classical Indian Electional Astrology"
        )

    async def run(self, context: Dict[str, Any]) -> AgentResponse:
        query = context.get("user_query", "general")
        venture_type = self._classify_venture(query)
        windows = await self._find_best_muhurta(days_ahead=7, venture_type=venture_type)

        if not windows:
            return AgentResponse(
                agent_name=self.name, signal=Signal.NEUTRAL, confidence=0.3,
                reasoning="No suitable Muhurta found", sources=["muhurta.md", "nakshatras.md"],
            )

        best = windows[0]
        score = best["score"]

        if score > 0.75:
            signal, confidence = Signal.LONG, score
        elif score > 0.55:
            signal, confidence = Signal.NEUTRAL, score
        else:
            signal, confidence = Signal.NEUTRAL, 0.5

        return AgentResponse(
            agent_name=self.name, signal=signal, confidence=confidence,
            reasoning=f"Best Muhurta: {best['datetime']} — {best['nakshatra']} pada {best['pada']}, score: {score:.2f}",
            sources=["muhurta.md", "nakshatras.md", "choghadiya.md"],
            metadata={"venture_type": venture_type, "best_window": best, "all_windows": windows[:5]},
        )

    def _classify_venture(self, query: str) -> str:
        q = query.lower()
        if any(w in q for w in ["business", "startup", "marriage", "travel"]):
            return "auspicious"
        elif any(w in q for w in ["medical", "surgery", "health"]):
            return "health"
        elif any(w in q for w in ["buy", "investment", "property"]):
            return "financial"
        return "general"

    async def _find_best_muhurta(self, days_ahead: int, venture_type: str) -> List[Dict]:
        windows = []
        base = datetime.utcnow()

        for d in range(days_ahead):
            for h in range(6, 22):
                dt = base + timedelta(days=d, hours=h)
                try:
                    eph = swiss_ephemeris(
                        date=dt.strftime("%Y-%m-%d"),
                        time=dt.strftime("%H:%M:%S"),
                        compute_panchanga=True
                    )
                except Exception:
                    continue

                score = self._score_muhurta(eph, venture_type)
                if score > 0.55:
                    panchanga = eph.get("panchanga", {})
                    windows.append({
                        "datetime": dt.isoformat(),
                        "score": score,
                        "nakshatra": panchanga.get("nakshatra", "Unknown"),
                        "pada": panchanga.get("nakshatra_pada", 1),
                        "tithi": panchanga.get("tithi", "Unknown"),
                        "vara": panchanga.get("vara", "Unknown"),
                        "yoga": panchanga.get("yoga", "Unknown"),
                        "karana": panchanga.get("karana", "Unknown"),
                    })

        windows.sort(key=lambda x: x["score"], reverse=True)
        return windows[:10]

    def _score_muhurta(self, eph: Dict, venture_type: str) -> float:
        panchanga = eph.get("panchanga", {})
        nakshatra = panchanga.get("nakshatra", "")
        yoga_category = panchanga.get("yoga_category", "Neutral")

        score = 0.5

        if nakshatra in self.GOOD_NAKSHATRAS:
            score += self.GOOD_NAKSHATRAS[nakshatra] * 0.3
        elif nakshatra in self.BAD_NAKSHATRAS:
            score -= 0.25

        if yoga_category == "Auspicious":
            score += 0.15
        elif yoga_category == "Inauspicious":
            score -= 0.15

        return max(0.1, min(score, 1.0))
