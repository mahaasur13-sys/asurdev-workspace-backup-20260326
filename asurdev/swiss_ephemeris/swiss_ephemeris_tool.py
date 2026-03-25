"""
Swiss Ephemeris Tool — Main LangGraph Tool
============================================
Module-level tool that wraps all ephemeris calculations.
ENFORCEMENT: All agents MUST call this tool before any astrological work.
"""

import swisseph as swe
from datetime import datetime
from typing import Dict, Any, Tuple
from functools import lru_cache
from pathlib import Path

# =============================================================================
# SETUP
# =============================================================================

EPHE_PATH = Path(__file__).parent / "ephe"
swe.set_ephe_path(str(EPHE_PATH))

# =============================================================================
# CONSTANTS
# =============================================================================

AYANAMSA_MAP = {
    "lahiri": swe.SIDM_LAHIRI,
    "raman": swe.SIDM_RAMAN,
    "krishnamurti": swe.SIDM_KRISHNAMURTI,
    "fagan_bradley": swe.SIDM_FAGAN_BRADLEY,
    "surya_siddhanta": swe.SIDM_SURYASIDDHANTA,
    "true_citra": swe.SIDM_TRUE_CITRA,
    "true_revati": swe.SIDM_TRUE_REVATI,
    "tropical": 0,
}

HOUSE_MAP = {
    "P": b"P", "K": b"K", "W": b"W", "E": b"E", "R": b"R",
    "O": b"O", "C": b"C", "T": b"T", "A": b"A", "H": b"H", "G": b"G",
}

PLANETS = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
    "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN, "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO, "North_Node": swe.TRUE_NODE,
}

PLANET_LIST = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]

ZODIAC_SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]


# =============================================================================
# INPUT SCHEMA (for LangChain/LangGraph)
# =============================================================================

class SwissEphemerisInput:
    """Input schema for Swiss Ephemeris tool."""
    
    def __init__(
        self,
        date: str = "2026-03-22",
        time: str = "10:00:00",
        lat: float = 55.7558,
        lon: float = 37.6173,
        ayanamsa: str = "lahiri",
        zodiac: str = "sidereal",
        house_system: str = "W",
        compute_houses: bool = True,
        compute_panchanga: bool = True,
        compute_choghadiya: bool = True,
        compute_ashtakavarga: bool = False,
    ):
        self.date = date
        self.time = time
        self.lat = lat
        self.lon = lon
        self.ayanamsa = ayanamsa
        self.zodiac = zodiac
        self.house_system = house_system
        self.compute_houses = compute_houses
        self.compute_panchanga = compute_panchanga
        self.compute_choghadiya = compute_choghadiya
        self.compute_ashtakavarga = compute_ashtakavarga


# =============================================================================
# HELPERS
# =============================================================================

def get_jd(date: str, time: str) -> float:
    dt = datetime.fromisoformat(f"{date}T{time}")
    return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60 + dt.second/3600)


