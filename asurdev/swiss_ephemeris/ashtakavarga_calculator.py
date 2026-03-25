"""
Ashtakavarga Calculator — Sarvashtakavarga & Bhinnashtakavarga
================================================================
Optimized calculation using Parashara's standard tables.
Uses only house numbers from Swiss Ephemeris, fully cached.
"""

from functools import lru_cache
from typing import Dict, Tuple, List

# =============================================================================
# BHINNASHTAKAVARGA TABLES (Parashara)
# =============================================================================
# Each table shows relative houses (from reference planet) where
# each contributor planet gives a "bindu" (point).

BAV_TABLES = {
    "Sun": {
        "Sun":    [1, 2, 4, 7, 8, 9, 10, 11],
        "Moon":   [3, 6, 10, 11],
        "Mars":   [1, 2, 4, 7, 8, 9, 10, 11],
        "Mercury":[3, 5, 6, 9, 10, 11, 12],
        "Jupiter":[5, 6, 9, 11],
        "Venus":  [6, 7, 12],
        "Saturn": [1, 2, 4, 7, 8, 9, 10, 11],
        "Lagna":  [3, 4, 6, 10, 11, 12],
    },
    "Moon": {
        "Sun":    [3, 6, 7, 8, 10, 11],
        "Moon":   [1, 3, 6, 7, 10, 11],
        "Mars":   [2, 3, 5, 6, 9, 10, 11],
        "Mercury":[1, 3, 4, 5, 7, 8, 10, 11],
        "Jupiter":[1, 4, 7, 8, 10, 11, 12],
        "Venus":  [3, 4, 5, 7, 9, 10, 11],
        "Saturn": [3, 5, 6, 11],
        "Lagna":  [3, 6, 10, 11],
    },
    "Mars": {
        "Sun":    [1, 2, 4, 7, 8, 9, 10, 11],
        "Moon":   [3, 6, 10, 11],
        "Mars":   [1, 2, 4, 7, 8, 9, 10, 11],
        "Mercury":[3, 5, 6, 9, 10, 11, 12],
        "Jupiter":[5, 6, 9, 11],
        "Venus":  [6, 7, 12],
        "Saturn": [1, 2, 4, 7, 8, 9, 10, 11],
        "Lagna":  [3, 4, 6, 10, 11, 12],
    },
    "Mercury": {
        "Sun":    [3, 6, 10, 11],
        "Moon":   [3, 6, 7, 8, 10, 11],
        "Mars":   [2, 3, 5, 6, 9, 10, 11],
        "Mercury":[1, 3, 4, 5, 7, 8, 10, 11],
        "Jupiter":[1, 4, 7, 8, 10, 11, 12],
        "Venus":  [3, 4, 5, 7, 9, 10, 11],
        "Saturn": [3, 5, 6, 11],
        "Lagna":  [3, 6, 10, 11],
    },
    "Jupiter": {
        "Sun":    [5, 9, 10, 11],
        "Moon":   [1, 3, 6, 7, 10, 11],
        "Mars":   [3, 5, 6, 9, 10, 11],
        "Mercury":[3, 5, 6, 9, 10, 11, 12],
        "Jupiter":[1, 2, 4, 7, 8, 9, 10, 11],
        "Venus":  [3, 6, 9, 10, 11],
        "Saturn": [5, 9, 10, 11],
        "Lagna":  [3, 6, 9, 10, 11],
    },
    "Venus": {
        "Sun":    [3, 6, 10, 11],
        "Moon":   [3, 6, 7, 8, 10, 11],
        "Mars":   [2, 3, 5, 6, 9, 10, 11],
        "Mercury":[1, 3, 4, 5, 7, 8, 10, 11],
        "Jupiter":[1, 4, 7, 8, 10, 11, 12],
        "Venus":  [3, 4, 5, 7, 9, 10, 11],
        "Saturn": [3, 5, 6, 11],
        "Lagna":  [3, 6, 10, 11],
    },
    "Saturn": {
        "Sun":    [1, 2, 4, 7, 8, 9, 10, 11],
        "Moon":   [3, 6, 10, 11],
        "Mars":   [1, 2, 4, 7, 8, 9, 10, 11],
        "Mercury":[3, 5, 6, 9, 10, 11, 12],
        "Jupiter":[5, 6, 9, 11],
        "Venus":  [6, 7, 12],
        "Saturn": [1, 2, 4, 7, 8, 9, 10, 11],
        "Lagna":  [3, 4, 6, 10, 11, 12],
    },
}

PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]


# =============================================================================
# MAIN CALCULATION (cached)
# =============================================================================

@lru_cache(maxsize=1024)
def calculate_ashtakavarga(house_map: Tuple[int, ...]) -> Dict:
    """
    Calculate Bhinnashtakavarga and Sarvashtakavarga.
    
    Args:
        house_map: Tuple of 8 house numbers in order:
                   (Sun_house, Moon_house, Mars_house, Mercury_house,
                    Jupiter_house, Venus_house, Saturn_house, Lagna_house)
    
    Returns:
        Dict with bhinnashtakavarga, sarvashtakavarga, total_bindus,
        benefic_receptors, malefic_receptors
    """
    # Convert tuple to dict for easier access
    house_dict = dict(zip(PLANETS + ["Lagna"], house_map))
    
    # Initialize Bhinnashtakavarga (BAV)
    bav = {}
    
    # Sarvashtakavarga accumulator (all planets contribute to houses 1-12)
    sav = [0] * 13  # index 0 unused, indices 1-12 for houses
    
    # Calculate BAV for each reference planet
    for ref_planet in PLANETS:
        ref_house = house_dict[ref_planet]
        points = [0] * 13
        
        # Each contributor planet's relative house is checked
        for contrib_planet, rel_houses in BAV_TABLES[ref_planet].items():
            if contrib_planet not in house_dict:
                continue
            
            contrib_house = house_dict[contrib_planet]
            
            # Relative house of contributor from reference
            rel = ((contrib_house - ref_house + 12) % 12) + 1
            
            # If relative house is in the table for this contributor
            if rel in rel_houses:
                # Add bindu to all houses that have same relative position
                for h in range(1, 13):
                    h_rel = ((h - ref_house + 12) % 12) + 1
                    if h_rel == rel:
                        points[h] += 1
                        sav[h] += 1  # Accumulate for Sarvashtakavarga
        
        # Store BAV for this reference planet
        bav[ref_planet] = {
            f"house_{h}": points[h] for h in range(1, 13)
        }
        bav[ref_planet]["total"] = sum(points[1:])
    
    # Calculate Sarvashtakavarga
    sarvashtakavarga = {
        f"house_{h}": sav[h] for h in range(1, 13)
    }
    sarvashtakavarga["total"] = sum(sav[1:])
    
    # Identify benefic/malefic receptors
    benefic_receptors = [h for h in range(1, 13) if sav[h] >= 4]
    malefic_receptors = [h for h in range(1, 13) if sav[h] <= 2]
    
    # Best houses for trading (high Sav)
    best_houses = sorted(range(1, 13), key=lambda h: sav[h], reverse=True)[:3]
    
    return {
        "bhinnashtakavarga": bav,
        "sarvashtakavarga": sarvashtakavarga,
        "total_bindus": sum(sav[1:]),
        "max_bindus_per_house": max(sav[1:]),
        "benefic_receptors": benefic_receptors,
        "malefic_receptors": malefic_receptors,
        "best_houses_for_trading": best_houses,
        "house_scores": {f"house_{h}": sav[h] for h in range(1, 13)},
    }


def calculate_from_positions(positions: Dict) -> Dict:
    """
    Calculate Ashtakavarga from planet positions dict.
    
    Args:
        positions: Dict with planet names as keys and 'house' in values:
                   {"Sun": {"lon": ..., "house": 10}, ...}
    
    Returns:
        Ashtakavarga result
    """
    house_map = tuple(
        positions.get(p, {}).get("house", 1) for p in PLANETS
    ) + (positions.get("Lagna", {}).get("house", 1),)
    
    return calculate_ashtakavarga(house_map)


# =============================================================================
# HOUSE INTERPRETATION
# =============================================================================

