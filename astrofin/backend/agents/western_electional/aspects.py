"""
Aspect Calculator — Western Astrology.
Calculates aspects between planets and their orbs.
"""
from enum import Enum
from typing import Dict, List, Tuple, Optional
import math


class AspectType(Enum):
    CONJUNCTION = "Conjunction"      # Соединение (0°)
    SEXTILE = "Sextile"              # Секстиль (60°)
    SQUARE = "Square"                # Квадрат (90°)
    TRINE = "Trine"                 # Трин (120°)
    OPPOSITION = "Opposition"       # Opposition (180°)
    SEMI_SEXTILE = "Semi-Sextile"  # Полусекстиль (30°)
    SEMI_SQUARE = "Semi-Square"    # Полуквадрат (45°)
    SESQUIQUADRATE = "Sesquiquadrate"  # Квинкондрат (135°)
    QUINTILE = "Quintile"          # Квинтиль (72°)
    BIQUINTILE = "Bi-Quintile"     # Биквинтиль (144°)


# Aspect orbs (in degrees) — how close to exact the aspect must be
ASPECT_ORBS = {
    AspectType.CONJUNCTION: 10.0,
    AspectType.OPPOSITION: 10.0,
    AspectType.TRINE: 8.0,
    AspectType.SQUARE: 8.0,
    AspectType.SEXTILE: 6.0,
    AspectType.SEMI_SEXTILE: 3.0,
    AspectType.SEMI_SQUARE: 2.0,
    AspectType.SESQUIQUADRATE: 2.0,
    AspectType.QUINTILE: 2.0,
    AspectType.BIQUINTILE: 2.0,
}

# Major aspects for electional astrology
MAJOR_ASPECTS = {
    AspectType.CONJUNCTION: {"nature": "neutral", "strength": 5},
    AspectType.OPPOSITION: {"nature": "challenging", "strength": 5},
    AspectType.TRINE: {"nature": "harmonious", "strength": 5},
    AspectType.SQUARE: {"nature": "challenging", "strength": 4},
    AspectType.SEXTILE: {"nature": "harmonious", "strength": 3},
}

# Sign qualities
SIGN_QUALITIES = {
    "Cardinal": ["Aries", "Cancer", "Libra", "Capricorn"],
    "Fixed": ["Leo", "Scorpio", "Aquarius", "Taurus"],
    "Mutable": ["Gemini", "Virgo", "Sagittarius", "Pisces"],
}


class AspectCalculator:
    """
    Calculates aspects between planetary positions.
    
    Usage:
        calc = AspectCalculator()
        aspects = calc.calculate_aspects(planet_positions)
    """
    
    @staticmethod
    def normalize_longitude(longitude: float) -> float:
        """Normalize longitude to 0-360 range."""
        return longitude % 360
    
    @staticmethod
    def get_angle(pos1: float, pos2: float) -> float:
        """Get angular distance between two positions."""
        diff = abs(pos1 - pos2) % 360
        if diff > 180:
            diff = 360 - diff
        return diff
    
    @staticmethod
    def is_aspect(angle: float, aspect_type: AspectType, planet1: str, planet2: str) -> bool:
        """Check if angle matches aspect within orb."""
        target_angle = {
            AspectType.CONJUNCTION: 0,
            AspectType.OPPOSITION: 180,
            AspectType.TRINE: 120,
            AspectType.SQUARE: 90,
            AspectType.SEXTILE: 60,
            AspectType.SEMI_SEXTILE: 30,
            AspectType.SEMI_SQUARE: 45,
            AspectType.SESQUIQUADRATE: 135,
            AspectType.QUINTILE: 72,
            AspectType.BIQUINTILE: 144,
        }[aspect_type]
        
        orb = ASPECT_ORBS[aspect_type]
        diff = abs(angle - target_angle)
        if diff > 180:
            diff = 360 - diff
        
        return diff <= orb
    
    @classmethod
    def calculate_aspects(
        cls, 
        positions: Dict[str, float],
        include_minor: bool = False
    ) -> List[Dict]:
        """
        Calculate all aspects between planets.
        
        Args:
            positions: Dict of {planet_name: longitude}
            include_minor: Include semi-sextile, quintiles, etc.
        
        Returns:
            List of aspect dicts with details
        """
        aspects = []
        planets = list(positions.keys())
        
        for i, p1 in enumerate(planets):
            for p2 in planets[i+1:]:
                angle = cls.get_angle(positions[p1], positions[p2])
                
                for aspect_type, data in MAJOR_ASPECTS.items():
                    if cls.is_aspect(angle, aspect_type, p1, p2):
                        aspects.append({
                            "planet1": p1,
                            "planet2": p2,
                            "aspect": aspect_type.value,
                            "angle": round(angle, 2),
                            "nature": data["nature"],
                            "strength": data["strength"],
                            "applying": True,  # Simplified
                        })
                
                if include_minor:
                    for minor_type in [AspectType.SEMI_SEXTILE, AspectType.QUINTILE]:
                        if cls.is_aspect(angle, minor_type, p1, p2):
                            aspects.append({
                                "planet1": p1,
                                "planet2": p2,
                                "aspect": minor_type.value,
                                "angle": round(angle, 2),
                                "nature": "minor",
                                "strength": 1,
                                "applying": True,
                            })
        
        return aspects
    
    @staticmethod
    def get_aspect_nature_score(aspects: List[Dict]) -> Tuple[int, str]:
        """
        Calculate overall nature score from aspects.
        
        Returns: (score, description)
        """
        if not aspects:
            return 0, "No aspects — difficult to judge"
        
        harmonious = sum(1 for a in aspects if a["nature"] == "harmonious")
        challenging = sum(1 for a in aspects if a["nature"] == "challenging")
        neutral = sum(1 for a in aspects if a["nature"] == "neutral")
        
        score = harmonious - challenging + neutral * 0.5
        
        if score >= 3:
            return score, "Very harmonious aspects — favorable"
        elif score >= 1:
            return score, "Mostly harmonious — generally favorable"
        elif score >= -1:
            return score, "Mixed aspects — balanced"
        elif score >= -3:
            return score, "Mostly challenging — caution advised"
        else:
            return score, "Very challenging aspects — unfavorable"
    
    @staticmethod
    def get_mutual_reception(planet1: str, sign1: str, planet2: str, sign2: str) -> bool:
        """Check for mutual reception between two planets."""
        from .dignities import RULERSHIP
        
        # Mutual reception by sign
        if RULERSHIP.get(sign1) == planet2 and RULERSHIP.get(sign2) == planet1:
            return True
        
        # Could add other types: by exaltation, triplicity, term, decan
        return False
