"""
Choghadiya Calculator — Vedic Time Periods
=============================================
Full day + night Choghadiya with correct indices.
Day: 06:00-18:00, Night: 18:00-06:00 next day.
Each Choghadiya = day_duration / 8 or night_duration / 8.
"""

from functools import lru_cache
from typing import Dict, List

# =============================================================================
# CONSTANTS
# =============================================================================

CHOGHADIYA_CYCLE = ["Udveg", "Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog"]

# GOOD types for trading
GOOD_TYPES = {"Amrit", "Shubh", "Labh", "Char"}
NEUTRAL_TYPES = {"Udveg"}
BAD_TYPES = {"Kaal", "Rog"}

# Day start index by weekday (0=Sunday)
DAY_START_IDX = {
    0: 0,  # Sunday: Udveg
    1: 3,  # Monday: Amrit
    2: 6,  # Tuesday: Rog
    3: 2,  # Wednesday: Labh
    4: 5,  # Thursday: Shubh
    5: 1,  # Friday: Char
    6: 4,  # Saturday: Kaal
}

# Night start index by weekday
NIGHT_START_IDX = {
    0: 5,  # Friday's Char (before Saturday)
    1: 6,  # Saturday's Rog
    2: 0,  # Sunday's Udveg
    3: 1,  # Monday's Char
    4: 2,  # Tuesday's Labh
    5: 4,  # Thursday's Kaal
    6: 3,  # Friday's Amrit
}

# Choghadiya quality descriptions
CHOGHADIYA_QUALITY = {
    "Udveg": "Communication, leadership, government work",
    "Char": "Movement, travel, trade,灵活",
    "Labh": "Profit, gain, business, investment",
    "Amrit": "All auspicious works, best for trading",
    "Kaal": "Avoid new ventures, best for routine",
    "Shubh": "Good deeds, ceremonies, starting projects",
    "Rog": "Health issues, conflicts, avoid important work",
}


# =============================================================================
# HELPER (cached)
# =============================================================================

@lru_cache(maxsize=1024)
def _jd_to_hms(jd_val: float) -> str:
    """Convert Julian Day to HH:MM:SS string."""
    import swisseph as swe
    d = swe.revjul(jd_val)
    hours = d[3]
    h = int(hours)
    m = int((hours - h) * 60)
    s = int(((hours - h) * 60 - m) * 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


# =============================================================================
# MAIN CALCULATION (cached)
# =============================================================================

@lru_cache(maxsize=512)
def calculate_choghadiya(
    sunrise_jd: float,
    sunset_jd: float,
    weekday_idx: int
) -> Dict:
    """
    Calculate complete Choghadiya for day and night.
    
    Args:
        sunrise_jd: Julian Day of sunrise
        sunset_jd: Julian Day of sunset
        weekday_idx: 0=Sunday, 1=Monday, ... 6=Saturday
    
    Returns:
        Dict with day_parts (8) and night_parts (8)
    """
    # Duration of day and night in Julian days
    day_dur = sunset_jd - sunrise_jd
    night_dur = (sunrise_jd + 1.0) - sunset_jd  # Next sunrise - sunset
    
    # Each Choghadiya = 1/8 of day or night
    day_part = day_dur / 8.0
    night_part = night_dur / 8.0
    
    day_start_idx = DAY_START_IDX.get(weekday_idx % 7, 0)
    night_start_idx = NIGHT_START_IDX.get(weekday_idx % 7, 0)
    
    def generate_parts(
        start_jd: float,
        part_dur: float,
        start_idx: int,
        is_day: bool
    ) -> List[Dict]:
        """Generate 8 Choghadiya parts."""
        parts = []
        current = start_jd
        for i in range(8):
            typ = CHOGHADIYA_CYCLE[(start_idx + i) % 7]
            parts.append({
                "period": i + 1,
                "type": typ,
                "start": _jd_to_hms(current),
                "start_jd": current,
                "end": _jd_to_hms(current + part_dur),
                "end_jd": current + part_dur,
                "quality": CHOGHADIYA_QUALITY.get(typ, ""),
                "auspicious": typ in GOOD_TYPES,
                "is_day": is_day,
            })
            current += part_dur
        return parts
    
    return {
        "day_parts": generate_parts(sunrise_jd, day_part, day_start_idx, True),
        "night_parts": generate_parts(sunset_jd, night_part, night_start_idx, False),
        "day_duration_hours": round(day_dur * 24, 2),
        "night_duration_hours": round(night_dur * 24, 2),
        "sunrise": _jd_to_hms(sunrise_jd),
        "sunset": _jd_to_hms(sunset_jd),
    }


def get_current_choghadiya(
    jd: float,
    sunrise_jd: float,
    sunset_jd: float,
    weekday_idx: int
) -> Dict:
    """
    Get the current Choghadiya period for a given JD.
    
    Returns the specific period (day or night) that contains jd.
    """
    choghadiya = calculate_choghadiya(sunrise_jd, sunset_jd, weekday_idx)
    
    # Check day parts
    for period in choghadiya["day_parts"]:
        if period["start_jd"] <= jd <= period["end_jd"]:
            return period
    
    # Check night parts
    for period in choghadiya["night_parts"]:
        if period["start_jd"] <= jd <= period["end_jd"]:
            return period
    
    # Fallback to first day period
    return choghadiya["day_parts"][0]


def get_best_choghadiya_periods(
    sunrise_jd: float,
    sunset_jd: float,
    weekday_idx: int,
    limit: int = 3
) -> List[Dict]:
    """Get the best auspicious Choghadiya periods."""
    choghadiya = calculate_choghadiya(sunrise_jd, sunset_jd, weekday_idx)
    
    all_parts = choghadiya["day_parts"] + choghadiya["night_parts"]
    auspicious = [p for p in all_parts if p["auspicious"]]
    
    # Sort by type priority: Amrit > Shubh > Labh > Char
    priority = {"Amrit": 0, "Shubh": 1, "Labh": 2, "Char": 3}
    auspicious.sort(key=lambda x: priority.get(x["type"], 99))
    
    return auspicious[:limit]


# =============================================================================
# MUHURTA SCORING (for trading)
# =============================================================================

CHOGHADIYA_TRADING_SCORES = {
    "Amrit": 100,
    "Shubh": 75,
    "Labh": 80,
    "Char": 70,
    "Udveg": 50,
    "Kaal": 20,
    "Rog": 15,
}


@lru_cache(maxsize=128)
def get_choghadiya_trading_score(choghadiya_type: str) -> int:
    """Get trading score for a Choghadiya type."""
    return CHOGHADIYA_TRADING_SCORES.get(choghadiya_type, 50)
