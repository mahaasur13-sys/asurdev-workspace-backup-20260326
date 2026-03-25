"""
Classical Astrology Core — Essential & Accidental Dignities
Based on William Lilly "Christian Astrology" & John Froli "Horary Textbook"
"""

from enum import Enum
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


# ============ ESSENTIAL DIGNITIES ============

# Exaltation (Ayanavala in Vedic)
EXALTATION = {
    "Sun": {"sign": "Aries", "degree": 19},
    "Moon": {"sign": "Taurus", "degree": 3},
    "Mercury": {"sign": "Virgo", "degree": 15},
    "Venus": {"sign": "Pisces", "degree": 27},
    "Mars": {"sign": "Capricorn", "degree": 28},
    "Jupiter": {"sign": "Cancer", "degree": 15},
    "Saturn": {"sign": "Libra", "degree": 21},
}

# Fall (opposite of Exaltation)
FALL = {
    "Sun": "Libra", "Moon": "Scorpio", "Mercury": "Pisces",
    "Venus": "Virgo", "Mars": "Cancer", "Jupiter": "Capricorn", "Saturn": "Aries"
}

# Triplicity Rulers (Day/Night)
TRIPLICITY_DAY = {
    "Fire": {"Aries": "Sun", "Leo": "Sun", "Sagittarius": "Sun"},
    "Earth": {"Taurus": "Venus", "Virgo": "Venus", "Capricorn": "Venus"},
    "Air": {"Gemini": "Jupiter", "Libra": "Jupiter", "Aquarius": "Jupiter"},
    "Water": {"Cancer": "Moon", "Scorpio": "Mars", "Pisces": "Venus"},
}

TRIPLICITY_NIGHT = {
    "Fire": {"Aries": "Jupiter", "Leo": "Jupiter", "Sagittarius": "Jupiter"},
    "Earth": {"Taurus": "Moon", "Virgo": "Moon", "Capricorn": "Moon"},
    "Air": {"Gemini": "Saturn", "Libra": "Saturn", "Aquarius": "Saturn"},
    "Water": {"Cancer": "Venus", "Scorpio": "Moon", "Pisces": "Mars"},
}

# Terms (Bounds) — Ancient Egyptian system
TERMS = {
    "Aries": [("Jupiter", 6), ("Venus", 6), ("Mercury", 6), ("Mars", 6), ("Saturn", 6)],
    "Taurus": [("Venus", 8), ("Mercury", 6), ("Jupiter", 8), ("Saturn", 4), ("Mars", 4)],
    "Gemini": [("Mercury", 7), ("Jupiter", 6), ("Venus", 6), ("Mars", 6), ("Saturn", 5)],
    "Cancer": [("Mars", 7), ("Venus", 6), ("Mercury", 6), ("Jupiter", 6), ("Saturn", 5)],
    "Leo": [("Sun", 6), ("Jupiter", 5), ("Mercury", 6), ("Venus", 6), ("Saturn", 7)],
    "Virgo": [("Mercury", 7), ("Venus", 6), ("Jupiter", 5), ("Saturn", 6), ("Mars", 6)],
    "Libra": [("Saturn", 6), ("Mercury", 6), ("Venus", 8), ("Jupiter", 6), ("Mars", 4)],
    "Scorpio": [("Mars", 7), ("Jupiter", 4), ("Venus", 8), ("Mercury", 6), ("Saturn", 5)],
    "Sagittarius": [("Jupiter", 6), ("Venus", 5), ("Mercury", 6), ("Mars", 7), ("Saturn", 6)],
    "Capricorn": [("Saturn", 7), ("Mercury", 6), ("Venus", 6), ("Mars", 5), ("Jupiter", 6)],
    "Aquarius": [("Saturn", 6), ("Mercury", 6), ("Venus", 6), ("Jupiter", 6), ("Mars", 6)],
    "Pisces": [("Venus", 12), ("Jupiter", 4), ("Mercury", 4), ("Mars", 4), ("Saturn", 6)],
}

