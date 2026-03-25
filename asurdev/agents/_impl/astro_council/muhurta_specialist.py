"""
Muhurta Specialist — Electional Astrology (Western Timing)
=========================================================

Specialist for determining auspicious timing based on:
- Day of week (planetary hour ruler)
- Moon sign compatibility
- Lunar phase (Shubha Karaka timing)
- Nakshatra/Manzil analysis
- House strength for the activity
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field

# Add obsidian module to path for RAG
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
try:
    from asurdev.obsidian.rag_pipeline import VaultRAG
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False


# Western planetary associations for timing
PLANETARY_RULERS = {
    0: "Sun",      # Sunday
    1: "Moon",     # Monday
    2: "Mercury",  # Tuesday (Tyr - Mars)
    3: "Jupiter",  # Wednesday (Odin - Mercury)
    4: "Mars",     # Thursday (Thor - Jupiter)
    5: "Venus",    # Friday (Frigg - Venus)
    6: "Saturn",   # Saturday
}

# Activity-to-planet mappings
ACTIVITY_PLANETS = {
    "wealth": "Jupiter",
    "marriage": "Venus",
    "travel": "Mercury",
    "health": "Mars",
    "education": "Mercury",
    "spiritual": "Jupiter",
    "creative": "Sun",
    "career": "Saturn",
    "relationships": "Venus",
    "communication": "Mercury",
    "legal": "Jupiter",
    "politics": "Saturn",
}

# Lunar phase meanings for timing
LUNAR_PHASES = {
    "new": {"quality": "starting", "suitability": ["new_ventures", "clean_slates"]},
    "waxing": {"quality": "building", "suitability": ["growth", "acquisition"]},
    "full": {"quality": "culmination", "suitability": ["completion", "celebration"]},
    "waning": {"quality": "releasing", "suitability": ["ending", "letting_go"]},
}

# Best days for activities (Western approach)
BEST_DAYS = {
    "wealth": ["Thursday", "Sunday"],
    "marriage": ["Friday", "Sunday"],
    "travel": ["Wednesday", "Thursday"],
    "health": ["Tuesday", "Saturday"],
    "education": ["Wednesday", "Thursday"],
    "spiritual": ["Thursday", "Sunday"],
    "creative": ["Sunday", "Tuesday"],
    "career": ["Saturday", "Thursday"],
    "relationships": ["Friday", "Sunday"],
    "communication": ["Wednesday", "Friday"],
    "legal": ["Thursday", "Sunday"],
    "politics": ["Saturday", "Thursday"],
}


@dataclass
class TimingResult:
    """Result of Muhurta analysis."""
    activity: str
    date: datetime
    day_of_week: str
    planetary_ruler: str
    moon_sign: str
    lunar_phase: str
    score: int
    quality: str
    recommendations: List[str]
    rag_context: List[Dict[str, str]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class MuhurtaReport:
    """Complete Muhurta analysis report."""
    activity: str
    requested_date: datetime
    overall_score: int
    timing_results: List[TimingResult]
    best_timing: Optional[TimingResult]
    rag_insights: List[Dict[str, str]]
    summary: str


class MuhurtaSpecialist:
    """
    Western Electional Astrology Specialist.
    
    Provides auspicious timing recommendations using:
    1. Day of week (Planetary Ruler)
    2. Moon sign compatibility with activity
    3. Lunar phase suitability
    4. House strength for the activity type
    5. RAG-enhanced insights from Obsidian vault (#мухурта)
    """
    
    def __init__(self, vault_path: str = "/home/workspace/obsidian-sync"):
        self.vault_path = vault_path
        self.rag = None
        self.rag_context = []
        
        if RAG_AVAILABLE:
            self._init_rag()
    
    def _init_rag(self):
        """Initialize RAG pipeline for Muhurta insights."""
        try:
            self.rag = VaultRAG(self.vault_path)
            self.rag.scan_vault()
            
            # Get all Muhurta-related blocks
            muhurta_blocks = self.rag.get_by_tag("мухурта")
            
            # Also get related tags
            related_tags = ["мухурта", "timing", "electional", " благоприятный", "начало"]
            self.rag_context = []
            
            for tag in related_tags:
                blocks = self.rag.get_by_tag(tag)
                for block in blocks[:5]:
                    if block not in self.rag_context:
                        self.rag_context.append({
                            "tag": tag,
                            "content": block["content"],
                            "file": block["file"]
                        })
            
            print(f"[MuhurtaSpecialist] RAG initialized: {len(self.rag_context)} context blocks")
            
        except Exception as e:
            print(f"[MuhurtaSpecialist] RAG initialization failed: {e}")
            self.rag_context = []
    
    def analyze_timing(
        self,
        activity: str,
        date: datetime,
        moon_sign: str = "Aries",
        lunar_phase: str = "waxing"
    ) -> TimingResult:
        """Analyze a specific date/time for an activity."""
        
        day_num = date.weekday()
        day_name = date.strftime("%A")
        planetary_ruler = PLANETARY_RULERS[day_num]
        
        # Calculate base score
        score = 5
        
        # Day of week compatibility
        best_days = BEST_DAYS.get(activity.lower(), ["Sunday"])
        if day_name in best_days:
            score += 3
        elif day_name == planetary_ruler:
            score += 2
        
        # Moon sign compatibility
        moon_planet = self._sign_to_planet(moon_sign)
        activity_planet = ACTIVITY_PLANETS.get(activity.lower(), "Jupiter")
        
        if moon_planet == activity_planet:
            score += 3
        elif self._are_friendly(moon_planet, activity_planet):
            score += 1
        
        # Lunar phase suitability
        phase_info = LUNAR_PHASES.get(lunar_phase.lower(), LUNAR_PHASES["waxing"])
        if activity.lower() in phase_info["suitability"]:
            score += 2
        
        # RAG-based adjustments
        rag_bonus = self._get_rag_bonus(activity, date)
        score += rag_bonus
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            activity, day_name, planetary_ruler, moon_sign, lunar_phase
        )
        
        # Warnings
        warnings = self._generate_warnings(
            activity, day_name, planetary_ruler, moon_sign, lunar_phase
        )
        
        # Quality assessment
        if score >= 10:
            quality = "Excellent"
        elif score >= 7:
            quality = "Good"
        elif score >= 4:
            quality = "Moderate"
        else:
            quality = "Poor"
        
        return TimingResult(
            activity=activity,
            date=date,
            day_of_week=day_name,
            planetary_ruler=planetary_ruler,
            moon_sign=moon_sign,
            lunar_phase=lunar_phase,
            score=score,
            quality=quality,
            recommendations=recommendations,
            warnings=warnings
        )
    
    def find_best_timing(
        self,
        activity: str,
        start_date: datetime,
        days_ahead: int = 7,
        preferred_hour: Optional[int] = None
    ) -> MuhurtaReport:
        """Find the best timing window for an activity."""
        
        results = []
        current = start_date
        
        for _ in range(days_ahead):
            timing = self.analyze_timing(activity, current)
            results.append(timing)
            current += timedelta(days=1)
        
        # Find best timing
        best = max(results, key=lambda x: x.score)
        
        # Get RAG insights
        rag_insights = self._search_rag(activity)
        
        summary = self._generate_summary(activity, best, results)
        
        return MuhurtaReport(
            activity=activity,
            requested_date=start_date,
            overall_score=best.score,
            timing_results=results,
            best_timing=best,
            rag_insights=rag_insights,
            summary=summary
        )
    
    def _sign_to_planet(self, sign: str) -> str:
        """Convert zodiac sign to its ruling planet."""
        sign_map = {
            "Aries": "Mars", "Scorpio": "Mars",
            "Taurus": "Venus", "Libra": "Venus",
            "Gemini": "Mercury", "Virgo": "Mercury",
            "Cancer": "Moon",
            "Leo": "Sun",
            "Sagittarius": "Jupiter", "Pisces": "Jupiter",
            "Capricorn": "Saturn", "Aquarius": "Saturn"
        }
        return sign_map.get(sign, "Moon")
    
    def _are_friendly(self, planet1: str, planet2: str) -> bool:
        """Check if two planets have mutual friendship."""
        friends = {
            "Sun": ["Moon", "Mars", "Jupiter"],
            "Moon": ["Sun", "Mercury"],
            "Mars": ["Sun", "Jupiter", "Moon"],
            "Mercury": ["Sun", "Venus"],
            "Jupiter": ["Sun", "Mars", "Moon"],
            "Venus": ["Mercury", "Saturn"],
            "Saturn": ["Mercury", "Venus"],
        }
        return planet2 in friends.get(planet1, [])
    
    def _get_rag_bonus(self, activity: str, date: datetime) -> int:
        """Get score bonus from RAG knowledge."""
        if not self.rag_context:
            return 0
        
        activity_lower = activity.lower()
        bonus = 0
        
        # Check if activity is mentioned in vault
        for ctx in self.rag_context:
            content = ctx["content"].lower()
            if activity_lower in content:
                if "благоприятн" in content:
                    bonus += 1
                if "мухурта" in ctx["tag"] or "timing" in ctx["tag"]:
                    bonus += 1
        
        return min(bonus, 2)  # Cap at +2
    
    def _search_rag(self, query: str, top_k: int = 3) -> List[Dict[str, str]]:
        """Search vault for relevant Muhurta insights."""
        if not self.rag:
            return []
        
        results = self.rag.search(query, top_k=top_k)
        return [{"content": r["content"], "file": r["file"]} for r in results]
    
    def _generate_recommendations(
        self,
        activity: str,
        day: str,
        planet: str,
        moon: str,
        phase: str
    ) -> List[str]:
        """Generate timing recommendations."""
        recs = [
            f"Day {day} (ruled by {planet}) — {'optimal' if planet == ACTIVITY_PLANETS.get(activity.lower(), '') else 'acceptable'} for {activity}",
            f"Moon in {moon} — {'favorable' if self._are_friendly(self._sign_to_planet(moon), ACTIVITY_PLANETS.get(activity.lower(), 'Jupiter')) else 'neutral'} placement",
            f"Lunar phase: {phase} — suitable for {LUNAR_PHASES.get(phase, {}).get('quality', 'neutral')} activities",
        ]
        return recs
    
    def _generate_warnings(
        self,
        activity: str,
        day: str,
        planet: str,
        moon: str,
        phase: str
    ) -> List[str]:
        """Generate timing warnings."""
        warnings = []
        
        # Check for difficult combinations
        if planet == "Saturn" and activity.lower() in ["marriage", "creative"]:
            warnings.append("Saturn day may bring delays or seriousness")
        
        if phase == "new" and activity.lower() in ["marriage", "celebration"]:
            warnings.append("New Moon is not ideal for celebratory events")
        
        if not warnings:
            warnings.append("No significant warnings for this timing")
        
        return warnings
    
    def _generate_summary(
        self,
        activity: str,
        best: TimingResult,
        all_results: List[TimingResult]
    ) -> str:
        """Generate analysis summary."""
        excellent = sum(1 for r in all_results if r.quality == "Excellent")
        good = sum(1 for r in all_results if r.quality == "Good")
        
        return (
            f"Muhurta analysis for {activity}: "
            f"Best day is {best.day_of_week} ({best.date.strftime('%Y-%m-%d')}) "
            f"with {best.quality} quality (score: {best.score}). "
            f"Found {excellent} excellent and {good} good options in the analyzed period."
        )
    
    def interpret_muhurta(
        self,
        activity: str,
        birth_chart_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        RAG-enhanced Muhurta interpretation.
        
        Uses vault knowledge to provide context-aware advice.
        """
        interpretation_parts = [
            f"## Muhurta Analysis: {activity.title()}",
            "",
        ]
        
        # Add RAG context if available
        if self.rag_context:
            interpretation_parts.append("### Vault Insights:")
            for i, ctx in enumerate(self.rag_context[:3], 1):
                interpretation_parts.append(f"{i}. *{ctx['content'][:150]}...*")
            interpretation_parts.append("")
        
        # Add activity-specific guidance
        planet = ACTIVITY_PLANETS.get(activity.lower(), "Jupiter")
        interpretation_parts.extend([
            f"### Timing Principles for {activity.title()}",
            f"- **Ruling Planet**: {planet}",
            f"- **Best Days**: {', '.join(BEST_DAYS.get(activity.lower(), ['Sunday']))}",
            f"- **RAG Tag**: #мухурта #{video.lower() if 'video' in activity.lower() else activity.lower()}",
            "",
        ])
        
        return "\n".join(interpretation_parts)


if __name__ == "__main__":
    print("=" * 60)
    print("Muhurta Specialist — Electional Astrology Test")
    print("=" * 60)
    
    specialist = MuhurtaSpecialist()
    
    # Test 1: Find best timing for marriage
    print("\n### TEST 1: Marriage Muhurta ###")
    report = specialist.find_best_timing(
        activity="marriage",
        start_date=datetime.now(),
        days_ahead=7
    )
    
    print(f"Activity: {report.activity}")
    print(f"Best day: {report.best_timing.day_of_week} ({report.best_timing.date.strftime('%Y-%m-%d')})")
    print(f"Score: {report.best_timing.score} ({report.best_timing.quality})")
    print(f"Moon sign: {report.best_timing.moon_sign}")
    print(f"Lunar phase: {report.best_timing.lunar_phase}")
    
    print(f"\nRecommendations:")
    for rec in report.best_timing.recommendations:
        print(f"  - {rec}")
    
    print(f"\nWarnings:")
    for warn in report.best_timing.warnings:
        print(f"  - {warn}")
    
    # Test 2: RAG-enhanced interpretation
    print("\n### TEST 2: RAG Interpretation ###")
    interp = specialist.interpret_muhurta("travel")
    print(interp)
    
    # Test 3: Single date analysis
    print("\n### TEST 3: Single Date Analysis ###")
    timing = specialist.analyze_timing(
        activity="wealth",
        date=datetime.now(),
        moon_sign="Sagittarius",
        lunar_phase="waxing"
    )
    print(f"Score: {timing.score} — {timing.quality}")
    print(f"Day: {timing.day_of_week} (ruled by {timing.planetary_ruler})")
