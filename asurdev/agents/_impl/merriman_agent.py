"""
Merriman Agent - 7-Planet Cycle Analysis (R. Merriman method)
Based on "The Merrill Model" - planetary cycles for market timing

Reference: R. Merriman's works on financial astrology
"""
import math
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from .base_agent import BaseAgent, AgentResponse


@dataclass
class PlanetPosition:
    name: str
    longitude: float  # 0-360 degrees
    speed: float  # degrees per day
    zodiac: str
    
    @property
    def zodiac_name(self) -> str:
        signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                 "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        idx = int(self.longitude // 30) % 12
        return signs[idx]
    
    @property
    def degree(self) -> float:
        return self.longitude % 30


@dataclass 
class CycleSignal:
    planet: str
    cycle_position: str  # "early", "mid", "late"
    aspect_to_prior: Optional[str]  # "conjunction", "opposition", etc.
    strength: int  # 0-100
    description: str


# Simplified planetary data (in production, use ephemeris library like swephpy)
PLANET_DATA = {
    "Mercury":  {"period_days": 87.97,  "speed": 4.15,  "glyph": "☿"},
    "Venus":    {"period_days": 224.7,  "speed": 1.60,  "glyph": "♀"},
    "Mars":     {"period_days": 686.98, "speed": 0.52,  "glyph": "♂"},
    "Jupiter":  {"period_days": 4332.6, "speed": 0.083, "glyph": "♃"},
    "Saturn":   {"period_days": 10759.2, "speed": 0.034, "glyph": "♄"},
    "Uranus":   {"period_days": 30688.5, "speed": 0.012, "glyph": "♅"},
    "Neptune":  {"period_days": 60182.0, "speed": 0.006, "glyph": "♆"},
}

# Cycle phases and their market interpretation
CYCLE_PHASES = {
    (0, 45):    ("BULLISH", 60, "Early cycle - accumulation phase"),
    (45, 90):   ("BULLISH", 70, "First quarter - momentum building"),
    (90, 135):  ("BULLISH", 65, "Mid-cycle peak - consolidation likely"),
    (135, 180): ("BEARISH", 55, "Late cycle - distribution begins"),
    (180, 225): ("BEARISH", 65, "Decline phase"),
    (225, 270): ("BEARISH", 70, "Second quarter - selling pressure"),
    (270, 315): ("NEUTRAL", 50, "Bottom formation"),
    (315, 360): ("BULLISH", 60, "Approaching new cycle"),
}