HOUSE_INTERPRETATION = {
    1: {
        "name": "ASCENDANT / LAGNA",
        "themes": ["Self", "Physical Body", "First Impression"],
        "excellent": "Strong personality, good health, charisma",
        "good": "Healthy, confident, good first impression",
        "average": "Average vitality, normal appearance",
        "weak": "Health issues, lack of confidence",
        "poor": "Significant health challenges, weak presence"
    },
    2: {
        "name": "FINANCES / FAMILY",
        "themes": ["Wealth", "Family", "Speech"],
        "excellent": "Financial abundance, harmonious family, melodious voice",
        "good": "Stable finances, supportive family",
        "average": "Average finances, normal family life",
        "weak": "Financial struggles, family discord",
        "poor": "Poverty, speech impediments, family troubles"
    },
    3: {
        "name": "SIBLINGS / VALOR",
        "themes": ["Siblings", "Courage", "Efforts"],
        "excellent": "Strong siblings, brave, many endeavors succeed",
        "good": "Good sibling relationships, courageous",
        "average": "Average sibling bond, normal courage",
        "weak": "Sibling conflicts, cowardice",
        "poor": "Sibling loss, accidents, laziness"
    },
    4: {
        "name": "MOTHER / EMOTIONS",
        "themes": ["Mother", "Home", "Emotional Stability"],
        "excellent": "Blessed mother, emotional peace, property happiness",
        "good": "Good relationship with mother, comfortable home",
        "average": "Average maternal relationship, normal emotions",
        "weak": "Mother issues, emotional instability",
        "poor": "Mother's illness/death, no peace, property disputes"
    },
    5: {
        "name": "CHILDREN / CREATIVITY",
        "themes": ["Children", "Intelligence", "Love Affairs"],
        "excellent": "Many intelligent children, creative genius, spiritual wisdom",
        "good": "Good children, creative abilities",
        "average": "Average children, normal creativity",
        "weak": "Fewer children, average intelligence",
        "poor": "No children,智能化 issues, failed love affairs"
    },
    6: {
        "name": "ENEMIES / DISEASES",
        "themes": ["Enemies", "Diseases", "Debts"],
        "excellent": "No enemies, excellent health, victory over enemies",
        "good": "Weak enemies, good health",
        "average": "Manageable enemies, average health",
        "weak": "Enemies exist, health issues",
        "poor": "Powerful enemies, chronic diseases, debt"
    },
    7: {
        "name": "PARTNER / MARRIAGE",
        "themes": ["Spouse", "Partnerships", "Business"],
        "excellent": "Beautiful spouse, successful partnerships",
        "good": "Good spouse, supportive partnerships",
        "average": "Average spouse, normal partnerships",
        "weak": "Spouse issues, unstable partnerships",
        "poor": "Spouse illness/death, failed marriages, business losses"
    },
    8: {
        "name": "LIFESPAN / SECRETS",
        "themes": ["Longevity", "Secrets", "Inheritance"],
        "excellent": "Long life, hidden knowledge, inheritance",
        "good": "Good lifespan, secrets well-kept",
        "average": "Average lifespan, some secrets",
        "weak": "Health concerns, secrets revealed",
        "poor": "Short lifespan, chronic secrets, no inheritance"
    },
    9: {
        "name": "FORTUNE / SPIRITUALITY",
        "themes": ["Fortune", "Father", "Religion"],
        "excellent": "Great fortune, blessed father, spiritual elevation",
        "good": "Good fortune, religious/spiritual",
        "average": "Average luck, normal religious inclination",
        "weak": "Bad luck, father issues",
        "poor": "Misfortune, father's illness/death, irreligion"
    },
    10: {
        "name": "CAREER / REPUTATION",
        "themes": ["Career", "Status", "Power"],
        "excellent": "Top career, high status, authority",
        "good": "Good career, respected position",
        "average": "Average career, normal reputation",
        "weak": "Career struggles, average status",
        "poor": "Failed career, loss of reputation, humiliation"
    },
    11: {
        "name": "GAINS / FRIENDS",
        "themes": ["Gains", "Friends", "Amplitude"],
        "excellent": "Massive gains, noble friends, increased wealth",
        "good": "Good income, supportive friends",
        "average": "Average gains, normal friendships",
        "weak": "Limited gains, unreliable friends",
        "poor": "No gains, losses, false friends"
    },
    12: {
        "name": "EXPENSES / LIBERATION",
        "themes": ["Expenses", "Foreign", "Moksha"],
        "excellent": "Spiritual expenses, foreign travel, liberation",
        "good": "Controlled expenses, foreign connections",
        "average": "Average expenses, some foreign travel",
        "weak": "Excessive expenses, limited foreign travel",
        "poor": "Heavy losses, imprisonment, spiritual decline"
    },
}


