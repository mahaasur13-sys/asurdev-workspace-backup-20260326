"""Western Astrology Module — Aspects, Transits, Financial Astrology"""

from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass

from .vedic import SwissEphemeris, PlanetaryPositions

# Financial indicators
BULLISH_PLANETS = ["sun", "jupiter", "venus"]

FINANCIAL_SIGNS = {
    "Taurus": {"type": "earth", "finance": "BULLISH", "desc": "Stable growth"},
    "Capricorn": {"type": "earth", "finance": "BULLISH", "desc": "Career, ambition"},
    "Virgo": {"type": "earth", "finance": "NEUTRAL", "desc": "Detail, analysis"},
    "Libra": {"type": "air", "finance": "NEUTRAL", "desc": "Partnerships"},
    "Aquarius": {"type": "air", "finance": "VOLATILE", "desc": "Innovation"},
    "Gemini": {"type": "air", "finance": "VOLATILE", "desc": "Communication"},
    "Aries": {"type": "fire", "finance": "BULLISH", "desc": "Action, leadership"},
    "Leo": {"type": "fire", "finance": "BULLISH", "desc": "Confidence"},
    "Sagittarius": {"type": "fire", "finance": "BULLISH", "desc": "Expansion"},
    "Cancer": {"type": "water", "finance": "BULLISH", "desc": "Sentiment"},
    "Scorpio": {"type": "water", "finance": "BEARISH", "desc": "Transformation"},
    "Pisces": {"type": "water", "finance": "BEARISH", "desc": "Intuition"},
}


@dataclass
class Aspect:
    """Aspect between two planets"""
    planet1: str
    planet2: str
    aspect_type: str
    orb: float
    is_exact: bool
    strength: float


class AspectAnalyzer:
    """Analyze planetary aspects"""
    
    PLANET_ORDER = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]
    ASPECT_TYPES = [("conjunction", 0), ("sextile", 60), ("square", 90), ("trine", 120), ("opposition", 180)]
    
    @classmethod
    def calculate_aspects(cls, positions: PlanetaryPositions) -> List[Aspect]:
        """Calculate all aspects between planets"""
        aspects = []
        
        for i, p1 in enumerate(cls.PLANET_ORDER):
            for p2 in cls.PLANET_ORDER[i+1:]:
                pos1 = getattr(positions, p1)
                pos2 = getattr(positions, p2)
                
                angle = abs(pos1 - pos2) % 360
                if angle > 180:
                    angle = 360 - angle
                
                for aspect_name, exact_angle in cls.ASPECT_TYPES:
                    orb = abs(angle - exact_angle)
                    if orb <= 10:
                        strength = max(0, 100 - orb * 5 - (10 if orb > 2 else 0))
                        aspects.append(Aspect(
                            planet1=p1, planet2=p2,
                            aspect_type=aspect_name,
                            orb=round(orb, 2),
                            is_exact=orb <= 2,
                            strength=strength
                        ))
                        break
        
        return sorted(aspects, key=lambda x: x.strength, reverse=True)
    
    @classmethod
    def interpret_aspects(cls, aspects: List[Aspect]) -> Dict:
        """Interpret aspects for financial trading"""
        interpretation = []
        score = 50
        
        for aspect in aspects[:5]:
            p1, p2 = aspect.planet1, aspect.planet2
            
            if aspect.aspect_type == "trine" and (p1 in BULLISH_PLANETS or p2 in BULLISH_PLANETS):
                interpretation.append({"planets": f"{p1}-{p2}", "type": "BULLISH", "meaning": "Harmonious"})
                score += aspect.strength * 0.1
            elif aspect.aspect_type == "square":
                interpretation.append({"planets": f"{p1}-{p2}", "type": "VOLATILE", "meaning": "Tension"})
                score -= aspect.strength * 0.05
            elif aspect.aspect_type == "opposition":
                interpretation.append({"planets": f"{p1}-{p2}", "type": "CONFLICTING", "meaning": "Indecision"})
        
        return {
            "top_aspects": [
                {"planets": f"{a.planet1}-{a.planet2}", "type": a.aspect_type, 
                 "orb": a.orb, "strength": round(a.strength, 1)}
                for a in aspects[:5]
            ],
            "interpretation": interpretation,
            "aspect_score": round(score, 1),
            "signal": "BULLISH" if score >= 65 else "BEARISH" if score <= 35 else "NEUTRAL"
        }


class WesternAstrologer:
    """Western Astrology Agent"""
    
    def __init__(self, lat: float = 40.7128, lon: float = -74.0060):
        self.lat = lat
        self.lon = lon
    
    def analyze(self, dt: datetime = None) -> Dict:
        """Full Western analysis"""
        dt = dt or datetime.now()
        positions = SwissEphemeris.get_planetary_positions(dt, ayanamsa_correction=0)
        
        phase, illumination = SwissEphemeris.moon_phase(SwissEphemeris.julian_day(dt))
        aspects = AspectAnalyzer.calculate_aspects(positions)
        aspect_analysis = AspectAnalyzer.interpret_aspects(aspects)
        
        financial = self._get_financial_signal(positions, aspect_analysis, illumination)
        
        return {
            "timestamp": dt.isoformat(),
            "western": {
                "moon_phase": phase,
                "illumination": round(illumination, 1),
                "dominant_sign": self._get_dominant_element(positions),
            },
            "aspects": aspect_analysis,
            "signs": {
                "moon": positions.get_sign("moon"),
                "sun": positions.get_sign("sun"),
                "venus": positions.get_sign("venus"),
                "jupiter": positions.get_sign("jupiter"),
            },
            "financial": financial,
            "planetary_positions": {
                p: {"sign": positions.get_sign(p), "degree": round(positions.get_degree(p), 1)}
                for p in ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]
            },
        }
    
    def _get_dominant_element(self, pos: PlanetaryPositions) -> str:
        elements = {"fire": 0, "earth": 0, "air": 0, "water": 0}
        fire = ["Aries", "Leo", "Sagittarius"]
        earth = ["Taurus", "Virgo", "Capricorn"]
        air = ["Gemini", "Libra", "Aquarius"]
        
        for planet in ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]:
            sign = pos.get_sign(planet)
            if sign in fire: elements["fire"] += 1
            elif sign in earth: elements["earth"] += 1
            elif sign in air: elements["air"] += 1
            else: elements["water"] += 1
        
        return max(elements, key=elements.get)
    
    def _get_financial_signal(self, pos: PlanetaryPositions, aspects: Dict, illumination: float) -> Dict:
        score = 50
        
        moon_sign = pos.get_sign("moon")
        fin_sign = FINANCIAL_SIGNS.get(moon_sign, {}).get("finance", "NEUTRAL")
        if fin_sign == "BULLISH": score += 15
        elif fin_sign == "BEARISH": score -= 15
        
        score += (aspects["aspect_score"] - 50) * 0.3
        if illumination < 20: score += 10
        elif illumination > 80: score -= 5
        
        if pos.get_sign("jupiter") in ["Taurus", "Cancer", "Libra", "Capricorn"]: score += 10
        if pos.get_sign("venus") in ["Taurus", "Libra", "Capricorn"]: score += 10
        
        signal = "BULLISH" if score >= 65 else "BEARISH" if score <= 35 else "NEUTRAL"
        
        return {"signal": signal, "score": min(100, max(0, round(score, 1))), "confidence": min(100, abs(score - 50) * 1.5 + 20)}
