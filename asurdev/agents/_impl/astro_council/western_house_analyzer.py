"""
Western House Analyzer — Mankasi System
========================================

Michael Mancini's House Analysis System:
- Planetary Forgers (Dispositors)
- Intercepted Signs
- House Strength Algorithm (6 steps)
- Essential & Accidental Dignities
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any


EXALTATION = {
    "Sun": {"sign": "Aries", "degree": 19},
    "Moon": {"sign": "Taurus", "degree": 3},
    "Mercury": {"sign": "Virgo", "degree": 15},
    "Venus": {"sign": "Pisces", "degree": 27},
    "Mars": {"sign": "Capricorn", "degree": 28},
    "Jupiter": {"sign": "Cancer", "degree": 15},
    "Saturn": {"sign": "Libra", "degree": 21},
}

FALL = {p: v["sign"] for p, v in EXALTATION.items()}
FALL["Sun"] = "Libra"
FALL["Moon"] = "Scorpio"

DOMICILE = {
    "Sun": ["Leo"],
    "Moon": ["Cancer"],
    "Mercury": ["Gemini", "Virgo"],
    "Venus": ["Taurus", "Libra"],
    "Mars": ["Aries", "Scorpio"],
    "Jupiter": ["Sagittarius", "Pisces"],
    "Saturn": ["Capricorn", "Aquarius"],
}

DETRIMENT = {
    "Sun": ["Aquarius"],
    "Moon": ["Capricorn"],
    "Mercury": ["Sagittarius", "Pisces"],
    "Venus": ["Aries", "Scorpio"],
    "Mars": ["Libra", "Taurus"],
    "Jupiter": ["Gemini", "Virgo"],
    "Saturn": ["Cancer", "Leo"],
}

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

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

ELEMENTS = {
    "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
    "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
    "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
    "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water",
}

HOUSE_TYPES = {
    1: {"type": "Angular", "score": 4, "description": "Who I am"},
    2: {"type": "Succedent", "score": 2, "description": "Resources"},
    3: {"type": "Cadent", "score": 1, "description": "Communication"},
    4: {"type": "Angular", "score": 4, "description": "Home"},
    5: {"type": "Succedent", "score": 2, "description": "Creativity"},
    6: {"type": "Cadent", "score": 1, "description": "Service"},
    7: {"type": "Angular", "score": 4, "description": "Partnerships"},
    8: {"type": "Succedent", "score": 2, "description": "Transformation"},
    9: {"type": "Cadent", "score": 1, "description": "Higher mind"},
    10: {"type": "Angular", "score": 4, "description": "Career"},
    11: {"type": "Succedent", "score": 2, "description": "Hopes"},
    12: {"type": "Cadent", "score": 1, "description": "Isolation"},
}


@dataclass
class DignityScore:
    planet: str
    sign: str
    domicile: int = 0
    exaltation: int = 0
    triplicity: int = 0
    term: int = 0
    fall: int = 0
    detriment: int = 0
    total: int = 0
    
    def __post_init__(self):
        self.total = self.domicile + self.exaltation + self.triplicity + self.term + self.fall + self.detriment


@dataclass
class HouseAnalysis:
    house: int
    cusp_sign: str
    ruler: str
    ruler_position: Dict[str, Any]
    ruler_dignity: DignityScore
    house_type: str
    house_type_score: int
    forger: Optional[str] = None
    forger_dignity: Optional[DignityScore] = None
    planets_in_house: List[str] = field(default_factory=list)
    intercepted: bool = False
    intercepted_signs: List[str] = field(default_factory=list)
    total_score: int = 0
    strength_category: str = "Unknown"
    interpretation: str = ""
    step_scores: Dict[str, int] = field(default_factory=dict)


class WesternHouseAnalyzer:
    """Michael Mancini's House Analysis System."""
    
    def __init__(self, is_day_chart: bool = True):
        self.is_day_chart = is_day_chart
    
    def calculate_essential_dignity(self, planet: str, sign: str) -> DignityScore:
        ds = DignityScore(planet=planet, sign=sign)
        
        if sign in DOMICILE.get(planet, []):
            ds.domicile = 4
        if EXALTATION.get(planet, {}).get("sign") == sign:
            ds.exaltation = 5
        if FALL.get(planet) == sign:
            ds.fall = -5
        if sign in DETRIMENT.get(planet, []):
            ds.detriment = -4
        
        element = ELEMENTS.get(sign, "Earth")
        triplicity = TRIPLICITY_DAY if self.is_day_chart else TRIPLICITY_NIGHT
        if planet in triplicity.get(element, {}).values():
            ds.triplicity = 3
        
        for term_planet, end_deg in TERMS.get(sign, []):
            if term_planet == planet:
                ds.term = 2
                break
        
        ds.total = ds.domicile + ds.exaltation + ds.triplicity + ds.term + ds.fall + ds.detriment
        return ds
    
    def get_sign_ruler(self, sign: str) -> str:
        for planet, signs in DOMICILE.items():
            if sign in signs:
                return planet
        return "Unknown"
    
    def get_forger(self, ruler_position: Dict[str, Any]) -> Tuple[str, Optional[DignityScore]]:
        if not ruler_position or not ruler_position.get("sign"):
            return None, None
        
        ruler_sign = ruler_position["sign"]
        forger = self.get_sign_ruler(ruler_sign)
        
        if forger == "Unknown":
            return None, None
        
        forger_dignity = self.calculate_essential_dignity(forger, ruler_sign)
        return forger, forger_dignity
    
    def analyze_house(
        self,
        house: int,
        cusp_sign: str,
        ruler: str,
        ruler_position: Dict[str, Any],
        planets_in_house: List[str],
        sun_degree: float = 0,
        is_intercepted: bool = False,
        intercepted_signs: Optional[List[str]] = None
    ) -> HouseAnalysis:
        analysis = HouseAnalysis(
            house=house,
            cusp_sign=cusp_sign,
            ruler=ruler,
            ruler_position=ruler_position,
            ruler_dignity=self.calculate_essential_dignity(ruler, cusp_sign),
            house_type=HOUSE_TYPES[house]["type"],
            house_type_score=HOUSE_TYPES[house]["score"],
            planets_in_house=planets_in_house,
            intercepted=is_intercepted,
            intercepted_signs=intercepted_signs or [],
        )
        
        step_scores = {}
        step_scores["step1_ruler"] = 0
        step_scores["step2_essential"] = analysis.ruler_dignity.total
        
        ruler_house = ruler_position.get("house", 7)
        house_pos_score = HOUSE_TYPES.get(ruler_house, {"score": 1})["score"]
        step_scores["step3_house_position"] = house_pos_score
        
        forger, forger_dignity = self.get_forger(ruler_position)
        analysis.forger = forger
        analysis.forger_dignity = forger_dignity
        
        forger_bonus = 0
        if forger_dignity:
            if forger_dignity.domicile > 0 or forger_dignity.exaltation > 0:
                forger_bonus = 2
            elif forger_dignity.total > 0:
                forger_bonus = 1
            elif forger_dignity.total < 0:
                forger_bonus = -2
        step_scores["step4_forger"] = forger_bonus
        
        planet_count = len(planets_in_house)
        if planet_count >= 3:
            planet_score = 3
        elif planet_count == 2:
            planet_score = 2
        elif planet_count == 1:
            planet_score = 1
        elif planet_count == 0:
            planet_score = -1
        else:
            planet_score = 0
        step_scores["step5_planets"] = planet_score
        
        total = (
            analysis.ruler_dignity.total +
            house_pos_score +
            forger_bonus +
            planet_score
        )
        step_scores["step6_total"] = total
        analysis.step_scores = step_scores
        analysis.total_score = total
        
        if total >= 10:
            analysis.strength_category = "Very Strong"
        elif total >= 6:
            analysis.strength_category = "Strong"
        elif total >= 3:
            analysis.strength_category = "Moderate"
        elif total >= 0:
            analysis.strength_category = "Weak"
        else:
            analysis.strength_category = "Very Weak"
        
        analysis.interpretation = self._generate_interpretation(analysis)
        return analysis
    
    def _generate_interpretation(self, analysis: HouseAnalysis) -> str:
        lines = [
            f"House {analysis.house} ({HOUSE_TYPES[analysis.house]['description']}):",
            f"  Cusp: {analysis.cusp_sign}",
            f"  Ruler: {analysis.ruler} in {analysis.ruler_position.get('sign', 'Unknown')}",
            f"  Ruler dignity: {analysis.ruler_dignity.total}",
            f"  House type: {analysis.house_type} (+{analysis.house_type_score})",
        ]
        
        if analysis.forger:
            forger_status = "strong" if analysis.forger_dignity and analysis.forger_dignity.total > 0 else "weak"
            lines.append(f"  Forger: {analysis.forger} ({forger_status})")
        
        lines.append(f"  Planets: {', '.join(analysis.planets_in_house) or 'None'}")
        
        if analysis.intercepted:
            lines.append(f"  INTERCEPTED: {', '.join(analysis.intercepted_signs)}")
        
        lines.append(f"  TOTAL SCORE: {analysis.total_score} ({analysis.strength_category})")
        
        return "\n".join(lines)
    
    @staticmethod
    def _dignity_label(score: int) -> str:
        if score >= 5:
            return "Very Strong"
        elif score >= 3:
            return "Strong"
        elif score >= 1:
            return "Moderate"
        elif score >= -1:
            return "Neutral"
        elif score >= -3:
            return "Debilitated"
        else:
            return "Very Debilitated"


if __name__ == "__main__":
    print("=" * 60)
    print("Western House Analyzer — Mankasi System Test")
    print("=" * 60)
    
    analyzer = WesternHouseAnalyzer(is_day_chart=True)
    
    # Test House 10
    result = analyzer.analyze_house(
        house=10,
        cusp_sign="Sagittarius",
        ruler="Jupiter",
        ruler_position={"sign": "Taurus", "degree": 15.2, "house": 4},
        planets_in_house=["Venus"],
    )
    print(result.interpretation)
    print()