class MerrimanAgent(BaseAgent):
    """
    Implements R. Merriman's 7-planet cycle model for market timing.
    
    Key principles:
    1. Each planet has a cycle period (Mercury fastest, Neptune slowest)
    2. Cycle position (0-360°) indicates market phase
    3. Planetary aspects (conjunctions, oppositions) signal major turns
    4. Combined planetary positions give overall market direction
    """
    
    def __init__(self, lat: float = 28.6139, lon: float = 77.2090, **kwargs):
        super().__init__(
            name="MerrimanAgent",
            system_prompt="Финансовая астрология по методу Мерримана. Анализируй планетарные циклы для тайминга рынка.",
            temperature=0.3,
            **kwargs
        )
        self.lat = lat
        self.lon = lon
        
    async def analyze(self, context: Dict[str, Any]) -> AgentResponse:
        """
        Main analysis - returns cycle-based signal
        """
        now = datetime.now()
        
        # Get all planet positions
        positions = self._calculate_planet_positions(now)
        
        # Calculate cycle signals
        signals = self._analyze_cycles(positions, now)
        
        # Get primary cycle (Mercury as fastest - controls short-term)
        primary = positions["Mercury"]
        primary_signal, primary_conf, primary_desc = self._get_cycle_phase(primary.longitude)
        
        # Get medium-term (Venus)
        venus = positions["Venus"]
        venus_signal, venus_conf, venus_desc = self._get_cycle_phase(venus.longitude)
        
        # Get long-term (Jupiter)
        jupiter = positions["Jupiter"]
        jupiter_signal, jupiter_conf, jupiter_desc = self._get_cycle_phase(jupiter.longitude)
        
        # Composite signal
        composite = self._composite_signal([
            (primary_signal, primary_conf, 0.4),    # 40% short-term
            (venus_signal, venus_conf, 0.3),          # 30% medium-term
            (jupiter_signal, jupiter_conf, 0.3),      # 30% long-term
        ])
        
        # Check for major aspects (conjunctions, oppositions)
        major_aspects = self._find_major_aspects(positions)
        
        # Build summary
        glyphs = {p: PLANET_DATA[p]["glyph"] for p in PLANET_DATA}
        summary_parts = [
            f"☿{glyphs['Mercury']} {primary_signal}({primary_conf}%)",
            f"♀{glyphs['Venus']} {venus_signal}({venus_conf}%)",
            f"♃{glyphs['Jupiter']} {jupiter_signal}({jupiter_conf}%)",
        ]
        if major_aspects:
            summary_parts.append(f"⚡ {', '.join(major_aspects)}")
        
        return AgentResponse(
            agent_name="MerrimanAgent",
            signal=composite,
            confidence=self._calculate_confidence(positions),
            summary=" | ".join(summary_parts),
            details={
                "cycles": {
                    "mercury": {"position": primary.longitude, "signal": primary_signal, "description": primary_desc},
                    "venus": {"position": venus.longitude, "signal": venus_signal, "description": venus_desc},
                    "jupiter": {"position": jupiter.longitude, "signal": jupiter_signal, "description": jupiter_desc},
                },
                "planets": {p: {
                    "longitude": pos.longitude,
                    "zodiac": pos.zodiac_name,
                    "degree": round(pos.degree, 2),
                    "glyph": PLANET_DATA[p]["glyph"]
                } for p, pos in positions.items()},
                "major_aspects": major_aspects,
                "method": "R. Merriman 7-Planet Cycle Model"
            }
        )
    
    def _calculate_planet_positions(self, dt: datetime) -> Dict[str, PlanetPosition]:
        """
        Calculate approximate planetary longitudes.
        In production, use Swiss Ephemeris (swephpy) for accuracy.
        This is a simplified calculation for demonstration.
        """
        # Days since J2000.0 (Jan 1, 2000, 12:00 TT)
        j2000 = datetime(2000, 1, 1, 12, 0, 0)
        days_since_j2000 = (dt - j2000).total_seconds() / 86400.0
        
        positions = {}
        
        # Simplified orbital elements (more accurate in production)
        # Mean longitude at J2000 and daily motion
        mean_longitudes = {
            "Mercury": 252.87,
            "Venus": 181.97,
            "Mars": 355.43,
            "Jupiter": 34.40,
            "Saturn": 50.08,
            "Uranus": 314.20,
            "Neptune": 304.22,
        }
        
        for planet, data in PLANET_DATA.items():
            # Mean longitude
            mean_long = mean_longitudes[planet]
            # Add daily motion
            current_long = (mean_long + data["speed"] * days_since_j2000) % 360
            
            positions[planet] = PlanetPosition(
                name=planet,
                longitude=current_long,
                speed=data["speed"],
                zodiac=""
            )
        
        return positions
    
    def _get_cycle_phase(self, longitude: float) -> Tuple[str, int, str]:
        """Get signal based on cycle position (0-360°)"""
        for (start, end), (signal, conf, desc) in CYCLE_PHASES.items():
            if start <= longitude < end:
                return signal, conf, desc
        return "NEUTRAL", 50, "Unknown phase"
    
    def _analyze_cycles(self, positions: Dict[str, PlanetPosition], dt: datetime) -> List[CycleSignal]:
        """Analyze all planetary cycles"""
        signals = []
        
        # Primary cycles to analyze
        for planet in ["Mercury", "Venus", "Mars", "Jupiter", "Saturn"]:
            pos = positions[planet]
            phase = (pos.longitude % 360) / 360 * 100  # 0-100%
            
            if phase < 25:
                cycle_pos = "early"
            elif phase < 50:
                cycle_pos = "first_quarter"
            elif phase < 75:
                cycle_pos = "late"
            else:
                cycle_pos = "second_quarter"
            
            signal, conf, desc = self._get_cycle_phase(pos.longitude)
            
            signals.append(CycleSignal(
                planet=planet,
                cycle_position=cycle_pos,
                aspect_to_prior=None,
                strength=conf,
                description=desc
            ))
        
        return signals
    
    def _composite_signal(self, weighted_signals: List[Tuple[str, int, float]]) -> str:
        """Calculate weighted composite signal"""
        scores = {"BULLISH": 0.0, "BEARISH": 0.0, "NEUTRAL": 0.0}
        
        for signal, confidence, weight in weighted_signals:
            scores[signal] += confidence * weight
        
        if scores["BULLISH"] > scores["BEARISH"]:
            return "BULLISH"
        elif scores["BEARISH"] > scores["BULLISH"]:
            return "BEARISH"
        return "NEUTRAL"
    
    def _calculate_confidence(self, positions: Dict[str, PlanetPosition]) -> int:
        """
        Calculate confidence based on planetary alignments.
        More planets agreeing = higher confidence.
        """
        signals = []
        for planet in ["Mercury", "Venus", "Mars", "Jupiter", "Saturn"]:
            signal, conf, _ = self._get_cycle_phase(positions[planet].longitude)
            signals.append((signal, conf))
        
        # Check agreement
        bullish_count = sum(1 for s, _ in signals if s == "BULLISH")
        bearish_count = sum(1 for s, _ in signals if s == "BEARISH")
        
        base_conf = 50
        if bullish_count >= 4:
            return min(85, base_conf + bullish_count * 7)
        elif bearish_count >= 4:
            return min(85, base_conf + bearish_count * 7)
        elif bullish_count == 3:
            return 65
        elif bearish_count == 3:
            return 65
        
        return 55  # Mixed signals
    
    def _find_major_aspects(self, positions: Dict[str, PlanetPosition]) -> List[str]:
        """
        Find major aspects (conjunctions, oppositions, squares).
        These signal potential market turning points.
        """
        aspects = []
        
        # Check Mercury-Venus relationship (fast moving pair)
        merc_long = positions["Mercury"].longitude
        venus_long = positions["Venus"].longitude
        
        diff = abs(merc_long - venus_long) % 360
        if diff < 15 or diff > 345:
            aspects.append("Mercury-Venus Conjunction")
        elif 165 < diff < 195:
            aspects.append("Mercury-Venus Opposition")
        
        # Check Jupiter-Saturn (slow moving pair - defines multi-year cycles)
        jup_long = positions["Jupiter"].longitude
        sat_long = positions["Saturn"].longitude
        
        diff = abs(jup_long - sat_long) % 360
        if diff < 15 or diff > 345:
            aspects.append("Jupiter-Saturn Conjunction (Major Cycle)")
        elif 165 < diff < 195:
            aspects.append("Jupiter-Saturn Opposition")
        elif 85 < diff < 95:
            aspects.append("Jupiter-Saturn Square")
        
        return aspects


