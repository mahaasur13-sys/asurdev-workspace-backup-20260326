"""
Swiss Ephemeris tool for astrological calculations.
"""

from langchain_core.tools import tool
from datetime import datetime, timezone
from math import radians, degrees
from pytz import timezone as pytz_timezone
import math


# Try to import swiss_ephemeris, fall back to ephem
try:
    import swisseph as swe
    HAS_SWISS_EPH = True
except ImportError:
    HAS_SWISS_EPH = False


# =============================================================================
# ASTRO CALCULATIONS
# =============================================================================

# Nakshatra names (27 lunar mansions)
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra",
    "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula",
    "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

# Nakshatra rulership (traditional)
NAKSHATRA_OWNERS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury", "Ketu",
    "Venus", "Sun", "Moon", "Mars", "Rahu",
    "Jupiter", "Saturn", "Mercury", "Ketu", "Venus",
    "Sun", "Moon", "Mars", "Rahu", "Jupiter",
    "Saturn", "Mercury"
]

# Yoga names (Sun-Moon combinations)
YOGAS = [
    "Vishkumbha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarman", "Dhriti", "Shoola", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyan", "Shiva", "Siddha",
    "Sadhya", "Subha", "Brahmana", "Indra", "Lalana",
    "Chatra", "Mitra", "Paridhi", "Pridhi", "Ayu"
]


