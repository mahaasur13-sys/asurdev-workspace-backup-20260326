"""
HoraryChart — Core chart class for horary astrology.
Based on William Lilly "Christian Astrology" (1647)
"""

import math
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field

import swisseph as swe

from astrology.core import (
    EssentialDignities, AccidentalDignities, Aspects,
    EXALTATION, FALL, TERMS, DECANS, JOY,
)
from astrology.houses import calculate_whole_sign_houses, calculate_porphyry_cusps


SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
         "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

SIGN_ELEMENTS = {
    "Aries": "Fire", "Leo": "Fire", "Sagittarius": "Fire",
    "Taurus": "Earth", "Virgo": "Earth", "Capricorn": "Earth",
    "Gemini": "Air", "Libra": "Air", "Aquarius": "Air",
    "Cancer": "Water", "Scorpio": "Water", "Pisces": "Water",
}

TRADITIONAL_PLANETS = ["Mars", "Venus", "Mercury", "Jupiter", "Saturn", "Sun", "Moon"]

# Swiss Ephemeris planet IDs
SWE_PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
}

HOUSE_MEANINGS = {
    1: "The Querier (self)",
    2: "Money, possessions, assets",
    3: "Siblings, short travel, communication",
    4: "Real estate, heritage",
    5: "Speculation, children, gambling",
    6: "Health, employees, pets",
    7: "Partnerships, marriage, open enemies",
    8: "Death, debts, inheritance",
    9: "Long travel, religion, higher education",
    10: "Career, reputation, mother",
    11: "Hopes, wishes, friends",
    12: "Hidden enemies, imprisonment, self-undoing",
}


@dataclass
class PlanetPosition:
    name: str
    sign: str
    degree: float
    longitude: float
    speed: float = 1.0
    is_orient: bool = False
    is_occident: bool = False
    dignity_score: int = 0
    
    @property
    def sign_num(self) -> int:
        return SIGNS.index(self.sign) if self.sign in SIGNS else 0
    
    @property
    def element(self) -> str:
        return SIGN_ELEMENTS.get(self.sign, "Earth")
    
    @property
    def is_exalted(self) -> bool:
        return self.sign == EXALTATION.get(self.name, {}).get("sign")
    
    @property
    def is_fall(self) -> bool:
        return self.sign == FALL.get(self.name)
    
    @property
    def in_joy(self) -> bool:
        return self.sign == JOY.get(self.name)


@dataclass
class Significator:
    planet: PlanetPosition
    house: int
    dignity_score: int
    accidental_score: int = 0
    aspects_to_other: List[Dict] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    
    @property
    def total_score(self) -> int:
        return self.dignity_score + self.accidental_score


