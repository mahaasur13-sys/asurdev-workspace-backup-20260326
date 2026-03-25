"""
Swiss Ephemeris wrapper for planetary positions and Panchanga calculations.

All astronomical calculations MUST go through this module.
No hardcoded planet positions allowed.
"""
from __future__ import annotations

import swisseph as swe
from datetime import datetime
from typing import Any

# Set ephemeris path
swe.set_ephe_path("/home/workspace/astrofin/backend/ephe")

# Sign names (Western)
SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]

# Nakshatras (27 lunar mansions)
NAKSHATRAS = [
    "Aswini",
    "Bharani",
    "Krittika",
    "Rohini",
    "Mrigashirsha",
    "Ardra",
    "Punarvasu",
    "Pushya",
    "Aslesha",
    "Magha",
    "Purva Phalguni",
    "Uttara Phalguni",
    "Hasta",
    "Chitra",
    "Swati",
    "Vishakha",
    "Anuradha",
    "Jyeshtha",
    "Mula",
    "Purva Ashadha",
    "Uttara Ashadha",
    "Shravana",
    "Dhanishtha",
    "Shatabhisha",
    "Purva Bhadrapada",
    "Uttara Bhadrapada",
    "Revati",
]

# Days of week
VARAS = [
    "Sunday",
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
]


def _jd_to_datetime(jd: float) -> datetime:
    """Convert Julian Day to datetime."""
    year, month, day, hour = swe.jd_to_date(jd)
    hour_fraction = hour - int(hour)
    minute = int((hour_fraction) * 60)
    second = int(((hour_fraction) * 60 - minute) * 60)
    return datetime(year, month, day, int(hour), minute, second)


def _get_planet_sign(planet_idx: int, jd: float) -> tuple[str, float, float]:
    """Get planet position in sign and degrees."""
    pos = swe.calc_ut(jd, planet_idx, swe.FLG_SWIEPH | swe.FLG_SPEED)[0]
    longitude = pos[0] % 360
    sign_idx = int(longitude // 30)
    degrees = longitude % 30
    return SIGNS[sign_idx], degrees, longitude


def swiss_ephemeris(
    date: str,
    time: str,
    lat: float = 40.7128,
    lon: float = -74.0060,
    ayanamsa: str = "lahiri",
    compute_panchanga: bool = True,
) -> dict[str, Any]:
    """
    Get planetary positions and Panchanga data.

    Args:
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM:SS format
        lat: Latitude
        lon: Longitude
        ayanamsa: Ayanamsa calculation method
        compute_panchanga: Whether to compute Nakshatra, Yoga, etc.

    Returns:
        Dictionary with planetary positions and Panchanga data
    """
    dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S")
    jd = swe.utc_to_jd(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, 1)[0]

    # Get planetary positions
    planets: dict[str, dict[str, Any]] = {}
    planet_names = {
        swe.SUN: "Sun",
        swe.MOON: "Moon",
        swe.MARS: "Mars",
        swe.MERCURY: "Mercury",
        swe.JUPITER: "Jupiter",
        swe.VENUS: "Venus",
        swe.SATURN: "Saturn",
        swe.TRUE_NODE: "Rahu",
    }

    for idx, name in planet_names.items():
        sign, degrees, longitude = _get_planet_sign(idx, jd)
        planets[name.lower()] = {
            "sign": sign,
            "degrees": round(degrees, 2),
            "longitude": round(longitude, 2),
        }

    result: dict[str, Any] = {
        "planets": planets,
        "datetime": f"{date} {time}",
        "jd": jd,
    }

    if compute_panchanga:
        # Calculate Nakshatra
        moon_long = planets["moon"]["longitude"]
        nakshatra_idx = int(moon_long * 27 / 360) % 27
        nakshatra_deg = (moon_long * 27 / 360) % 27 - nakshatra_idx
        nakshatra = NAKSHATRAS[nakshatra_idx]

        # Calculate Yoga
        sun_long = planets["sun"]["longitude"]
        yoga_idx = int((sun_long + moon_long) * 27 / 360) % 27
        yogas = [
            "Vishkumbha", "Preeti", "Aayushman", "Saubhagya", "Shobhana",
            "Atiganda", "Sukarma", "Dhruti", "Shoola", "Ganda",
            "Bhruti", "Shaubhagya", "Shobhana", "Amrita", "Chitra",
            "Siddha", "Vyatipata", "Variyan", "Parigha", "Shiva",
            "Siddha", "Sadhya", "Shubha", "Brahmagupte", "Indigupte",
        ]
        yoga = yogas[yoga_idx]

        # Day of week
        day_idx = int(jd + 1.5) % 7
        vara = VARAS[day_idx]

        # Tithi
        tithi_idx = int((moon_long - sun_long) // 12) % 15
        tithis = [
            "Shukla Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami",
            "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
            "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi", "Poornima",
        ]
        purnimanta_tithi = tithis[tithi_idx] if moon_long > sun_long else tithis[(tithi_idx + 1) % 15]

        result["panchanga"] = {
            "nakshatra": nakshatra,
            "nakshatra_pada": int(nakshatra_deg * 4) + 1,
            "yoga": yoga,
            "vara": vara,
            "tithi": purnimanta_tithi,
            "yoga_category": (
                "Auspicious" if yoga in ["Shobhana", "Amrita", "Siddha", "Shubha"]
                else "Inauspicious" if yoga in ["Atiganda", "Ganda", "Shoola", "Vyatipata"]
                else "Neutral"
            ),
        }

    return result