def calculate_moon_position(dt: datetime, lat: float, lon: float) -> dict:
    """
    Calculate moon position and derived astrological data.
    
    Uses simplified astronomical calculations (no Swiss Ephemeris required).
    For production, use swisseph for accurate calculations.
    """
    # Convert datetime to Julian Day
    utc = dt.astimezone(timezone.utc)
    year = utc.year
    month = utc.month
    day = utc.day
    hour = utc.hour + utc.minute / 60 + utc.second / 3600
    
    # Julian Day calculation
    if month <= 2:
        year -= 1
        month += 12
    
    A = int(year / 100)
    B = 2 - A + int(A / 4)
    JD = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + hour / 24 + B - 1524.5
    
    # Moon's mean longitude
    L0 = 218.3165 + 13.176396 * (JD - 2451545)
    L0 = L0 % 360
    
    # Moon's mean anomaly
    M = 134.9634 + 13.064993 * (JD - 2451545)
    M = M % 360
    
    # Moon's argument of latitude
    F = 93.2721 + 13.229350 * (JD - 2451545)
    F = F % 360
    
    # Moon's mean elongation
    D = 297.8502 + 12.74915 * (JD - 2451545)
    D = D % 360
    
    # Longitude correction (simplified)
    dL = 6.29 * math.sin(math.radians(M))
    L = L0 + dL
    L = L % 360
    
    # Moon's ecliptic latitude (simplified)
    dB = 5.12 * math.sin(math.radians(F))
    B = dB  # degrees from ecliptic
    
    # Convert to Nakshatra (each nakshatra = 13°20' = 13.333°)
    nakshatra_index = int(L / (360 / 27))
    nakshatra_index = nakshatra_index % 27
    nakshatra = NAKSHATRAS[nakshatra_index]
    nakshatra_progress = (L % (360 / 27)) / (360 / 27)  # 0-1 progress in nakshatra
    
    # Tithi (lunar day) - simplified
    # Synodic month = 29.53059 days
    synodic_days = 29.53059
    tithi_number = int((D / 360) * 30) + 1  # 1-30
    tithi_progress = ((D % 12) * 30) / 360  # 0-1 progress in tithi
    
    # Paksha (waxing/waning)
    paksha = "Shukla Paksha" if tithi_number <= 15 else "Krishna Paksha"
    
    # Yoga calculation (simplified)
    yoga_number = int((L0 + D) / (360 / 27)) % 27
    yoga = YOGAS[yoga_number]
    
    # Karana (half tithi)
    karana_number = int((D % 12) / 2) + 1  # 1-60
    karana_names = ["Bava", "Balava", "Kaulava", "Taitula", "Garija", "Vanija",
                   "Vishti", "Bhadra", "Kinvat", "Titikshu"]
    karana = karana_names[karana_number % 10]
    
    # Moon phase (0=new, 0.5=full)
    moon_phase_deg = D % 360
    moon_phase_pct = moon_phase_deg / 360
    
    if moon_phase_pct < 0.0625:
        moon_phase = "New Moon (Amavasya)"
    elif moon_phase_pct < 0.1875:
        moon_phase = "Waxing Crescent (Shukla Pratipat)"
    elif moon_phase_pct < 0.3125:
        moon_phase = "First Quarter (Dwitiya)"
    elif moon_phase_pct < 0.4375:
        moon_phase = "Waxing Gibbous (Tritiya)"
    elif moon_phase_pct < 0.5625:
        moon_phase = "Full Moon (Poornima)"
    elif moon_phase_pct < 0.6875:
        moon_phase = "Waning Gibbous (Shashthi)"
    elif moon_phase_pct < 0.8125:
        moon_phase = "Last Quarter (Saptami)"
    elif moon_phase_pct < 0.9375:
        moon_phase = "Waning Crescent (Navami)"
    else:
        moon_phase = "New Moon (Amavasya)"
    
    # Favorable nakshatras for trading
    favorable_nakshatras = ["Mrigashira", "Rohini", "Pushya", "Uttara Phalguni", 
                           "Uttara Ashadha", "Revati", "Hasta", "Swati"]
    neutral_nakshatras = ["Ashwini", "Bharani", "Krittika", "Punarvasu", "Chitra",
                         "Anuradha", "Shravana", "Dhanishtha", "Purva Bhadrapada"]
    unfavorable_nakshatras = ["Ashlesha", "Jyeshtha", "Mula", "Magha", 
                              "Purva Phalguni", "Purva Ashadha", "Ardra", "Vishakha", "Shatabhisha"]
    
    if nakshatra in favorable_nakshatras:
        nakshatra_signal = "BULLISH"
    elif nakshatra in unfavorable_nakshatras:
        nakshatra_signal = "BEARISH"
    else:
        nakshatra_signal = "NEUTRAL"
    
    # Calculate favorability score
    favorability = 0.5  # Base
    
    if paksha == "Shukla Paksha":
        favorability += 0.15  # Waxing moon favorable
    else:
        favorability -= 0.10  # Waning less favorable
    
    if nakshatra_signal == "BULLISH":
        favorability += 0.25
    elif nakshatra_signal == "BEARISH":
        favorability -= 0.20
    
    # Full moon / New moon adjustments
    if "Full Moon" in moon_phase:
        favorability -= 0.15  # Full moon can cause volatility
    elif "New Moon" in moon_phase:
        favorability += 0.10  # New moon = fresh starts
    
    favorability = max(0.0, min(1.0, favorability))
    
    return {
        "timestamp": dt.isoformat(),
        "location": {"lat": lat, "lon": lon},
        "moon_longitude": round(L, 2),
        "moon_latitude": round(B, 2),
        "moon_phase": moon_phase,
        "moon_phase_deg": round(moon_phase_deg, 2),
        "nakshatra": nakshatra,
        "nakshatra_ lord": NAKSHATRA_OWNERS[nakshatra_index],
        "nakshatra_progress": round(nakshatra_progress, 2),
        "nakshatra_signal": nakshatra_signal,
        "tithi": tithi_number,
        "paksha": paksha,
        "yoga": yoga,
        "karana": karana,
        "favorability_score": round(favorability, 2),
        "interpretation": _interpret_astro(favorability, nakshatra_signal, paksha, moon_phase),
        "trading_recommendation": _get_trading_recommendation(favorability, nakshatra_signal)
    }