# Faces (Decans) — 10° each
DECANS = {
    0: "Mars", 1: "Sun", 2: "Venus",    # Aries
    3: "Mercury", 4: "Moon", 5: "Saturn",  # Taurus
    6: "Jupiter", 7: "Mars", 8: "Sun",     # Gemini
    9: "Venus", 10: "Mercury", 11: "Moon", # Cancer
    12: "Saturn", 13: "Jupiter", 14: "Mars", # Leo
    15: "Sun", 16: "Venus", 17: "Mercury", # Virgo
    18: "Moon", 19: "Saturn", 20: "Jupiter", # Libra
    21: "Mars", 22: "Sun", 23: "Venus",    # Scorpio
    24: "Mercury", 25: "Moon", 26: "Saturn", # Sagittarius
    27: "Jupiter", 28: "Mars", 29: "Sun",  # Capricorn
    30: "Venus", 31: "Mercury", 32: "Moon", # Aquarius
    33: "Saturn", 34: "Jupiter", 35: "Mars", # Pisces
}

# ============ ACCIDENTAL DIGNITIES ============

@dataclass
class AccidentalDignity:
    type: str
    score: int
    description: str


# Joy — Planet in its joy sign (traditional)
JOY = {
    "Sun": "Aries",      # East
    "Moon": "Taurus",    # First place after Sun
    "Saturn": "Libra",   # West
    "Jupiter": "Cancer", # House of the Moon's Joy
    "Mars": "Scorpio",   # Fall of Moon
    "Venus": "Pisces",   # Exaltation of Moon
    "Mercury": "Virgo",  # Mercury's joy
}

# Planets dignity scores
DIGNITY_SCORES = {
    "exaltation": 5,
    "trine": 4,
    "triplicity_day": 3,
    "triplicity_night": 3,
    "term": 2,
    "face": 1,
    "detriment": -5,
    "fall": -4,
}


class EssentialDignities:
    """Calculate Essential Dignities based on Lilly & Froli"""
    
    @classmethod
    def get_dignity_score(cls, planet: str, sign: str, is_day: bool = True) -> int:
        """Calculate total dignity score for a planet in a sign"""
        score = 0
        details = []
        
        # Exaltation
        if sign == EXALTATION.get(planet, {}).get("sign"):
            score += DIGNITY_SCORES["exaltation"]
            details.append("Exaltation")
        
        # Fall
        if sign == FALL.get(planet):
            score += DIGNITY_SCORES["fall"]
            details.append("Fall")
        
        # Triplicity
        element = cls._get_element(sign)
        if is_day and planet in TRIPLICITY_DAY.get(element, {}).values():
            score += DIGNITY_SCORES["triplicity_day"]
            details.append("Triplicity (Day)")
        elif not is_day and planet in TRIPLICITY_NIGHT.get(element, {}).values():
            score += DIGNITY_SCORES["triplicity_night"]
            details.append("Triplicity (Night)")
        
        # Term
        for term_planet, end_degree in TERMS.get(sign, []):
            if term_planet == planet:
                score += DIGNITY_SCORES["term"]
                details.append("Term")
                break
        
        # Face (Decan)
        sign_num = cls._sign_to_number(sign)
        # Simplified - just check if planet matches decan ruler
        decan_index = sign_num * 3  # 3 decans per sign
        
        return score, details
    
    @staticmethod
    def _get_element(sign: str) -> str:
        """Get element of a sign"""
        elements = {
            "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
            "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
            "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
            "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water",
        }
        return elements.get(sign, "Earth")
    
    @staticmethod
    def _sign_to_number(sign: str) -> int:
        """Convert sign to number (0-11)"""
        signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                 "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        return signs.index(sign) if sign in signs else 0


