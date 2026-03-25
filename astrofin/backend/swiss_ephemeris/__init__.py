"""
Swiss Ephemeris wrapper for planetary positions.
"""

import math
from datetime import datetime
from typing import Dict, Any, Optional

# Check availability
try:
    import swisseph as swe
    HAS_SWISS_EPHEMERIS = True
    swe.set_ephe_path("/home/workspace/astrofin/swiss_ephemeris_data")
except ImportError:
    HAS_SWISS_EPHEMERIS = False


# Zodiac signs
ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Planets to calculate
PLANETS = [
    swe.SUN, swe.MOON, swe.MARS, swe.MERCURY,
    swe.JUPITER, swe.VENUS, swe.SATURN,
]


def _to_julian_day(dt: datetime) -> float:
    """Convert datetime to Julian Day."""
    a = (14 - dt.month) // 12
    y = dt.year + 4800 - a
    m = dt.month + 12 * a - 3
    jdn = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
    return jdn + (dt.hour - 12) / 24.0 + dt.minute / 1440.0 + dt.second / 86400.0


def get_current_positions(dt: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Get current planetary positions in zodiac signs.

    Returns dict with planet names as keys and:
      - longitude: degrees in zodiac (0-360)
      - sign: zodiac sign name
      - degrees_in_sign: degrees within the sign (0-30)
    """
    if dt is None:
        dt = datetime.now()

    if not HAS_SWISS_EPHEMERIS:
        return _fallback_positions(dt)

    jd = _to_julian_day(dt)
    positions = {}

    for planet in PLANETS:
        try:
            result = swe.calc_ut(jd, planet)
            longitude = result[0][0]

            sign_index = int(longitude // 30)
            degrees_in_sign = longitude % 30

            planet_name = swe.get_planet_name(planet).lower()

            positions[planet_name] = {
                "longitude": longitude,
                "sign": ZODIAC_SIGNS[sign_index],
                "degrees_in_sign": degrees_in_sign,
            }
        except Exception:
            continue

    # Add aspects
    positions["saturn_square_mars"] = _check_aspect(positions, 180, 90)

    return positions


def _check_aspect(positions: Dict, orb: float, exact: float) -> bool:
    """Check if two planets are within orb of exact aspect."""
    if "saturn" not in positions or "mars" not in positions:
        return False

    saturn_long = positions["saturn"]["longitude"]
    mars_long = positions["mars"]["longitude"]

    diff = abs(saturn_long - mars_long) % 360
    diff = min(diff, 360 - diff)

    return abs(diff - exact) <= orb


def _fallback_positions(dt: datetime) -> Dict[str, Any]:
    """Fallback when Swiss Ephemeris is not available."""
    # Simplified calculation based on date
    day_of_year = dt.timetuple().tm_yday

    # Very approximate planetary positions
    positions = {
        "sun": {
            "longitude": (day_of_year / 365.25) * 360,
            "sign": ZODIAC_SIGNS[int((day_of_year / 365.25) * 12) % 12],
            "degrees_in_sign": 0,
        },
        "moon": {
            "longitude": (day_of_year * 12 + dt.hour / 2) * 30 % 360,
            "sign": ZODIAC_SIGNS[int((day_of_year * 12) % 12)],
            "degrees_in_sign": 0,
        },
    }

    return positions


def get_planetary_forces(dt: Optional[datetime] = None) -> Dict[str, float]:
    """
    Get planetary force strengths for trading.
    Returns dict with planet names and force values (-1 to 1).
    """
    positions = get_current_positions(dt)
    forces = {}

    for planet, data in positions.items():
        if planet in ["saturn_square_mars"]:
            continue

        sign = data.get("sign", "")

        # Fire signs: strong momentum
        if sign in ["Aries", "Leo", "Sagittarius"]:
            forces[planet] = 0.5
        # Earth signs: stability
        elif sign in ["Taurus", "Virgo", "Capricorn"]:
            forces[planet] = 0.3
        # Water signs: sentiment
        elif sign in ["Cancer", "Scorpio", "Pisces"]:
            forces[planet] = 0.4
        # Air signs: volatility
        elif sign in ["Gemini", "Libra", "Aquarius"]:
            forces[planet] = 0.1
        else:
            forces[planet] = 0.0

    return forces
