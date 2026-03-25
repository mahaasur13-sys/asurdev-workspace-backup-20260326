"""
House Systems — Placidus, Whole Sign, Equal House.
"""
from enum import Enum
from typing import Dict, List, Tuple, Optional
import math


class HouseSystem(Enum):
    PLACIDUS = "P"     # Most popular
    WHOLE_SIGN = "W"   # Sign = House
    EQUAL_HOUSE = "E"  # Each house = 30° from Ascendant
    KOCH = "K"         # Birthplace-centric
    REGIO = "R"        # Campanus equivalent
    PORPHYRY = "O"     # Equal 30° houses from Ascendant


# House qualities
HOUSE_NATURES = {
    1: {"name": "Ascendant", "keywords": "Self, Appearance, Vitality"},
    2: {"name": "2nd House", "keywords": "Money, Possessions, Values"},
    3: {"name": "3rd House", "keywords": "Communication, Siblings, Short journeys"},
    4: {"name": "IC", "keywords": "Home, Family, Roots, Property"},
    5: {"name": "5th House", "keywords": "Creativity, Children, Pleasure"},
    6: {"name": "6th House", "keywords": "Health, Work, Service, Routine"},
    7: {"name": "Descendant", "keywords": "Partnerships, Marriage, Open Enemies"},
    8: {"name": "8th House", "keywords": "Transformation, Shared Resources, Death"},
    9: {"name": "9th House", "keywords": "Higher Education, Travel, Religion"},
    10: {"name": "MC", "keywords": "Career, Public Image, Authority"},
    11: {"name": "11th House", "keywords": "Friendships, Groups, Hopes"},
    12: {"name": "12th House", "keywords": "Hidden Enemies, Institutions, Self-undoing"},
}


class HouseCalculator:
    """
    Calculates house positions using various house systems.
    
    Usage:
        calc = HouseCalculator()
        houses = calc.calculate_houses(ascendant=15.5, lat=40.7128, system=HouseSystem.PLACIDUS)
    """
    
    @staticmethod
    def whole_sign_houses(ascendant: float) -> Dict[int, Tuple[float, float]]:
        """
        Whole Sign house system — simplest.
        Each sign is a house, house 1 = sign containing Ascendant.
        """
        asc_sign = int(ascendant // 30)
        houses = {}
        
        for i in range(12):
            house_num = (asc_sign + i) % 12 + 1
            house_start = i * 30
            house_end = (i + 1) * 30
            houses[house_num] = (house_start, house_end)
        
        return houses
    
    @staticmethod
    def equal_houses(ascendant: float) -> Dict[int, Tuple[float, float]]:
        """
        Equal House system — each house = 30° from Ascendant.
        """
        houses = {}
        for i in range(12):
            house_num = i + 1
            house_start = (ascendant + i * 30) % 360
            house_end = (ascendant + (i + 1) * 30) % 360
            houses[house_num] = (house_start, house_end)
        
        return houses
    
    @staticmethod
    def placidus_houses(
        ascendant: float,
        latitude: float,
        mc: float
    ) -> Dict[int, Tuple[float, float]]:
        """
        Placidus house system — most commonly used.
        
        This is a simplified approximation for educational purposes.
        Real Placidus calculation requires complex spherical trigonometry.
        """
        houses = {}
        
        # Simplified Placidus calculation
        # In practice, use Swiss Ephemeris or detailed algorithm
        asc_sign = int(ascendant // 30)
        mc_sign = int(mc // 30)
        
        # House cusps follow rough approximation
        for i in range(12):
            house_num = i + 1
            
            # Van Roeken formula approximation
            decl = math.sin(math.radians(latitude))
            factor = 1 + decl * math.cos(math.radians(i * 30 - ascendant))
            
            house_start = (ascendant + i * 30 * factor) % 360
            house_end = (ascendant + (i + 1) * 30 * factor) % 360
            
            houses[house_num] = (house_start, house_end)
        
        return houses
    
    @classmethod
    def calculate_houses(
        cls,
        ascendant: float,
        latitude: float = 40.7128,
        mc: Optional[float] = None,
        system: HouseSystem = HouseSystem.WHOLE_SIGN
    ) -> Dict[int, Tuple[float, float]]:
        """
        Calculate houses using specified house system.
        """
        if system == HouseSystem.WHOLE_SIGN:
            return cls.whole_sign_houses(ascendant)
        elif system == HouseSystem.EQUAL_HOUSE:
            return cls.equal_houses(ascendant)
        elif system == HouseSystem.PLACIDUS:
            mc = mc or (ascendant + 90) % 360  # Simplified MC
            return cls.placidus_houses(ascendant, latitude, mc)
        else:
            # Default to Whole Sign
            return cls.whole_sign_houses(ascendant)
    
    @staticmethod
    def get_planet_house(planet_longitude: float, houses: Dict[int, Tuple[float, float]]) -> int:
        """Determine which house a planet is in."""
        for house_num, (start, end) in houses.items():
            if start < end:
                if start <= planet_longitude < end:
                    return house_num
            else:  # House crosses 0°
                if planet_longitude >= start or planet_longitude < end:
                    return house_num
        
        return 1  # Default fallback
    
    @staticmethod
    def get_house_ruler(house_num: int, houses: Dict[int, Tuple[float, float]]) -> str:
        """Get the planet ruling a house based on sign on cusp."""
        from .dignities import RULERSHIP
        
        cusp_start, _ = houses[house_num]
        cusp_sign_idx = int(cusp_start // 30)
        signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                 "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        
        return RULERSHIP.get(signs[cusp_sign_idx], "Unknown")
