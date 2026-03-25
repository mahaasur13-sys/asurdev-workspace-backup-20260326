"""
Western Electional Astrology — finding optimal electional windows.
Based on William Lilly's "Christian Astrology" methodology.
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from backend.agents.base_agent import BaseAgent, AgentResponse, Signal
from backend.src.swiss_ephemeris import swiss_ephemeris, NAKSHATRAS
from backend.agents.western_electional.dignities import EssentialDignities
from backend.agents.western_electional.aspects import AspectCalculator
from backend.agents.western_electional.houses import HouseCalculator, HouseSystem


@dataclass
class ElectionalWindow:
    """An electional time window for an action."""
    start_time: datetime
    end_time: datetime
    score: float
    quality: str  # "Excellent", "Good", "Fair", "Poor"
    reasons: List[str]
    planetary_positions: Dict[str, str]
    aspects: List[Dict]
    essential_dignities: Dict[str, int]
    moon_sign: str
    moon_phase: str
    ruling_planet_status: Dict[str, int]


class WesternElectionalAgent(BaseAgent):
    """
    Western Electional Astrology Agent.
    
    Finds optimal electional windows for various types of actions:
    - Business ventures
    - Legal matters
    - Travel
    - Romance/Marriage
    - Health procedures
    - Property purchases
    - Financial investments
    
    Based on William Lilly's methodology from "Christian Astrology".
    """
    
    # Action types and their ideal conditions
    ACTION_CONDITIONS = {
        "business": {
            "ideal_signs": ["Aries", "Leo", "Sagittarius", "Capricorn"],
            "avoid_signs": ["Pisces", "Virgo"],
            "best_houses": [1, 10, 11],
            "best_aspects": ["Trine", "Sextile"],
            "avoid_aspects": ["Square", "Opposition"],
            "ideal_moon": ["Cancer", "Leo", "Virgo"],
        },
        "legal": {
            "ideal_signs": ["Aquarius", "Libra", "Sagittarius"],
            "avoid_signs": ["Pisces", "Scorpio"],
            "best_houses": [1, 7, 9, 10],
            "best_aspects": ["Trine", "Sextile", "Conjunction"],
            "avoid_aspects": ["Square"],
            "ideal_moon": ["Libra", "Aquarius"],
        },
        "travel": {
            "ideal_signs": ["Sagittarius", "Gemini", "Aquarius"],
            "avoid_signs": ["Taurus", "Capricorn"],
            "best_houses": [1, 3, 9],
            "best_aspects": ["Trine", "Sextile"],
            "avoid_aspects": ["Square", "Opposition"],
            "ideal_moon": ["Sagittarius", "Gemini"],
        },
        "romance": {
            "ideal_signs": ["Libra", "Venus", "Pisces"],
            "avoid_signs": ["Scorpio", "Capricorn"],
            "best_houses": [1, 5, 7],
            "best_aspects": ["Trine", "Sextile", "Conjunction"],
            "avoid_aspects": ["Square"],
            "ideal_moon": ["Taurus", "Libra"],
        },
        "health": {
            "ideal_signs": ["Aries", "Leo", "Cancer"],
            "avoid_signs": ["Scorpio", "Pisces"],
            "best_houses": [1, 6, 8],
            "best_aspects": ["Trine", "Conjunction"],
            "avoid_aspects": ["Square", "Opposition"],
            "ideal_moon": ["Aries", "Leo"],
        },
        "investment": {
            "ideal_signs": ["Taurus", "Capricorn", "Virgo"],
            "avoid_signs": ["Aries", "Libra"],
            "best_houses": [2, 8, 11],
            "best_aspects": ["Trine", "Sextile"],
            "avoid_aspects": ["Square", "Opposition"],
            "ideal_moon": ["Taurus", "Capricorn"],
        },
    }
    
    def __init__(self):
        super().__init__(
            name="WesternElectionalAgent",
            system_prompt="Western Electional Astrology — finding optimal electional windows"
        )
        self.dignities = EssentialDignities()
        self.aspects = AspectCalculator()
        self.houses = HouseCalculator()
    
    async def run(self, context: Dict) -> AgentResponse:
        """Main entry point."""
        action_type = context.get("action_type", "business")
        location = context.get("location", {"lat": 40.7128, "lon": -74.0060})
        duration_days = context.get("duration_days", 7)
        start_date = context.get("start_date", datetime.now())
        
        windows = await self.find_electional_windows(
            action_type=action_type,
            location=location,
            duration_days=duration_days,
            start_date=start_date
        )
        
        best = windows[0] if windows else None
        
        return AgentResponse(
            agent_name=self.name,
            signal=Signal.LONG if best and best.score >= 70 else Signal.NEUTRAL,
            confidence=(best.score / 100) if best else 0.3,
            reasoning=self._format_reasoning(best, action_type),
            metadata={
                "windows_found": len(windows),
                "best_window": {
                    "start": best.start_time.isoformat() if best else None,
                    "end": best.end_time.isoformat() if best else None,
                    "score": best.score if best else 0,
                    "quality": best.quality if best else "N/A",
                    "reasons": best.reasons if best else [],
                    "moon_sign": best.moon_sign if best else "Unknown",
                },
                "all_windows": [
                    {
                        "start": w.start_time.isoformat(),
                        "end": w.end_time.isoformat(),
                        "score": w.score,
                        "quality": w.quality,
                    }
                    for w in windows[:5]
                ],
            }
        )
    
    async def find_electional_windows(
        self,
        action_type: str,
        location: Dict,
        duration_days: int = 7,
        start_date: Optional[datetime] = None,
        interval_minutes: int = 30
    ) -> List[ElectionalWindow]:
        """
        Find optimal electional windows within the given time range.
        
        Args:
            action_type: Type of action (business, legal, travel, etc.)
            location: Dict with lat/lon
            duration_days: How many days to search
            start_date: Starting date for search
            interval_minutes: Check every N minutes
        
        Returns:
            List of ElectionalWindow sorted by score (best first)
        """
        start_date = start_date or datetime.now()
        conditions = self.ACTION_CONDITIONS.get(action_type, self.ACTION_CONDITIONS["business"])
        
        windows = []
        current = start_date
        
        while current < start_date + timedelta(days=duration_days):
            try:
                window = await self._evaluate_window(
                    dt=current,
                    action_type=action_type,
                    conditions=conditions,
                    location=location
                )
                
                if window and window.score >= 40:
                    # Merge with adjacent windows of similar quality
                    merged = False
                    for existing in windows:
                        if (abs((existing.end_time - window.start_time).total_seconds()) < 3600 and
                            existing.quality == window.quality):
                            existing.end_time = window.end_time
                            existing.score = max(existing.score, window.score)
                            merged = True
                            break
                    
                    if not merged:
                        windows.append(window)
            
            except Exception:
                pass
            
            current += timedelta(minutes=interval_minutes)
        
        # Sort by score descending
        windows.sort(key=lambda x: x.score, reverse=True)
        return windows
    
    async def _evaluate_window(
        self,
        dt: datetime,
        action_type: str,
        conditions: Dict,
        location: Dict
    ) -> Optional[ElectionalWindow]:
        """Evaluate a single time window."""
        date_str = dt.strftime("%Y-%m-%d")
        time_str = dt.strftime("%H:%M:%S")
        
        eph = swiss_ephemeris(
            date=date_str,
            time=time_str,
            lat=location.get("lat", 40.7128),
            lon=location.get("lon", -74.0060),
            compute_panchanga=True
        )
        
        score = 0
        reasons = []
        positives = []
        negatives = []
        
        # === 1. Check Moon Sign ===
        moon_sign = eph["planets"]["moon"]["sign"]
        moon_degree = eph["planets"]["moon"]["degrees"]
        moon_long = eph["planets"]["moon"]["longitude"]
        
        if moon_sign in conditions.get("ideal_moon", []):
            score += 15
            positives.append(f"Moon in {moon_sign} (ideal for {action_type})")
        elif moon_sign in conditions.get("avoid_signs", []):
            score -= 20
            negatives.append(f"Moon in {moon_sign} (avoid for {action_type})")
        else:
            score += 5
        
        # === 2. Check Essential Dignities ===
        dignities = self.dignities
        dignity_scores = {}
        for planet, data in eph["planets"].items():
            planet_dignity, desc = dignities.get_dignity_score(
                planet.capitalize(),
                data["degrees"],
                data["sign"]
            )
            dignity_scores[planet] = planet_dignity
        
        # Bonus for strong ruling planet
        ruling_planet_status = {"score": 0, "description": ""}
        
        # === 3. Check Aspects ===
        positions = {p: data["longitude"] for p, data in eph["planets"].items()}
        aspects = self.aspects.calculate_aspects(positions)
        aspect_score, aspect_desc = self.aspects.get_aspect_nature_score(aspects)
        score += aspect_score * 2
        
        if aspect_score > 0:
            positives.append(f"Harmonious aspects: {aspect_desc}")
        elif aspect_score < 0:
            negatives.append(f"Challenging aspects: {aspect_desc}")
        
        # === 4. Check Moon Phase ===
        tithi = eph.get("panchanga", {}).get("tithi", "")
        if "Shukla" in tithi or "Poornima" in tithi:  # Waxing moon
            score += 10
            positives.append("Waxing Moon (growth energy)")
        elif "Krishna" in tithi or "Amavasya" in tithi:  # Waning moon
            score -= 5
            negatives.append("Waning Moon (decline energy)")
        
        # === 5. Check Day of Week ===
        vara = eph.get("panchanga", {}).get("vara", "")
        day_bonus = {
            "Sunday": {"Mars": 5, "Sun": 10},
            "Monday": {"Moon": 10, "Jupiter": 5},
            "Tuesday": {"Mars": 10, "Saturn": -5},
            "Wednesday": {"Mercury": 10, "Moon": 5},
            "Thursday": {"Jupiter": 10, "Sun": 5},
            "Friday": {"Venus": 10, "Moon": 5},
            "Saturday": {"Saturn": 10, "Mars": -5},
        }
        
        day_info = day_bonus.get(vara, {})
        for planet, bonus in day_info.items():
            score += bonus
            if bonus > 0:
                positives.append(f"{vara} — {planet} well-placed (+{bonus})")
            else:
                negatives.append(f"{vara} — {planet} poorly placed ({bonus})")
        
        # === 6. Check for Retrogrades ===
        # Simplified check — would need more detailed ephemeris data
        
        # === Calculate Final Score ===
        score = max(0, min(100, score))
        
        # Determine quality
        if score >= 80:
            quality = "Excellent"
        elif score >= 65:
            quality = "Good"
        elif score >= 50:
            quality = "Fair"
        else:
            quality = "Poor"
        
        reasons = positives + negatives
        
        return ElectionalWindow(
            start_time=dt,
            end_time=dt + timedelta(minutes=30),
            score=score,
            quality=quality,
            reasons=reasons,
            planetary_positions={p: data["sign"] for p, data in eph["planets"].items()},
            aspects=aspects[:5],
            essential_dignities=dignity_scores,
            moon_sign=moon_sign,
            moon_phase=tithi,
            ruling_planet_status=ruling_planet_status,
        )
    
    def _format_reasoning(self, best: Optional[ElectionalWindow], action_type: str) -> str:
        """Format reasoning text from best window."""
        if not best:
            return f"No favorable electional windows found for {action_type} in the specified period."
        
        reasons_text = "; ".join(best.reasons[:3]) if best.reasons else "Mixed conditions"
        
        return (
            f"Best window for {action_type}: {best.start_time.strftime('%Y-%m-%d %H:%M')} UTC\n"
            f"Score: {best.score}/100 ({best.quality})\n"
            f"Moon in {best.moon_sign}\n"
            f"Reasons: {reasons_text}"
        )


async def run_western_electional_agent(context: Dict) -> Dict:
    """Runner function."""
    agent = WesternElectionalAgent()
    result = await agent.run(context)
    return {"western_electional_signal": result.to_dict()}
