"""
MuhurtaSpecialist Agent — Auspicious Time Selection
===================================================

Part of AstroCouncil. Specialized in finding optimal timing
for actions based on Vedic astrology rules.

Usage:
    agent = MuhurtaSpecialist()
    result = await agent.analyze({
        "action": "брак",
        "datetime": "2026-03-22T10:00:00",
        "lat": 55.7558,
        "lon": 37.6173
    })
"""

import os
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

from .base_agent import BaseAgent
from agents.types import AgentResponse

# Swiss Ephemeris
try:
    from swiss_ephemeris import swiss_ephemeris
    EPHEMERIS_AVAILABLE = True
except ImportError:
    EPHEMERIS_AVAILABLE = False
    swiss_ephemeris = None

# Muhurta Search
try:
    from muhurta_search import MuhurtaSearcher, MuhurtaWindow
    MUHURTA_SEARCH_AVAILABLE = True
except ImportError:
    MUHURTA_SEARCH_AVAILABLE = False
    MuhurtaSearcher = None


class MuhurtaSpecialist(BaseAgent):
    """
    Specialized agent for finding auspicious timing.
    
    Tools:
    - swiss_ephemeris: for accurate panchanga calculations
    - muhurta_search: for knowledge-based rule matching
    - retrieve_knowledge: for RAG-based knowledge retrieval
    
    Actions supported:
    - брак/свадьба (marriage)
    - путешествие (travel)
    - бизнес/начало (business)
    - ритуал/обряд (ritual)
    - медицина (medical)
    - образование (education)
    """
    
    def __init__(
        self,
        lat: float = 28.6139,
        lon: float = 77.2090,
        knowledge_path: Optional[str] = None,
        **kwargs
    ):
        name = kwargs.pop("name", "MuhurtaSpecialist")
        system_prompt = kwargs.pop(
            "system_prompt",
            "Специалист по выбору благоприятного времени (мухурта). "
            "Используй Swiss Ephemeris для точных расчётов. "
            "Комбинируй астрологические данные с правилами из базы знаний."
        )
        
        super().__init__(name=name, system_prompt=system_prompt, **kwargs)
        
        self.lat = float(lat)
        self.lon = float(lon)
        self.knowledge_path = knowledge_path or os.path.join(
            os.path.dirname(__file__), "..", "..", "knowledge", "vedic"
        )
        
        # Initialize searcher
        if MUHURTA_SEARCH_AVAILABLE:
            self.searcher = MuhurtaSearcher(self.knowledge_path)
        else:
            self.searcher = None
        
        # Action to score modifiers
        self.action_modifiers = {
            "брак": {"weight_nakshatra": 3, "weight_yoga": 2, "weight_choghadiya": 2},
            "путешествие": {"weight_nakshatra": 2, "weight_yoga": 1, "weight_day": 3},
            "бизнес": {"weight_nakshatra": 2, "weight_yoga": 3, "weight_aspect": 2},
            "ритуал": {"weight_nakshatra": 3, "weight_tithi": 3, "weight_month": 2},
        }
    
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """
        Analyze and find auspicious timing for an action.
        
        Context:
        - action: Type of action (required)
        - datetime: Start date/time for search (optional, default: now)
        - lat, lon: Location coordinates (optional, use agent defaults)
        - days_ahead: How many days to search (default: 7)
        """
        # Validate inputs
        action = context.get("action")
        if not action:
            return AgentResponse(
                agent_name=self.name,
                signal="ERROR",
                confidence=0,
                summary="Не указан тип действия (action)",
                details={"error": "Missing required field: action"}
            )
        
        # Get parameters
        dt = context.get("datetime")
        if dt:
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        else:
            dt = datetime.now()
        
        lat = context.get("lat", self.lat)
        lon = context.get("lon", self.lon)
        days_ahead = context.get("days_ahead", 7)
        
        # Validate coordinates
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            return AgentResponse(
                agent_name=self.name,
                signal="ERROR",
                confidence=0,
                summary="Некорректные координаты",
                details={"error": f"Invalid coordinates: {lat}, {lon}"}
            )
        
        # Get ephemeris data
        ephemeris_data = self._get_ephemeris(dt, lat, lon)
        if not ephemeris_data:
            return AgentResponse(
                agent_name=self.name,
                signal="ERROR",
                confidence=0,
                summary="Не удалось получить эфемериды",
                details={"error": "Swiss Ephemeris unavailable or returned error"}
            )
        
        # Get action-specific weights
        weights = self.action_modifiers.get(action.lower(), {
            "weight_nakshatra": 2, "weight_yoga": 2, "weight_choghadiya": 2
        })
        
        # Evaluate current moment
        current_signal = self._evaluate_moment(ephemeris_data, action, weights)
        
        # Find best windows if days_ahead > 0
        best_windows = []
        if days_ahead > 0 and self.searcher:
            try:
                windows = self.searcher.find_muhurta(dt, action, lat, lon, days_ahead)
                best_windows = windows[:3]  # Top 3
            except Exception as e:
                pass  # Fallback to current moment analysis
        
        # Build response
        if best_windows:
            best = best_windows[0]
            signal = "BULLISH" if best.score >= 70 else "NEUTRAL" if best.score >= 50 else "BEARISH"
            confidence = best.score
            
            summary = (
                f"🌙 MuhurtaSpecialist: {signal} ({confidence}%)\n"
                f"   Действие: {action}\n"
                f"   Лучшее время: {best.start_time.strftime('%Y-%m-%d %H:%M')}\n"
                f"   Накшатра: {best.nakshatra} | Йога: {best.yoga}"
            )
            
            details = {
                "action": action,
                "best_window": {
                    "start": best.start_time.isoformat(),
                    "end": best.end_time.isoformat(),
                    "score": best.score,
                    "nakshatra": best.nakshatra,
                    "yoga": best.yoga,
                    "tithi": best.tithi,
                    "reasons": best.reasons,
                    "applied_rules": best.applied_rules,
                },
                "alternative_windows": [
                    {
                        "start": w.start_time.isoformat(),
                        "score": w.score,
                        "nakshatra": w.nakshatra,
                    }
                    for w in best_windows[1:]
                ],
                "current_panchanga": ephemeris_data.get("panchanga", {}),
                "weights_used": weights,
            }
        else:
            # No future windows, use current moment
            signal = current_signal["signal"]
            confidence = current_signal["confidence"]
            summary = (
                f"🌙 MuhurtaSpecialist: {signal} ({confidence}%)\n"
                f"   Действие: {action}\n"
                f"   Текущий момент: {ephemeris_data.get('panchanga', {}).get('nakshatra', 'Unknown')}\n"
                f"   Рекомендация: {current_signal['recommendation']}"
            )
            
            details = {
                "action": action,
                "current_panchanga": ephemeris_data.get("panchanga", {}),
                "current_choghadiya": ephemeris_data.get("current_choghadiya", {}),
                "signal_breakdown": current_signal["breakdown"],
                "recommendation": current_signal["recommendation"],
                "weights_used": weights,
            }
        
        return AgentResponse(
            agent_name=self.name,
            signal=signal,
            confidence=confidence,
            summary=summary,
            details=details,
            metadata={
                "lat": lat,
                "lon": lon,
                "datetime": dt.isoformat(),
                "model": self.model,
            }
        )
    
    def _get_ephemeris(self, dt: datetime, lat: float, lon: float) -> Dict:
        """Get ephemeris data using Swiss Ephemeris."""
        if not EPHEMERIS_AVAILABLE:
            return {}
        
        date_str = dt.strftime("%Y-%m-%d")
        time_str = dt.strftime("%H:%M:%S")
        
        try:
            return swiss_ephemeris(
                date=date_str,
                time=time_str,
                lat=lat,
                lon=lon,
                compute_panchanga=True,
                compute_choghadiya=True,
                compute_ashtakavarga=False,
            )
        except Exception:
            return {}
    
    def _evaluate_moment(
        self, 
        eph: Dict, 
        action: str,
        weights: Dict[str, int]
    ) -> Dict:
        """
        Evaluate if the current moment is auspicious for the action.
        
        Returns: {signal, confidence, breakdown, recommendation}
        """
        panchanga = eph.get("panchanga", {})
        
        nakshatra = panchanga.get("nakshatra", "Unknown")
        yoga = panchanga.get("yoga", "Unknown")
        yoga_category = panchanga.get("yoga_category", "Neutral")
        tithi = panchanga.get("tithi", "Unknown")
        vara = panchanga.get("vara", "Unknown")
        
        choghadiya = eph.get("current_choghadiya", {})
        chogh_type = choghadiya.get("type", "Unknown")
        
        score = 50  # Base
        breakdown = []
        
        # Nakshatra scoring
        good_nakshatras = {
            "Rohini", "Mrigashira", "Punarvasu", "Pushya",
            "Hasta", "Swati", "Uttara Phalguni", "Shravana",
            "Uttara Ashadha", "Uttara Bhadrapada", "Revati"
        }
        
        if nakshatra in good_nakshatras:
            score += 15 * weights.get("weight_nakshatra", 2) // 2
            breakdown.append(f"+ Накшатра {nakshatra} благоприятна")
        else:
            score -= 5
            breakdown.append(f"~ Накшатра {nakshatra} нейтральна")
        
        # Yoga scoring
        if yoga_category == "Auspicious":
            score += 10 * weights.get("weight_yoga", 2) // 2
            breakdown.append(f"+ Йога {yoga} благоприятна")
        elif yoga_category == "Inauspicious":
            score -= 15 * weights.get("weight_yoga", 2) // 2
            breakdown.append(f"- Йога {yoga} неблагоприятна")
        
        # Choghadiya scoring
        good_chogh = {"Amrit", "Siddha", "Shubha", "Labha"}
        bad_chogh = {"Rudra", "Kal", "Rog"}
        
        if chogh_type in good_chogh:
            score += 10 * weights.get("weight_choghadiya", 2) // 2
            breakdown.append(f"+ Чогадия {chogh_type} благоприятна")
        elif chogh_type in bad_chogh:
            score -= 15 * weights.get("weight_choghadiya", 2) // 2
            breakdown.append(f"- Чогадия {chogh_type} неблагоприятна")
        
        # Day of week
        day_scores = {
            "Sunday": -5, "Monday": 5, "Tuesday": -10,
            "Wednesday": 5, "Thursday": 15, "Friday": 10, "Saturday": -5
        }
        day_score = day_scores.get(vara, 0)
        score += day_score
        breakdown.append(f"{'+' if day_score >= 0 else ''}{day_score} День: {vara}")
        
        # Normalize
        score = max(0, min(100, score))
        
        # Determine signal
        if score >= 70:
            signal = "BULLISH"
            recommendation = f"Благоприятное время для {action}"
        elif score >= 50:
            signal = "NEUTRAL"
            recommendation = f"Приемлемое время для {action}, есть лучшие окна"
        else:
            signal = "BEARISH"
            recommendation = f"Неблагоприятное время для {action}, перенесите"
        
        return {
            "signal": signal,
            "confidence": score,
            "breakdown": breakdown,
            "recommendation": recommendation,
        }
    
    def get_rag_context(self, query: str, top_k: int = 3) -> Optional[str]:
        """Get relevant context from knowledge base."""
        if not self.searcher:
            return None
        
        try:
            rules = self.searcher._get_rules_for_action(query)
            if rules:
                return "\n\n".join(rules[:top_k])
        except Exception:
            pass
        
        return None


# =============================================================================
# STANDALONE TEST
# =============================================================================

async def test_muhurta_specialist():
    """Test MuhurtaSpecialist."""
    print("🌙 MuhurtaSpecialist — Тест")
    print("=" * 60)
    
    agent = MuhurtaSpecialist(
        lat=55.7558,
        lon=37.6173,
    )
    
    # Test actions
    actions = ["брак", "путешествие", "бизнес"]
    
    for action in actions:
        print(f"\n{'='*60}")
        print(f"Тест действия: {action}")
        print("-" * 60)
        
        result = await agent.analyze({
            "action": action,
            "datetime": datetime.now().isoformat(),
            "lat": 55.7558,
            "lon": 37.6173,
            "days_ahead": 3,
        })
        
        print(f"Signal: {result.signal}")
        print(f"Confidence: {result.confidence}%")
        print(f"\nSummary:\n{result.summary}")
        print(f"\nDetails keys: {list(result.details.keys())}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_muhurta_specialist())
