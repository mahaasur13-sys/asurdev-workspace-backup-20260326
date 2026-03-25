"""
Western Astrologer — Essential & Accidental Dignities (William Lilly)
 + House Analysis (Michael Mancini Mankasi System)
ДETERMINISTIC VERSION — только расчёты, без "интуиции"
"""
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

# Try to import Mankasi House Analyzer
try:
    from .western_house_analyzer import WesternHouseAnalyzer, HOUSE_TYPES
    MANKASI_AVAILABLE = True
except ImportError:
    MANKASI_AVAILABLE = False
    WesternHouseAnalyzer = None
    HOUSE_TYPES = None

# ============ ESSENTIAL DIGNITIES (Lilly) ============

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

# Terms (Ancient Egyptian)
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


@dataclass
class DignityScore:
    """Результат расчёта dignity"""
    planet: str
    sign: str
    total_score: int
    details: Dict[str, int]
    interpretation: str


class WesternAstrologer:
    """
    Western Astrologer на базе правил William Lilly.
    
    Использует ТОЛЬКО детерминированные расчёты:
    - Essential Dignities (Exaltation, Fall, Triplicity, Term, Face)
    - Accidental Dignities (Joy, Stationary, Combust, etc.)
    - Aspects (Conjunction, Sextile, Square, Trine, Opposition)
    
    Никакой "интуиции" или "interpretations" — только формулы.
    """

    def __init__(self):
        pass

    def analyze(self, positions: Dict[str, float], is_day: bool = True) -> Dict:
        """
        Полный анализ для списка планетных позиций.
        
        Args:
            positions: {planet: degree_in_zodiac} напр. {"Sun": 125.5, "Moon": 45.2}
            is_day: Дневная или ночная карта
            
        Returns:
            Dict с dignity scores, aspects, final signal
        """
        # 1. Convert degrees to signs
        planet_signs = {}
        planet_degrees = {}
        
        for planet, lon in positions.items():
            sign_num = int(lon / 30) % 12
            deg_in_sign = lon % 30
            planet_signs[planet] = SIGNS[sign_num]
            planet_degrees[planet] = deg_in_sign
        
        # 2. Essential Dignities
        dignity_scores = {}
        for planet, sign in planet_signs.items():
            score, details = self._calculate_dignity(planet, sign, is_day)
            dignity_scores[planet] = DignityScore(
                planet=planet,
                sign=sign,
                total_score=score,
                details=details,
                interpretation=self._interpret_score(score)
            )
        
        # 3. Accidental Dignities
        acc_dignities = self._calculate_accidental(planet_degrees, planet_signs, positions)
        
        # 4. Aspects
        aspects = self._calculate_aspects(positions)
        
        # 5. Final signal
        signal, confidence = self._calculate_signal(dignity_scores, acc_dignities, aspects)
        
        return {
            "dignities": {p: {
                "sign": d.sign,
                "score": d.total_score,
                "details": d.details
            } for p, d in dignity_scores.items()},
            "accidental": acc_dignities,
            "aspects": aspects,
            "signal": signal,
            "confidence": confidence,
            "interpretation": self._format_interpretation(dignity_scores, aspects)
        }
    
    def _calculate_dignity(self, planet: str, sign: str, is_day: bool) -> Tuple[int, Dict]:
        """Расчёт essential dignity score"""
        score = 0
        details = {}
        
        # Exaltation (+5)
        if sign == EXALTATION.get(planet, {}).get("sign"):
            score += 5
            details["exaltation"] = 5
        
        # Fall (-4)
        elif sign == FALL.get(planet):
            score -= 4
            details["fall"] = -4
        
        # Triplicity (±3)
        element = ELEMENTS.get(sign, "Earth")
        triplicity = TRIPLICITY_DAY if is_day else TRIPLICITY_NIGHT
        if planet in triplicity.get(element, {}).values():
            score += 3
            details["triplicity"] = 3
        
        # Term (±2)
        for term_planet, end_deg in TERMS.get(sign, []):
            if term_planet == planet:
                score += 2
                details["term"] = 2
                break
        
        return score, details
    
    def _calculate_accidental(self, degrees: Dict, signs: Dict, positions: Dict) -> Dict:
        """Расчёт accidental dignities"""
        acc = {}
        
        for planet in positions:
            score = 0
            notes = []
            
            # Joy sign
            joy_signs = {"Sun": "Aries", "Moon": "Taurus", "Saturn": "Libra",
                        "Jupiter": "Cancer", "Mars": "Scorpio", "Venus": "Pisces",
                        "Mercury": "Virgo"}
            if signs.get(planet) == joy_signs.get(planet):
                score += 5
                notes.append("Joy")
            
            # Combust (within 8°30' of Sun)
            sun_degree = degrees.get("Sun", 0)
            planet_degree = degrees.get(planet, 0)
            diff = abs(sun_degree - planet_degree)
            if diff < 8.5 or diff > 351.5:
                score -= 4
                notes.append("Combust")
            
            acc[planet] = {"score": score, "notes": notes}
        
        return acc
    
    def _calculate_aspects(self, positions: Dict[str, float]) -> List[Dict]:
        """Расчёт аспектов (Lilly)"""
        aspects = []
        
        ASPECT_ORBS = {
            "conjunction": 8,
            "sextile": 6,
            "square": 8,
            "trine": 8,
            "opposition": 10,
        }
        
        ASPECT_SYMBOLS = {
            "conjunction": "☌", "sextile": "✶", "square": "□",
            "trine": "△", "opposition": "☍"
        }
        
        planets = list(positions.keys())
        
        for i, p1 in enumerate(planets):
            for p2 in planets[i+1:]:
                lon1, lon2 = positions[p1], positions[p2]
                diff = abs(lon1 - lon2)
                if diff > 180:
                    diff = 360 - diff
                
                for aspect_name, orb in ASPECT_ORBS.items():
                    ideal_angle = {"conjunction": 0, "sextile": 60, "square": 90,
                                   "trine": 120, "opposition": 180}[aspect_name]
                    
                    if abs(diff - ideal_angle) <= orb:
                        aspects.append({
                            "planets": f"{p1}-{p2}",
                            "aspect": aspect_name,
                            "symbol": ASPECT_SYMBOLS[aspect_name],
                            "actual_angle": round(diff, 1),
                            "orb": round(abs(diff - ideal_angle), 1),
                            "nature": "good" if aspect_name in ["sextile", "trine"] 
                                      else "bad" if aspect_name in ["square", "opposition"]
                                      else "neutral"
                        })
        
        return aspects
    
    def _calculate_signal(self, dignities: Dict, acc_dign: Dict, aspects: List) -> Tuple[str, int]:
        """Финальный сигнал на основе всех расчётов"""
        # Суммарный score для Луны (главный индикатор)
        moon_score = dignities.get("Moon", DignityScore("Moon", "Aries", 0, {}, "")).total_score
        moon_acc = acc_dign.get("Moon", {"score": 0})["score"]
        
        # Считать хорошие/плохие аспекты
        good_aspects = sum(1 for a in aspects if a["nature"] == "good")
        bad_aspects = sum(1 for a in aspects if a["nature"] == "bad")
        
        # Combined score
        combined = moon_score + moon_acc + (good_aspects * 2) - (bad_aspects * 2)
        
        if combined >= 10:
            return "STRONG_BULLISH", 70
        elif combined >= 5:
            return "BULLISH", 60
        elif combined >= -5:
            return "NEUTRAL", 50
        elif combined >= -10:
            return "BEARISH", 60
        else:
            return "STRONG_BEARISH", 70
    
    @staticmethod
    def _interpret_score(score: int) -> str:
        """Интерпретация dignity score"""
        if score >= 5:
            return "Strong"
        elif score >= 3:
            return "Moderate"
        elif score >= 1:
            return "Weak"
        elif score >= -1:
            return "Neutral"
        elif score >= -3:
            return "Debilitated"
        else:
            return "Very Debilitated"
    
    def _format_interpretation(self, dignities: Dict, aspects: List) -> str:
        """Форматирование результата для человека"""
        lines = ["Western Astrology Analysis:"]
        
        for planet, d in dignities.items():
            lines.append(f"  {planet} in {d.sign}: Score={d.total_score} ({d.interpretation})")
        
        lines.append(f"  Aspects: {len(aspects)} found")
        for a in aspects[:5]:
            lines.append(f"    {a['planets']} {a['symbol']} ({a['nature']})")
        
        return "\n".join(lines)

    def interpret_houses(self, ephemeris_data: Dict[str, Any], is_day: bool = True) -> Dict[str, Any]:
        """
        Интерпретация домов по системе Манкаси (Michael Mancini).
        
        Использует WesternHouseAnalyzer для 6-шагового алгоритма анализа:
        1. Identify House Ruler
        2. Assess Essential Dignity of Ruler
        3. Evaluate House Position of Ruler
        4. Find and Evaluate Planetary Forger
        5. Count Planets in House
        6. Calculate Final Score and Interpret
        
        Args:
            ephemeris_data: Данные из Swiss Ephemeris, содержащие:
                - positions: {planet: degree} или {planet: {"sign": str, "degree": float}}
                - houses: Dict[int, Dict] с куспидами
                - planets_in_signs: Dict[str, List[str]] — какие планеты в каких знаках
            is_day: Дневная или ночная карта
            
        Returns:
            Dict с анализом всех 12 домов
        """
        if not MANKASI_AVAILABLE:
            return {
                "error": "Mankasi House Analyzer not available",
                "mankasi_enabled": False
            }
        
        analyzer = WesternHouseAnalyzer(is_day_chart=is_day)
        
        positions = ephemeris_data.get("positions", {})
        houses = ephemeris_data.get("houses", {})
        planets_in_signs = ephemeris_data.get("planets_in_signs", {})
        
        # Convert positions to consistent format
        planet_positions = {}
        for planet, pos_data in positions.items():
            if isinstance(pos_data, dict):
                planet_positions[planet] = pos_data
            else:
                # degree_in_zodiac format
                sign_num = int(pos_data / 30) % 12
                deg_in_sign = pos_data % 30
                planet_positions[planet] = {
                    "sign": SIGNS[sign_num],
                    "degree": deg_in_sign
                }
        
        results = {}
        all_scores = []
        
        for house_num in range(1, 13):
            house_info = houses.get(house_num, {})
            cusp_sign = house_info.get("sign", "Unknown")
            
            # Find ruler of cusp sign
            ruler = self._get_sign_ruler(cusp_sign)
            
            # Find ruler's current position
            ruler_pos = planet_positions.get(ruler, {"sign": "Unknown", "degree": 0})
            ruler_sign = ruler_pos.get("sign", "Unknown")
            
            # Determine which house the ruler is in
            ruler_house = self._find_planet_house(ruler, houses, planet_positions)
            ruler_pos["house"] = ruler_house
            
            # Find planets in this house
            planets_in_house = self._get_planets_in_house(house_num, planet_positions, houses)
            
            # Check for intercepted signs (simplified)
            is_intercepted = house_info.get("intercepted", False)
            intercepted_signs = house_info.get("intercepted_signs", [])
            
            # Analyze using Mankasi algorithm
            analysis = analyzer.analyze_house(
                house=house_num,
                cusp_sign=cusp_sign,
                ruler=ruler,
                ruler_position=ruler_pos,
                planets_in_house=planets_in_house,
                sun_degree=planet_positions.get("Sun", {}).get("degree", 0),
                is_intercepted=is_intercepted,
                intercepted_signs=intercepted_signs
            )
            
            results[f"House_{house_num}"] = {
                "cusp_sign": cusp_sign,
                "ruler": ruler,
                "ruler_sign": ruler_sign,
                "ruler_dignity": analysis.ruler_dignity.total,
                "house_type": analysis.house_type,
                "forger": analysis.forger,
                "forger_status": "strong" if analysis.forger_dignity and analysis.forger_dignity.total > 0 else "weak",
                "planets": planets_in_house,
                "intercepted": is_intercepted,
                "score": analysis.total_score,
                "strength": analysis.strength_category,
                "interpretation": analysis.interpretation
            }
            
            all_scores.append(analysis.total_score)
        
        # Calculate overall house strength
        avg_score = sum(all_scores) / len(all_scores) if all_scores else 0
        
        return {
            "mankasi_enabled": True,
            "houses": results,
            "summary": {
                "average_score": round(avg_score, 1),
                "strongest_houses": self._get_strongest_houses(results, top_n=3),
                "weakest_houses": self._get_weakest_houses(results, top_n=3),
            },
            "house_descriptions": {
                1: "Who I am — Личность, внешность, здоровье",
                2: "Resources — Финансы, собственность, ценности",
                3: "Communication — Обучение, коммуникация, братья/сёстры",
                4: "Home — Семья, недвижимость, корни",
                5: "Creativity — Дети, творчество, романтика",
                6: "Service — Работа, здоровье, слуги",
                7: "Partnerships — Брак, партнёрства, открытые враги",
                8: "Transformation — Секс, трансформация, наследство",
                9: "Higher Mind — Философия, путешествия, высшее образование",
                10: "Career — Профессия, статус, общественное положение",
                11: "Hopes — Надежды, друзья, группы",
                12: "Isolation — Ограничения, тайные враги, психическое здоровье"
            }
        }
    
    def _get_sign_ruler(self, sign: str) -> str:
        """Get ruler of a sign"""
        DOMICILE = {
            "Sun": ["Leo"], "Moon": ["Cancer"],
            "Mercury": ["Gemini", "Virgo"], "Venus": ["Taurus", "Libra"],
            "Mars": ["Aries", "Scorpio"], "Jupiter": ["Sagittarius", "Pisces"],
            "Saturn": ["Capricorn", "Aquarius"],
        }
        for planet, signs in DOMICILE.items():
            if sign in signs:
                return planet
        return "Unknown"
    
    def _find_planet_house(self, planet: str, houses: Dict, planet_positions: Dict) -> int:
        """Find which house a planet is in"""
        planet_pos = planet_positions.get(planet, {})
        planet_sign = planet_pos.get("sign", "")
        
        for house_num, house_info in houses.items():
            if house_info.get("sign") == planet_sign:
                return house_num
        
        return 7  # Default to 7th house if not found
    
    def _get_planets_in_house(self, house_num: int, planet_positions: Dict, houses: Dict) -> List[str]:
        """Get list of planets in a specific house"""
        house_info = houses.get(house_num, {})
        house_sign = house_info.get("sign", "")
        
        planets = []
        for planet, pos in planet_positions.items():
            if pos.get("sign") == house_sign:
                planets.append(planet)
        
        return planets
    
    def _get_strongest_houses(self, results: Dict, top_n: int = 3) -> List[Dict]:
        """Get top N strongest houses by score"""
        sorted_houses = sorted(
            [(k, v["score"], v["strength"]) for k, v in results.items()],
            key=lambda x: x[1], reverse=True
        )
        return [{"house": h[0], "score": h[1], "strength": h[2]} for h in sorted_houses[:top_n]]
    
    def _get_weakest_houses(self, results: Dict, top_n: int = 3) -> List[Dict]:
        """Get top N weakest houses by score"""
        sorted_houses = sorted(
            [(k, v["score"], v["strength"]) for k, v in results.items()],
            key=lambda x: x[1]
        )
        return [{"house": h[0], "score": h[1], "strength": h[2]} for h in sorted_houses[:top_n]]
