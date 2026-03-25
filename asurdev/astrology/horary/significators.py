"""
SignificatorRegistry — Traditional significator definitions.
Based on Lilly "Christian Astrology" Book 2: Of Horary Questions
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class SignificatorCategory(Enum):
    """Categories of significators."""
    PERSON = "person"
    MONEY = "money"
    ASSETS = "assets"
    PARTNERSHIP = "partnership"
    CAREER = "career"
    TRAVEL = "travel"
    LEGAL = "legal"
    HEALTH = "health"
    DEATH = "death"


@dataclass
class SignificatorDef:
    """Definition of a significator."""
    name: str
    planets: List[str]
    houses: List[int]
    description: str
    category: SignificatorCategory


# Traditional significators from Lilly
SIGNIFICATOR_REGISTRY: Dict[str, SignificatorDef] = {
    # === MONEY & ASSETS ===
    "money": SignificatorDef(
        name="Money & Possessions",
        planets=["Jupiter", "Venus"],
        houses=[2],
        description="The 2nd house and its lord signify money and possessions. "
                    "Jupiter and Venus are natural significators of value.",
        category=SignificatorCategory.MONEY
    ),
    "wealth": SignificatorDef(
        name="Wealth",
        planets=["Jupiter", "Sun"],
        houses=[2, 11],
        description="The 2nd house for inherited wealth, 11th for gains.",
        category=SignificatorCategory.MONEY
    ),
    "debts": SignificatorDef(
        name="Debts & Borrowing",
        planets=["Saturn", "Mars"],
        houses=[2, 6, 8],
        description="Saturn signifies debts and obstacles. Mars in 8th indicates "
                    "other people's money. The 8th house rules debt.",
        category=SignificatorCategory.MONEY
    ),
    
    # === FINANCIAL ACTIONS ===
    "buy": SignificatorDef(
        name="Buying",
        planets=["Mercury", "Mars"],
        houses=[3, 7],
        description="Mercury signifies commerce and exchange. Mars signifies "
                    "the querent's desire to acquire. 3rd house for short actions.",
        category=SignificatorCategory.ASSETS
    ),
    "sell": SignificatorDef(
        name="Selling",
        planets=["Mercury", "Venus"],
        houses=[3, 11],
        description="Mercury for commerce. Venus for possessions. 11th for gains "
                    "from sales.",
        category=SignificatorCategory.ASSETS
    ),
    "invest": SignificatorDef(
        name="Investment",
        planets=["Jupiter", "Venus"],
        houses=[2, 5, 11],
        description="5th house for speculation. 2nd for money. Jupiter for growth. "
                    "Venus for stable value.",
        category=SignificatorCategory.MONEY
    ),
    "speculate": SignificatorDef(
        name="Speculation & Gambling",
        planets=["Mars", "Jupiter", "Moon"],
        houses=[5],
        description="The 5th house is the house of speculation. Mars gives boldness. "
                    "Jupiter gives fortune. Moon shows the current trend.",
        category=SignificatorCategory.MONEY
    ),
    
    # === PARTNERSHIP ===
    "partnership": SignificatorDef(
        name="Partnership",
        planets=["Venus", "Jupiter"],
        houses=[7],
        description="The 7th house rules partnerships. Venus signifies harmony. "
                    "Jupiter signifies benefit. Both parties should be considered.",
        category=SignificatorCategory.PARTNERSHIP
    ),
    "marriage": SignificatorDef(
        name="Marriage",
        planets=["Venus", "Jupiter"],
        houses=[7],
        description="Venus is the natural significator of marriage. Jupiter signifies "
                    "the partner. The 7th house is the house of marriage.",
        category=SignificatorCategory.PARTNERSHIP
    ),
    
    # === CAREER ===
    "career": SignificatorDef(
        name="Career & Profession",
        planets=["Sun", "Jupiter", "Mars"],
        houses=[10],
        description="The 10th house is the house of career. Sun signifies authority. "
                    "Jupiter signifies advancement. Mars signifies action.",
        category=SignificatorCategory.CAREER
    ),
    "job": SignificatorDef(
        name="Employment",
        planets=["Mars", "Saturn", "Mercury"],
        houses=[6, 10],
        description="6th house is the house of servants/work. 10th is career. "
                    "Saturn signifies employment. Mars signifies new ventures.",
        category=SignificatorCategory.CAREER
    ),
    "business": SignificatorDef(
        name="Business",
        planets=["Mercury", "Mars"],
        houses=[10, 11],
        description="Mercury rules commerce. Mars gives drive. The 10th house "
                    "is the career/business. The 11th is gains.",
        category=SignificatorCategory.CAREER
    ),
    
    # === TRAVEL ===
    "travel": SignificatorDef(
        name="Travel",
        planets=["Mercury", "Moon"],
        houses=[3, 9],
        description="3rd house is short travel. 9th house is long travel. Mercury "
                    "and Moon signify movement and communication.",
        category=SignificatorCategory.TRAVEL
    ),
    "short_travel": SignificatorDef(
        name="Short Travel",
        planets=["Mercury"],
        houses=[3],
        description="3rd house rules short journeys, visits, errands.",
        category=SignificatorCategory.TRAVEL
    ),
    "long_travel": SignificatorDef(
        name="Long Travel",
        planets=["Jupiter", "Moon"],
        houses=[9],
        description="9th house rules long journeys, foreign travel, pilgrimage.",
        category=SignificatorCategory.TRAVEL
    ),
    
    # === LEGAL ===
    "legal": SignificatorDef(
        name="Legal Matters",
        planets=["Jupiter", "Sun"],
        houses=[9, 10],
        description="The 9th house is the house of law. Jupiter signifies justice. "
                    "Sun signifies authority. The 10th shows the judge/court.",
        category=SignificatorCategory.LEGAL
    ),
    "lawsuit": SignificatorDef(
        name="Lawsuit",
        planets=["Mars", "Saturn", "Jupiter"],
        houses=[1, 7, 9],
        description="The 1st house is the querent. The 7th is the opponent. "
                    "Mars signifies aggression. Saturn signifies delay. Jupiter is justice.",
        category=SignificatorCategory.LEGAL
    ),
    
    # === HEALTH ===
    "health": SignificatorDef(
        name="Health",
        planets=["Sun", "Moon", "Saturn"],
        houses=[1, 6],
        description="The 1st house is the body. The 6th house is disease. "
                    "Saturn signifies chronic illness. Sun and Moon show vitality.",
        category=SignificatorCategory.HEALTH
    ),
    "disease": SignificatorDef(
        name="Disease",
        planets=["Mars", "Saturn", "Mercury"],
        houses=[6],
        description="The 6th house rules disease. Mars signifies acute conditions. "
                    "Saturn signifies chronic conditions. Mercury signifies nervous system.",
        category=SignificatorCategory.HEALTH
    ),
    
    # === DEATH ===
    "death": SignificatorDef(
        name="Death",
        planets=["Saturn", "Mars"],
        houses=[8],
        description="The 8th house is the house of death. Saturn signifies natural "
                    "death. Mars signifies violent death.",
        category=SignificatorCategory.DEATH
    ),
    "inheritance": SignificatorDef(
        name="Inheritance",
        planets=["Jupiter", "Venus"],
        houses=[8],
        description="The 8th house rules inheritance. Jupiter signifies the estate. "
                    "Venus signifies the benefactor's possessions.",
        category=SignificatorCategory.DEATH
    ),
    
    # === CRYPTO/FINANCIAL (Modern additions) ===
    "crypto": SignificatorDef(
        name="Cryptocurrency",
        planets=["Mercury", "Uranus"],
        houses=[3, 8],
        description="Cryptocurrency as digital exchange medium. Mercury rules "
                    "exchange. Uranus (modern) rules innovation. 3rd for communication tech.",
        category=SignificatorCategory.MONEY
    ),
    "stock": SignificatorDef(
        name="Stocks/Equities",
        planets=["Jupiter", "Venus"],
        houses=[5, 11],
        description="Stocks represent ownership in companies. Jupiter signifies "
                    "corporate growth. Venus signifies value. 5th for speculation.",
        category=SignificatorCategory.MONEY
    ),
    "trading": SignificatorDef(
        name="Trading",
        planets=["Mercury", "Mars"],
        houses=[3, 5],
        description="Active trading and speculation. Mercury for quick decisions. "
                    "Mars for aggressive action. 5th house for speculation.",
        category=SignificatorCategory.MONEY
    ),
}


class SignificatorRegistry:
    """Registry for looking up significators."""
    
    @staticmethod
    def get(name: str) -> Optional[SignificatorDef]:
        """Get a significator definition by name."""
        return SIGNIFICATOR_REGISTRY.get(name.lower())
    
    @staticmethod
    def get_by_category(category: SignificatorCategory) -> List[SignificatorDef]:
        """Get all significators in a category."""
        return [s for s in SIGNIFICATOR_REGISTRY.values() 
                if s.category == category]
    
    @staticmethod
    def get_financial() -> List[SignificatorDef]:
        """Get all financial-related significators."""
        return SignificatorRegistry.get_by_category(SignificatorCategory.MONEY)
    
    @staticmethod
    def search(query: str) -> List[SignificatorDef]:
        """Search significators by name or description."""
        query_lower = query.lower()
        results = []
        for sig in SIGNIFICATOR_REGISTRY.values():
            if (query_lower in sig.name.lower() or 
                query_lower in sig.description.lower()):
                results.append(sig)
        return results