def get_house_interpretation(house_num: int, bindus: int) -> Dict:
    """
    Get detailed interpretation for a house based on bindu count.
    
    Args:
        house_num: House number (1-12)
        bindus: Number of bindus (points) in that house
        
    Returns:
        Dict with interpretation details
    """
    if house_num not in HOUSE_INTERPRETATION:
        return {"error": "Invalid house number"}
    
    info = HOUSE_INTERPRETATION[house_num]
    
    if bindus >= 5:
        quality = "excellent"
        signal_modifier = "+20"
    elif bindus == 4:
        quality = "good"
        signal_modifier = "+10"
    elif bindus == 3:
        quality = "average"
        signal_modifier = "0"
    elif bindus == 2:
        quality = "weak"
        signal_modifier = "-10"
    else:
        quality = "poor"
        signal_modifier = "-20"
    
    return {
        "house": house_num,
        "house_name": info["name"],
        "themes": info["themes"],
        "bindus": bindus,
        "quality": quality,
        "interpretation": info[quality],
        "signal_modifier": signal_modifier,
        "for_trading": _get_trading_implication(house_num, bindus),
    }


def _get_trading_implication(house_num: int, bindus: int) -> str:
    """Get trading-specific implication for a house."""
    if house_num == 2:
        if bindus >= 4:
            return "Strong for storing wealth, accumulation trades"
        elif bindus <= 2:
            return "Weak for wealth accumulation, avoid saving trades"
    elif house_num == 3:
        if bindus >= 4:
            return "Good for quick trades, aggressive strategies"
        elif bindus <= 2:
            return "Weak for quick trades, avoid momentum strategies"
    elif house_num == 5:
        if bindus >= 4:
            return "Creative trading, speculative gains possible"
        elif bindus <= 2:
            return "Avoid speculation, conservative approach"
    elif house_num == 10:
        if bindus >= 4:
            return "Career influences market, good for position trading"
        elif bindus <= 2:
            return "Market career struggles, avoid long-term positions"
    elif house_num == 11:
        if bindus >= 4:
            return "Excellent for gains, profits, networking trades"
        elif bindus <= 2:
            return "Weak gains, avoid expansion trades"
    
    return "Neutral for trading"


def interpret_ashtakavarga_for_trading(ashtakavarga: Dict) -> Dict:
    """
    Generate trading signals from Ashtakavarga with full house interpretation.
    """
    sav = ashtakavarga["sarvashtakavarga"]
    best_houses = ashtakavarga["best_houses_for_trading"]
    
    # Calculate overall score (0-100)
    total_bindus = ashtakavarga["total_bindus"]
    max_possible = 8 * 12  # 7 planets + Lagna = 8 contributors
    overall_score = round((total_bindus / max_possible) * 100, 1)
    
    # Signal based on best houses
    if overall_score >= 70:
        signal = "BULLISH"
        confidence = min(85, 60 + overall_score - 70)
    elif overall_score >= 50:
        signal = "NEUTRAL"
        confidence = 50 + abs(overall_score - 60)
    else:
        signal = "BEARISH"
        confidence = min(75, 40 + (50 - overall_score))
    
    # House analysis with full interpretation
    house_analysis = {}
    for h in range(1, 13):
        score = sav[f"house_{h}"]
        if score >= 5:
            quality = "Excellent"
        elif score >= 4:
            quality = "Good"
        elif score >= 3:
            quality = "Average"
        elif score >= 2:
            quality = "Weak"
        else:
            quality = "Poor"
        
        house_analysis[f"House_{h}"] = {
            "bindus": score,
            "quality": quality,
            **get_house_interpretation(h, score)
        }
    
    return {
        "signal": signal,
        "confidence": round(confidence, 1),
        "overall_score": overall_score,
        "total_bindus": total_bindus,
        "best_houses": best_houses,
        "benefic_receptors": ashtakavarga["benefic_receptors"],
        "malefic_receptors": ashtakavarga["malefic_receptors"],
        "house_analysis": house_analysis,
    }
