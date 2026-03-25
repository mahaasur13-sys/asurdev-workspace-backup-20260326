"""
Essential Dignities — Western Astrology (William Lilly).
Calculates essential dignities for planetary strength assessment.
"""
from enum import Enum
from typing import Dict, List, Tuple


class DignityLevel(Enum):
    RULERSHIP = 5    # Домохозяин (exalted)
    EXALTATION = 4   # В экзальтации
    TRIPLICITY = 3   # Триплицитет
    TERM = 2         # Терм
    DECAN = 1        # Декана
    DETRIMENT = -5   # В изгнании
    FALL = -4        # В падении


# Rulership — традиционные домохозяева (до Урана)
RULERSHIP = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}

# Exaltation
EXALTATION = {
    "Sun": "Aries",
    "Moon": "Taurus",
    "Mercury": "Virgo",
    "Venus": "Pisces",
    "Mars": "Capricorn",
    "Jupiter": "Cancer",
    "Saturn": "Libra",
}

# Detriment (противоположность домохозяину)
DETRIMENT = {v: k for k, v in RULERSHIP.items()}

# Fall (противоположность экзальтации)
FALL = {v: k for k, v in EXALTATION.items()}

# Triplicities (элементы)
FIRE_SIGNS = ["Aries", "Leo", "Sagittarius"]
EARTH_SIGNS = ["Taurus", "Virgo", "Capricorn"]
AIR_SIGNS = ["Gemini", "Libra", "Aquarius"]
WATER_SIGNS = ["Cancer", "Scorpio", "Pisces"]

TRIPLICITY_DAY = {
    "Aries": "Sun", "Leo": "Sun", "Sagittarius": "Sun",
    "Taurus": "Venus", "Virgo": "Moon", "Capricorn": "Moon",
    "Gemini": "Saturn", "Libra": "Saturn", "Aquarius": "Saturn",
    "Cancer": "Mars", "Scorpio": "Mars", "Pisces": "Venus",
}

TRIPLICITY_NIGHT = {
    "Aries": "Jupiter", "Leo": "Jupiter", "Sagittarius": "Jupiter",
    "Taurus": "Moon", "Virgo": "Venus", "Capricorn": "Venus",
    "Gemini": "Saturn", "Libra": "Saturn", "Aquarius": "Saturn",
    "Cancer": "Mars", "Scorpio": "Mars", "Pisces": "Moon",
}

# Terms (границы) —埃及分数系统
TERMS_EGYPTIAN = {
    "Aries": [("Jupiter", 6), ("Venus", 6), ("Mercury", 6), ("Mars", 6), ("Saturn", 6)],
    "Taurus": [("Venus", 8), ("Mercury", 6), ("Jupiter", 5), ("Saturn", 6), ("Mars", 5)],
    "Gemini": [("Mercury", 7), ("Jupiter", 5), ("Venus", 5), ("Mars", 6), ("Saturn", 7)],
    "Cancer": [("Moon", 7), ("Mars", 5), ("Jupiter", 5), ("Venus", 6), ("Saturn", 7)],
    "Leo": [("Sun", 6), ("Jupiter", 5), ("Mercury", 5), ("Venus", 6), ("Mars", 8)],
    "Virgo": [("Mercury", 7), ("Venus", 6), ("Jupiter", 5), ("Mars", 5), ("Saturn", 7)],
    "Libra": [("Venus", 7), ("Mercury", 6), ("Saturn", 5), ("Jupiter", 6), ("Mars", 6)],
    "Scorpio": [("Mars", 7), ("Venus", 4), ("Jupiter", 5), ("Mercury", 5), ("Saturn", 9)],
    "Sagittarius": [("Jupiter", 7), ("Venus", 4), ("Mercury", 6), ("Mars", 6), ("Saturn", 7)],
    "Capricorn": [("Saturn", 7), ("Mercury", 6), ("Venus", 5), ("Jupiter", 5), ("Mars", 7)],
    "Aquarius": [("Saturn", 7), ("Mercury", 5), ("Venus", 6), ("Mars", 5), ("Jupiter", 7)],
    "Pisces": [("Jupiter", 7), ("Venus", 8), ("Mercury", 5), ("Mars", 4), ("Saturn", 6)],
}