class HoraryChart:
    """
    Horary Chart for financial decisions.
    Based on William Lilly "Christian Astrology" (1647).
    """
    
    def __init__(
        self,
        question: str,
        dt: datetime,
        lat: float = 28.6139,
        lon: float = 77.2090,
        house_system: str = "whole_sign",
    ):
        self.question = question
        self.datetime = dt
        self.lat = lat
        self.lon = lon
        self.house_system = house_system
        
        self.is_day = 6 <= dt.hour < 18
        self.positions: Dict[str, PlanetPosition] = {}
        self.cusps: List[float] = []
        self.asc: float = 0
        
        self._calculate_positions_sweph()
        self._calculate_houses()
        self._calculate_dignities()
    
    def _calculate_positions_sweph(self):
        """Calculate planetary positions using Swiss Ephemeris."""
        # Calculate Julian Day
        jd = swe.julday(
            self.datetime.year,
            self.datetime.month,
            self.datetime.day,
            self.datetime.hour + self.datetime.minute / 60 + self.datetime.second / 3600
        )
        
        sun_lon = None
        
        for planet_name, planet_id in SWE_PLANETS.items():
            # Get position with Swiss Ephemeris
            result = swe.calc(jd, planet_id, swe.FLG_SWIEPH)
            lon = result[0][0]  # Longitude in degrees
            speed = result[0][3]  # Speed in degrees per day
            
            sign_num = int(lon // 30) % 12
            deg_in_sign = lon % 30
            
            self.positions[planet_name] = PlanetPosition(
                name=planet_name,
                sign=SIGNS[sign_num],
                degree=deg_in_sign,
                longitude=lon,
                speed=abs(speed),
                is_orient=(lon > sun_lon) if sun_lon and planet_name != "Sun" else False,
                is_occident=(lon < sun_lon) if sun_lon and planet_name != "Sun" else False,
            )
            
            if planet_name == "Sun":
                sun_lon = lon
    
    def _calculate_houses(self):
        if "Sun" in self.positions:
            sun_pos = self.positions["Sun"].longitude
            hour_angle = (self.datetime.hour - 12) * 15
            self.asc = (sun_pos + hour_angle) % 360
        else:
            self.asc = self._julian_day(self.datetime) % 360
        
        if self.house_system == "whole_sign":
            self.cusps = calculate_whole_sign_houses(self.asc)
        else:
            self.cusps = calculate_porphyry_cusps(self.asc, (self.asc + 90) % 360)
    
    def _julian_day(self, dt: datetime) -> float:
        Y, M = dt.year, dt.month
        D = dt.day + (dt.hour + dt.minute / 60 + dt.second / 3600) / 24
        if M <= 2:
            Y, M = Y - 1, M + 12
        A = int(Y / 100)
        B = 2 - A + int(A / 4)
        return int(365.25 * (Y + 4716)) + int(30.6001 * (M + 1)) + D + B - 1524.5
    
    def _calculate_dignities(self):
        for planet_name, pos in self.positions.items():
            score, details = EssentialDignities.get_dignity_score(
                planet_name, pos.sign, self.is_day
            )
            pos.dignity_score = score
            pos.dignity_details = details
    
    def get_planet_in_house(self, planet_name: str) -> int:
        if planet_name not in self.positions:
            return 0
        planet_long = self.positions[planet_name].longitude
        for i in range(12):
            cusp_start = self.cusps[i]
            cusp_end = self.cusps[(i + 1) % 12]
            if cusp_end > cusp_start:
                if cusp_start <= planet_long < cusp_end:
                    return i + 1
            else:
                if planet_long >= cusp_start or planet_long < cusp_end:
                    return i + 1
        return 1
    
    def get_house_ruler(self, house_num: int) -> str:
        cusp_long = self.cusps[house_num - 1]
        cusp_sign = SIGNS[int(cusp_long // 30)]
        sign_rulers = {
            "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury",
            "Cancer": "Moon", "Leo": "Sun", "Virgo": "Mercury",
            "Libra": "Venus", "Scorpio": "Mars", "Sagittarius": "Jupiter",
            "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter",
        }
        return sign_rulers.get(cusp_sign, "Mercury")
    
    def get_significator(self, planet_name: str) -> Significator:
        if planet_name not in self.positions:
            raise ValueError(f"Planet {planet_name} not in chart")
        
        pos = self.positions[planet_name]
        house = self.get_planet_in_house(planet_name)
        
        ess_score, ess_details = EssentialDignities.get_dignity_score(
            planet_name, pos.sign, self.is_day
        )
        
        acc_dignities = AccidentalDignities.analyze(
            planet_name,
            {"sign": pos.sign, "degree": pos.degree,
             "speed": pos.speed, "is_orient": pos.is_orient,
             "is_occident": pos.is_occident}
        )
        acc_score = sum(d.score for d in acc_dignities)
        aspects = self.get_aspects_to_planet(planet_name)
        
        return Significator(
            planet=pos,
            house=house,
            dignity_score=ess_score,
            accidental_score=acc_score,
            aspects_to_other=aspects,
            notes=ess_details + [d.description for d in acc_dignities],
        )
    
    def get_aspects_to_planet(self, planet_name: str) -> List[Dict]:
        if planet_name not in self.positions:
            return []
        source_long = self.positions[planet_name].longitude
        aspects_found = []
        for other_name, other_pos in self.positions.items():
            if other_name == planet_name:
                continue
            aspects = Aspects.calculate_aspects(source_long, other_pos.longitude)
            for asp in aspects:
                aspects_found.append({
                    "to": other_name,
                    "aspect": asp["aspect"],
                    "nature": asp["nature"],
                    "orb": asp["orb"],
                })
        return aspects_found
    
    def get_ruling_planets(self, house: int) -> Tuple[str, Optional[str]]:
        cusp_long = self.cusps[house - 1]
        cusp_sign = SIGNS[int(cusp_long // 30)]
        rulers = {
            "Aries": ("Mars", None), "Taurus": ("Venus", None),
            "Gemini": ("Mercury", None), "Cancer": ("Moon", None),
            "Leo": ("Sun", None), "Virgo": ("Mercury", None),
            "Libra": ("Venus", "Mars"), "Scorpio": ("Mars", "Jupiter"),
            "Sagittarius": ("Jupiter", None), "Capricorn": ("Saturn", None),
            "Aquarius": ("Saturn", "Jupiter"), "Pisces": ("Jupiter", "Venus"),
        }
        return rulers.get(cusp_sign, ("Mercury", None))
    
    def describe(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "datetime": self.datetime.isoformat(),
            "is_day": self.is_day,
            "ascendant": {
                "longitude": round(self.asc, 2),
                "sign": SIGNS[int(self.asc // 30)],
                "degree": round(self.asc % 30, 2),
            },
            "positions": {
                name: {
                    "sign": pos.sign,
                    "degree": round(pos.degree, 2),
                    "house": self.get_planet_in_house(name),
                }
                for name, pos in self.positions.items()
            },
            "cusps": [round(c, 2) for c in self.cusps],
        }