@lru_cache(maxsize=2048)
def _jd_to_hms(jd_val: float) -> str:
    d = swe.revjul(jd_val)
    hours = d[3]
    h = int(hours)
    m = int((hours - h) * 60)
    s = int(((hours - h) * 60 - m) * 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def get_ayanamsa_value(jd_ut: float, ayanamsa_id: int) -> float:
    """Get ayanamsa for JD (ET). Must call set_sid_mode first."""
    jd_et = jd_ut + swe.deltat(jd_ut)
    swe.set_sid_mode(ayanamsa_id)
    return swe.get_ayanamsa_ex(jd_et, 0)[1]


def format_position(lon: float) -> Dict[str, Any]:
    """
    Convert raw longitude (0-360°) to UI-friendly format.
    27 nakshatras, each = 360/27 = 40/3 = 13.333...°
    Formula: nak_idx = int(lon / (360/27)) % 27
    """
    lon = lon % 360
    NAKSHAKTRA_WIDTH = 360.0 / 27  # 13.333...° per nakshatra
    sign_idx = int(lon // 30)
    deg_in_sign = lon % 30
    deg = int(deg_in_sign)
    minutes = int((deg_in_sign - deg) * 60)
    nak_idx = int(lon / NAKSHAKTRA_WIDTH) % 27
    nak_pada = int((lon % NAKSHAKTRA_WIDTH) / (NAKSHAKTRA_WIDTH / 4)) % 4 + 1
    return {
        "degree": f"{deg}°{minutes:02d}'",
        "sign": ZODIAC_SIGNS[sign_idx],
        "sign_idx": sign_idx,
        "lon": round(lon, 4),
        "nakshatra": NAKSHATRAS[nak_idx],
        "nakshatra_idx": nak_idx,
        "nakshatra_pada": nak_pada,
    }


def get_sunrise_sunset(date: str, lat: float, lon: float) -> Tuple[float, float]:
    parts = [int(x) for x in date.split("-")]
    jd = swe.julday(parts[0], parts[1], parts[2], 12.0)
    try:
        return swe.sunrise(jd, lat, lon), swe.sunset(jd, lat, lon)
    except Exception:
        base_jd = swe.julday(parts[0], parts[1], parts[2], 0)
        return base_jd + 0.25, base_jd + 0.75


# =============================================================================
# POSITION CALCULATIONS
# =============================================================================

def calculate_positions(jd_ut: float, flags: int, is_sidereal: bool, ayanamsa_value: float) -> Dict[str, Dict]:
    positions = {}
    for name, planet_id in PLANETS.items():
        if name == "South_Node":
            continue
        result = swe.calc(jd_ut, planet_id, flags)
        lon = result[0][0]
        lat = result[0][1]
        dist = result[0][2]
        speed = result[0][3]
        retro = speed < 0
        if is_sidereal:
            lon = (lon - ayanamsa_value) % 360  # sidereal = tropical - ayanamsa
        positions[name] = {
            "lon": round(lon, 6),
            "lat": round(lat, 6),
            "dist": round(dist, 6),
            "speed": round(speed, 6),
            "retro": retro,
        }
    # South Node = opposite Rahu
    if "North_Node" in positions:
        positions["South_Node"] = {
            "lon": round((positions["North_Node"]["lon"] + 180) % 360, 6),
            "lat": round(-positions["North_Node"]["lat"], 6),
            "dist": positions["North_Node"]["dist"],
            "speed": positions["North_Node"]["speed"],
            "retro": not positions["North_Node"]["retro"],
        }
    return positions


def assign_houses(positions: Dict, houses: Dict) -> Dict:
    cusps = [houses[str(i)] for i in range(1, 13)]
    asc = houses["asc"]
    for name, pos in positions.items():
        lon = pos["lon"]
        house = 1
        min_diff = 360
        for i in range(12):
            diff = (cusps[(i + 1) % 12] - cusps[i]) % 360
            point_diff = (lon - cusps[i]) % 360
            if point_diff < diff and point_diff < min_diff:
                min_diff = point_diff
                house = i + 1
        positions[name]["house"] = house
    positions["Lagna"] = {"lon": asc, "house": 1}
    return positions


def _format_positions_for_output(positions: Dict) -> Dict[str, Dict]:
    """Add degree/sign/nakshatra fields to positions for UI."""
    formatted = {}
    for name, pos in positions.items():
        formatted[name] = {**pos, **format_position(pos["lon"])}
    return formatted


# =============================================================================
# CACHED COMPUTE
# =============================================================================

@lru_cache(maxsize=1024)
def _cached_compute(
    date: str, time: str, lat: float, lon: float,
    ayanamsa: str, zodiac: str, house_system: str,
    compute_houses: bool, compute_panchanga: bool,
    compute_choghadiya: bool, compute_ashtakavarga: bool,
) -> Dict:
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    is_sidereal = zodiac == "sidereal" and ayanamsa != "tropical"
    ayanamsa_id = AYANAMSA_MAP.get(ayanamsa.lower(), swe.SIDM_LAHIRI)
    hsys = HOUSE_MAP.get(house_system, b"W")
    jd_ut = get_jd(date, time)
    ayanamsa_value = get_ayanamsa_value(jd_ut, ayanamsa_id)
    swe.set_sid_mode(ayanamsa_id)  # FIX: Set sidereal mode before calc
    positions = calculate_positions(jd_ut, flags, is_sidereal, ayanamsa_value)
    houses = None
    if compute_houses:
        try:
            cusps, ascmc = swe.houses(jd_ut, lat, lon, hsys)
            houses = {"asc": round(ascmc[0], 6), "mc": round(ascmc[1], 6),
                      "armc": round(ascmc[2], 6), "vertex": round(ascmc[3], 6)}
            for i, cusp in enumerate(cusps[:12], 1):
                houses[str(i)] = round(cusp, 6)
            positions = assign_houses(positions, houses)
        except Exception as e:
            houses = {"error": str(e)}
    sunrise_jd, sunset_jd = get_sunrise_sunset(date, lat, lon)
    d = swe.revjul(sunrise_jd)
    dt = datetime(int(d[0]), int(d[1]), int(d[2]))
    weekday_idx = dt.weekday()
    result = {
        "jd_ut": round(jd_ut, 6),
        "ayanamsa_value": round(ayanamsa_value, 6),
        "date": date, "time": time, "lat": lat, "lon": lon,
        "positions": positions,
        "positions_formatted": _format_positions_for_output(positions),
        "houses": houses,
        "sunrise": _jd_to_hms(sunrise_jd),
        "sunrise_jd": sunrise_jd,
        "sunset": _jd_to_hms(sunset_jd),
        "sunset_jd": sunset_jd,
        "weekday": weekday_idx,
    }
    if compute_panchanga:
        from .panchanga_calculator import calculate_panchanga
        result["panchanga"] = calculate_panchanga(
            jd_ut, positions.get("Sun", {}).get("lon", 0),
            positions.get("Moon", {}).get("lon", 0),
            sunrise_jd, sunset_jd, weekday_idx
        )
    if compute_choghadiya:
        from .choghadiya_calculator import calculate_choghadiya, get_current_choghadiya
        result["choghadiya"] = calculate_choghadiya(sunrise_jd, sunset_jd, weekday_idx)
        result["current_choghadiya"] = get_current_choghadiya(jd_ut, sunrise_jd, sunset_jd, weekday_idx)
    if compute_ashtakavarga and houses:
        from .ashtakavarga_calculator import calculate_ashtakavarga, interpret_ashtakavarga_for_trading
        house_map = tuple(positions.get(p, {}).get("house", 1) for p in PLANET_LIST) + (positions.get("Lagna", {}).get("house", 1),)
        result["ashtakavarga"] = calculate_ashtakavarga(house_map)
        result["ashtakavarga_trading"] = interpret_ashtakavarga_for_trading(result["ashtakavarga"])
    return result


# =============================================================================
# MAIN TOOL
# =============================================================================

def swiss_ephemeris(date: str, time: str, lat: float, lon: float, **kwargs) -> Dict:
    return _cached_compute(
        date=date, time=time, lat=round(lat, 6), lon=round(lon, 6),
        ayanamsa=kwargs.get("ayanamsa", "lahiri"),
        zodiac=kwargs.get("zodiac", "sidereal"),
        house_system=kwargs.get("house_system", "W"),
        compute_houses=kwargs.get("compute_houses", True),
        compute_panchanga=kwargs.get("compute_panchanga", True),
        compute_choghadiya=kwargs.get("compute_choghadiya", True),
        compute_ashtakavarga=kwargs.get("compute_ashtakavarga", False),
    )


if __name__ == "__main__":
    import json
    result = swiss_ephemeris(
        date="2026-03-22", time="10:00:00", lat=55.7558, lon=37.6173,
        ayanamsa="lahiri", zodiac="sidereal", house_system="W",
        compute_houses=True, compute_panchanga=True,
        compute_choghadiya=True, compute_ashtakavarga=True,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