# Decans (деканы) — каждый знак делится на 3 части по 10°
DECAN_RULERS = {
    "Aries": ["Mars", "Sun", "Jupiter"],
    "Taurus": ["Venus", "Mercury", "Saturn"],
    "Gemini": ["Mercury", "Venus", "Uranus"],
    "Cancer": ["Moon", "Mars", "Jupiter"],
    "Leo": ["Sun", "Jupiter", "Saturn"],
    "Virgo": ["Mercury", "Venus", "Mercury"],
    "Libra": ["Venus", "Saturn", "Uranus"],
    "Scorpio": ["Mars", "Moon", "Sun"],
    "Sagittarius": ["Jupiter", "Mars", "Sun"],
    "Capricorn": ["Saturn", "Mercury", "Venus"],
    "Aquarius": ["Saturn", "Venus", "Uranus"],
    "Pisces": ["Jupiter", "Moon", "Neptune"],
}


class EssentialDignities:
    """
    Calculates essential dignities for any planet at any degree.
    
    Usage:
        calc = EssentialDignities()
        dignity = calc.get_planet_dignity("Jupiter", 15.5, "Sagittarius")
    """
    
    @staticmethod
    def get_dignity_score(planet: str, degree: float, sign: str) -> Tuple[int, str]:
        """
        Get total dignity score for planet at given position.
        
        Returns: (score, description)
        """
        score = 0
        details = []
        
        # 1. Rulership
        if RULERSHIP.get(sign) == planet:
            score += DignityLevel.RULERSHIP.value
            details.append(f"Rulership: +5")
        
        # 2. Exaltation
        if EXALTATION.get(planet) == sign:
            score += DignityLevel.EXALTATION.value
            details.append(f"Exaltation: +4")
        
        # 3. Detriment
        if DETRIMENT.get(planet) == sign:
            score += DignityLevel.DETRIMENT.value
            details.append(f"Detriment: -5")
        
        # 4. Fall
        if FALL.get(planet) == sign:
            score += DignityLevel.FALL.value
            details.append(f"Fall: -4")
        
        # 5. Triplicity
        triplicity_ruler = EssentialDignities._get_triplicity_ruler(sign)
        if triplicity_ruler == planet:
            score += DignityLevel.TRIPLICITY.value
            details.append(f"Triplicity: +3")
        
        # 6. Term
        term_ruler = EssentialDignities._get_term_ruler(sign, degree)
        if term_ruler == planet:
            score += DignityLevel.TERM.value
            details.append(f"Term: +2")
        
        # 7. Decan
        decan_ruler = EssentialDignities._get_decan_ruler(degree)
        if decan_ruler == planet:
            score += DignityLevel.DECAN.value
            details.append(f"Decan: +1")
        
        return score, "; ".join(details) if details else "No dignity"
    
    @staticmethod
    def _get_triplicity_ruler(sign: str) -> str:
        """Get triplicity ruler for a sign."""
        if sign in FIRE_SIGNS:
            rulers = ["Sun", "Jupiter", "Mars"]
        elif sign in EARTH_SIGNS:
            rulers = ["Venus", "Moon", "Mars"]
        elif sign in AIR_SIGNS:
            rulers = ["Saturn", "Mercury", "Jupiter"]
        else:  # Water
            rulers = ["Venus", "Mars", "Moon"]
        
        # Simplified: return first ruler
        return rulers[0]
    
    @staticmethod
    def _get_term_ruler(sign: str, degree: float) -> str:
        """Get term ruler at given degree."""
        terms = TERMS_EGYPTIAN.get(sign, [])
        accumulated = 0
        for planet, end_degree in terms:
            accumulated += end_degree
            if degree < accumulated:
                return planet
        return terms[-1][0] if terms else "Unknown"
    
    @staticmethod
    def _get_decan_ruler(degree: float) -> str:
        """Get decan ruler at given degree."""
        decan_index = int(degree // 10)
        decans = list(DECAN_RULERS.values())
        return decans[decan_index % 3] if decans else "Unknown"
    
    @staticmethod
    def get_dignity_description(score: int) -> str:
        """Convert numeric score to description."""
        if score >= 10:
            return "Very strong — essential dignity"
        elif score >= 5:
            return "Strong — some dignity"
        elif score >= 1:
            return "Slight dignity"
        elif score == 0:
            return "Neutral — no dignity or debility"
        elif score >= -4:
            return "Weak — some debility"
        else:
            return "Very weak — severe debility"