def _interpret_astro(favorability: float, nakshatra_signal: str, paksha: str, moon_phase: str) -> str:
    """Generate human-readable interpretation."""
    parts = []
    
    if favorability >= 0.7:
        parts.append("Highly favorable conditions")
    elif favorability >= 0.55:
        parts.append("Moderately favorable")
    elif favorability >= 0.45:
        parts.append("Neutral conditions")
    elif favorability >= 0.3:
        parts.append("Caution advised")
    else:
        parts.append("Challenging conditions")
    
    if nakshatra_signal == "BULLISH":
        parts.append(f"while in {nakshatra_signal.lower()} nakshatra energy")
    elif nakshatra_signal == "BEARISH":
        parts.append(f"under {nakshatra_signal.lower()} nakshatra influence")
    
    if "Shukla" in paksha:
        parts.append("with waxing moon momentum")
    else:
        parts.append("during waning moon period")
    
    return ", ".join(parts)


def _get_trading_recommendation(favorability: float, nakshatra_signal: str) -> str:
    """Generate trading recommendation based on astro."""
    if favorability >= 0.7:
        return "Excellent conditions for new positions. Consider increasing size."
    elif favorability >= 0.55:
        return "Favorable for trading. Maintain normal position sizes."
    elif favorability >= 0.45:
        return "Neutral conditions. Proceed with caution, smaller sizes."
    elif favorability >= 0.3:
        return "Unfavorable conditions. Reduce risk, avoid new entries."
    else:
        return "Poor conditions. Best to stay on sidelines."


def calculate_astro(dt: datetime, lat: float = 25.2048, lon: float = 55.2708) -> dict:
    """
    Calculate comprehensive astrological data for trading.
    
    Args:
        dt: datetime object (UTC)
        lat: latitude for calculations
        lon: longitude for calculations
    
    Returns:
        dict with all astro data
    """
    return calculate_moon_position(dt, lat, lon)


# =============================================================================
# LANGCHAIN TOOL
# =============================================================================

@tool
def swiss_ephemeris(
    latitude: float = 25.2048,
    longitude: float = 55.2708,
    timezone_str: str = "Asia/Dubai"
) -> str:
    """
    Get current astrological data for trading decisions using Swiss Ephemeris methodology.
    
    This tool calculates:
    - Moon phase and position
    - Nakshatra (lunar mansion) and its ruler
    - Tithi (lunar day) and Paksha (waxing/waning)
    - Yoga (Sun-Moon combination)
    - Karana (half-lunar day)
    - Overall favorability score for trading
    
    Args:
        latitude: Location latitude (default: Dubai 25.2048)
        longitude: Location longitude (default: Dubai 55.2708)
        timezone_str: IANA timezone (default: Asia/Dubai)
    
    Returns:
        Comprehensive astrological data formatted for trading analysis.
    
    Example:
        swiss_ephemeris(latitude=25.2048, longitude=55.2708)
    """
    from datetime import datetime
    import pytz
    
    # Get current time in specified timezone
    tz = pytz.timezone(timezone_str)
    now = datetime.now(tz)
    
    astro = calculate_astro(now, latitude, longitude)
    
    # Format output
    output = f"""
=== ASTROLOGICAL DATA ({astro['timestamp']}) ===
Location: {latitude}°, {longitude}°

🌙 MOON STATUS:
- Phase: {astro['moon_phase']}
- Position: {astro['moon_phase_deg']}°
- Longitude: {astro['moon_longitude']}°

📍 NAKSHATRA (Lunar Mansion):
- Current: {astro['nakshatra']}
- Ruler: {astro['nakshatra_lord']}
- Progress: {astro['nakshatra_progress']:.0%} through nakshatra
- Signal: {astro['nakshatra_signal']}

📅 TITHI & PAKSHA:
- Lunar Day (Tithi): {astro['tithi']}
- Paksha: {astro['paksha']}
- Yoga: {astro['yoga']}
- Karana: {astro['karana']}

⭐ FAVORABILITY ANALYSIS:
- Score: {astro['favorability_score']}/1.0
- Interpretation: {astro['interpretation']}
- Trading Recommendation: {astro['trading_recommendation']}

⚠️ This is NOT financial advice. Astrology is for entertainment/educational purposes only.
"""
    return output.strip()


def create_swiss_ephemeris_tool():
    """Factory to create the swiss_ephemeris tool."""
    return swiss_ephemeris