class AccidentalDignities:
    """Calculate Accidental Dignities (Lilly)"""
    
    @classmethod
    def analyze(cls, planet: str, position: Dict, moon_phase: str = "") -> List[AccidentalDignity]:
        """Analyze accidental dignities"""
        dignities = []
        
        # Joy
        joy_sign = JOY.get(planet)
        if joy_sign == position.get("sign"):
            dignities.append(AccidentalDignity(
                type="Joy",
                score=5,
                description=f"Planet in its joy sign ({joy_sign})"
            ))
        
        # Stationary ( Cazimi would be checked here)
        if position.get("speed", 0) < 1:
            dignities.append(AccidentalDignity(
                type="Stationary",
                score=4,
                description="Planet is stationary — powerful"
            ))
        
        # Fast moving
        if position.get("speed", 0) > 15:
            dignities.append(AccidentalDignity(
                type="Fast",
                score=2,
                description="Planet moving quickly"
            ))
        
        # Under Sun's beams (combust)
        if position.get("degree") and 8 <= position.get("degree", 30) <= 30:
            # Simplified — actual combustion check needs exact degrees
            dignities.append(AccidentalDignity(
                type="Combust",
                score=-4,
                description="Within 8°30' of Sun — combust, weak"
            ))
        
        # Oriental/Eastern (rising before Sun)
        if position.get("is_orient"):  # Orientalis
            dignities.append(AccidentalDignity(
                type="Oriental",
                score=2,
                description="Planet is oriental (rising before Sun)"
            ))
        
        # Occidental/Western (setting after Sun)
        if position.get("is_occident"):
            dignities.append(AccidentalDignity(
                type="Occidental",
                score=-2,
                description="Planet is occidental (setting after Sun)"
            ))
        
        return dignities


class Aspects:
    """Calculate Aspects (Lilly Chapter 9)"""
    
    ASPECTS = {
        "conjunction": {"angle": 0, "orb": 8, "nature": "mix"},
        "sextile": {"angle": 60, "orb": 6, "nature": "good"},
        "square": {"angle": 90, "orb": 8, "nature": "bad"},
        "trine": {"angle": 120, "orb": 8, "nature": "good"},
        "opposition": {"angle": 180, "orb": 10, "nature": "bad"},
    }
    
    @classmethod
    def calculate_aspects(cls, planet1_pos: int, planet2_pos: int) -> List[Dict]:
        """Calculate aspects between two planets (positions in degrees)"""
        aspects_found = []
        diff = abs(planet1_pos - planet2_pos)
        if diff > 180:
            diff = 360 - diff
        
        for aspect_name, params in cls.ASPECTS.items():
            if abs(diff - params["angle"]) <= params["orb"]:
                aspects_found.append({
                    "aspect": aspect_name,
                    "angle": params["angle"],
                    "nature": params["nature"],
                    "orb": abs(diff - params["angle"]),
                })
        
        return aspects_found


class Reception:
    """Mutual Reception (Lilly Chapter 8)"""
    
    @classmethod
    def check_mutual_reception(cls, p1: str, sign1: str, p2: str, sign2: str) -> Dict:
        """Check for mutual reception between two planets"""
        # Planet in the sign of another planet = reception by sign
        # Check various types of reception
        
        results = {
            "has_reception": False,
            "type": None,
            "strength": 0,
            "description": ""
        }
        
        # Reception by sign (mutual)
        if EssentialDignities._sign_to_number(sign1) % 6 == EssentialDignities._sign_to_number(sign2) % 6:
            # Simplified check
            pass
        
        return results


class ArabicParts:
    """Arabic Parts — especially Part of Fortune (Froli Chapter 12)"""
    
    @classmethod
    def part_of_fortune(cls, sun_deg: int, moon_deg: int, asc_deg: int) -> int:
        """
        Calculate Part of Fortune (Lots of Fortune)
        Formula: ASC + Moon - Sun (for daytime)
        For night: ASC + Sun - Moon
        """
        day_part = (asc_deg + Moon_deg - sun_deg) % 360
        return day_part
    
    @classmethod
    def part_of_money(cls, sun_deg: int, moon_deg: int, asc_deg: int) -> int:
        """Part of Money/Wealth"""
        return (asc_deg + 2 - sun_deg + Moon_deg) % 360
    
    @classmethod
    def part_of_trade(cls, sun_deg: int, moon_deg: int, asc_deg: int) -> int:
        """Part of Trade/Merchandise"""
        return (asc_deg + Moon_deg - 2 * sun_deg) % 360