class MerrimanCycleCalculator:
    """
    Utility class for precise Merriman cycle calculations.
    Use this for backtesting and historical analysis.
    """
    
    @staticmethod
    def get_cycle_start(planet: str, reference_date: datetime) -> datetime:
        """
        Find the start of the current cycle for a planet.
        """
        if planet not in PLANET_DATA:
            raise ValueError(f"Unknown planet: {planet}")
        
        period = PLANET_DATA[planet]["period_days"]
        j2000 = datetime(2000, 1, 1, 12, 0, 0)
        days_since = (reference_date - j2000).total_seconds() / 86400
        
        # Find position in cycle
        position = days_since % period
        cycle_number = int(days_since // period)
        
        # Start of current cycle
        cycle_start = j2000 + timedelta(days=cycle_number * period)
        
        return cycle_start
    
    @staticmethod
    def get_next_aspect(planet1: str, planet2: str, from_date: datetime) -> Tuple[datetime, str]:
        """
        Calculate next major aspect between two planets.
        Returns (datetime, aspect_type)
        """
        # Simplified - in production use full ephemeris
        speed1 = PLANET_DATA[planet1]["speed"]
        speed2 = PLANET_DATA[planet2]["speed"]
        
        relative_speed = abs(speed1 - speed2)
        
        # Time to next conjunction
        days_to_conjunction = 180 / relative_speed
        
        return from_date + timedelta(days=days_to_conjunction), "conjunction"
    
    @staticmethod
    def cornmoon_analysis(from_date: datetime, to_date: datetime) -> List[Dict]:
        """
        Corned Moon analysis - Merriman's technique for short-term timing.
        Analyzes Moon's aspects to planets during void-of-course periods.
        """
        results = []
        
        # Simplified: generate daily samples
        current = from_date
        while current < to_date:
            # In production, calculate actual void-of-course periods
            results.append({
                "date": current.isoformat(),
                "void_of_course": False,  # Calculate from actual ephemeris
                "moon_phase": "Waxing" if (current.day % 15) < 8 else "Waning",
                "aspects": []  # Calculate from ephemeris
            })
            current += timedelta(days=1)
        
        return results
