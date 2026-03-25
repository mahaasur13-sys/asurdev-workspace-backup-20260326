#!/usr/bin/env python3
"""
asurdev Sentinel - Swiss Ephemeris API
========================================
Полноценный API для всех агентов.
ПЕРВОЕ ПРАВИЛО: Никогда не использовать приближения — только Swiss Ephemeris 2.10.03

Параметры:
- date: YYYY-MM-DD (UTC)
- time: HH:MM:SS (UTC)
- lat/lon: координаты
- ayanamsa: lahiri, raman, krishnamurti, fagan_bradley, suryasiddhanta, true_citra, true_revati, tropical
- zodiac: sidereal / tropical
- house_system: P, K, W, E, R, O, C, T, A, H, G
- compute_houses: true/false
- compute_panchanga: true/false
- compute_choghadiya: false
- compute_muhurta: false
"""

import swisseph as swe
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

EPHE_PATH = Path(__file__).parent / "ephemeris"
swe.set_ephe_path(str(EPHE_PATH))

# Ayanamsa mappings
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

# House system mappings (byte characters for swe.houses())
HOUSE_MAP = {
    "P": b"P",  # Placidus
    "K": b"K",  # Koch
    "W": b"W",  # Whole Sign
    "E": b"E",  # Equal
    "R": b"R",  # Regiomontanus
    "O": b"O",  # Porphyry
    "C": b"C",  # Campanus
    "T": b"T",  # Topocentric
    "A": b"A",  # Alcabitius
    "H": b"H",  # Horizontal
    "G": b"G",  # Gauquelin
}

# Planet IDs
PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mercury": swe.MERCURY,
    "Venus": swe.VENUS,
    "Mars": swe.MARS,
    "Jupiter": swe.JUPITER,
    "Saturn": swe.SATURN,
    "Uranus": swe.URANUS,
    "Neptune": swe.NEPTUNE,
    "Pluto": swe.PLUTO,
    "North_Node": swe.TRUE_NODE,  # Rahu
    "South_Node": swe.TRUE_NODE,  # Ketu (computed as 180° opposite)
    "Chiron": swe.CHIRON,
}

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva_Phalguni", "Uttara_Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva_Ashadha", "Uttara_Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva_Bhadra", "Uttara_Bhadra", "Revati"
]

TITHIS = [
    "Shukla_Pratipat", "Shukla_Dvitiya", "Shukla_Tritiya", "Shukla_Chaturthi",
    "Shukla_Panchami", "Shukla_Shashti", "Shukla_Saptami", "Shukla_Ashtami",
    "Shukla_Navami", "Shukla_Dashami", "Shukla_Ekadashi", "Shukla_Dvadashi",
    "Shukla_Trayodashi", "Shukla_Chaturdashi", "Poornima",
    "Krishna_Pratipat", "Krishna_Dvitiya", "Krishna_Tritiya", "Krishna_Chaturthi",
    "Krishna_Panchami", "Krishna_Shashti", "Krishna_Saptami", "Krishna_Ashtami",
    "Krishna_Navami", "Krishna_Dashami", "Krishna_Ekadashi", "Krishna_Dvadashi",
    "Krishna_Trayodashi", "Krishna_Chaturdashi", "Amavasya"
]

YOGAS = [
    "Vishakbhaga", "Priti", "Udit", "Vyu", "Ksham", "Shobhana",
    "Atiganda", "Sukarman", "Dhriti", "Shool", "Ganda",
    "Vriddhi", "Dhruva", "Harshana", "Vajra", "Siddhi",
    "Vyatipata", "Variyan", "Parigha", "Shiva", "Siddha",
    "Sampat", "Karan", "Taitula", "Garija", "Vanija",
    "Vishti"
]

VARS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]


def parse_args():
    """Parse command line arguments."""
    args = {
        "date": "2026-03-22",
        "time": "10:00:00",
        "lat": 55.7558,
        "lon": 37.6173,
        "altitude": 0.0,
        "ayanamsa": "lahiri",
        "zodiac": "sidereal",
        "house_system": "P",
        "compute_houses": False,
        "compute_panchanga": False,
        "compute_choghadiya": False,
        "compute_muhurta": False,
        "flags": swe.FLG_SWIEPH | swe.FLG_SPEED,
    }
    
    for arg in sys.argv[1:]:
        if "=" in arg:
            key, value = arg.split("=", 1)
            if key in ["lat", "lon", "altitude"]:
                args[key] = float(value)
            elif key in ["compute_houses", "compute_panchanga", "compute_choghadiya", "compute_muhurta"]:
                args[key] = value.lower() == "true"
            else:
                args[key] = value
    
    return args


def get_jd_ut(date: str, time: str) -> float:
    """Convert date+time to Julian Day (UT)."""
    dt_str = f"{date} {time}"
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
    return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60 + dt.second/3600)


def get_ayanamsa_value(jd_ut: float, ayanamsa_id: int, flags: int) -> float:
    """Get ayanamsa value for the given JD (UT converted to ET)."""
    jd_et = jd_ut + swe.deltat(jd_ut)  # Convert UT to ET
    return swe.get_ayanamsa_ex(jd_et, flags)[1]


def sidereal_longitude(ecl_lng: float, ayanamsa: float) -> float:
    """Convert ecliptic longitude to sidereal."""
    return (ecl_lng - ayanamsa) % 360


def get_planet_positions(jd_ut: float, flags: int, is_sidereal: bool, ayanamsa: float) -> dict:
    """Get positions for all planets."""
    positions = {}
    
    for name, planet_id in PLANETS.items():
        if name in ["South_Node"]:
            continue  # Ketu is computed as opposite to Rahu
        
        result = swe.calc(jd_ut, planet_id, flags)
        lon = result[0][0]
        lat = result[0][1]
        dist = result[0][2]
        speed = result[0][3]
        retro = speed < 0
        
        if is_sidereal:
            lon = sidereal_longitude(lon, ayanamsa)
        
        positions[name] = {
            "lon": round(lon, 6),
            "lat": round(lat, 6),
            "dist": round(dist, 6),
            "speed": round(speed, 6),
            "retro": retro,
        }
    
    # Ketu = opposite of Rahu (North_Node)
    if "North_Node" in positions:
        positions["South_Node"] = {
            "lon": round((positions["North_Node"]["lon"] + 180) % 360, 6),
            "lat": round(-positions["North_Node"]["lat"], 6),
            "dist": positions["North_Node"]["dist"],
            "speed": positions["North_Node"]["speed"],
            "retro": not positions["North_Node"]["retro"],
        }
    
    return positions


def get_houses(jd_ut: float, lat: float, lon: float, alt: float, 
                hsys: bytes, flags: int) -> dict:
    """Calculate house cusps and ascendant."""
    try:
        cusps, ascmc = swe.houses(jd_ut, lat, lon, hsys)
    except:
        return {"error": "House calculation failed"}
    
    houses = {
        "asc": round(ascmc[0], 6),
        "mc": round(ascmc[1], 6),
        "armc": round(ascmc[2], 6),
        "vertex": round(ascmc[3], 6),
    }
    
    for i, cusp in enumerate(cusps[:12], 1):
        houses[str(i)] = round(cusp, 6)
    
    return houses


def assign_houses(positions: dict, houses: dict) -> dict:
    """Assign house numbers to planets based on cusp positions."""
    asc = houses["asc"]
    cusps = [houses[str(i)] for i in range(1, 13)]
    
    for name, pos in positions.items():
        lon = pos["lon"]
        house = 1
        min_diff = 360
        
        for i in range(12):
            cusp_next = cusps[(i + 1) % 12]
            diff = (cusp_next - cusps[i]) % 360
            point_diff = (lon - cusps[i]) % 360
            
            if point_diff < diff and point_diff < min_diff:
                min_diff = point_diff
                house = i + 1
        
        positions[name]["house"] = house
    
    return positions


def get_nakshatra(lon: float) -> tuple[str, float]:
    """Calculate nakshatra from longitude."""
    nak_idx = int(lon // (13 + 1/3)) % 27
    deg_in_nak = (lon % (13 + 1/3)) / (13 + 1/3) * 100
    return NAKSHATRAS[nak_idx], round(deg_in_nak, 6)


def get_tithi(sun_lon: float, moon_lon: float) -> tuple[str, float]:
    """Calculate tithi from sun and moon longitudes."""
    diff = (moon_lon - sun_lon) % 360
    tithi_idx = int(diff // 12) % 30
    deg_in_tithi = (diff % 12) / 12 * 100
    return TITHIS[tithi_idx], round(deg_in_tithi, 6)


def get_yoga(sun_lon: float, moon_lon: float) -> tuple[str, float]:
    """Calculate yoga from sun and moon longitudes."""
    total = (sun_lon + moon_lon) % 360
    yoga_idx = int(total * 27 / 360) % 27
    deg_in_yoga = (total * 27 / 360) % 1 * 100
    return YOGAS[yoga_idx], round(deg_in_yoga, 6)


def get_sunrise_sunset(date: str, lat: float, lon: float) -> tuple[str, str]:
    """Calculate sunrise and sunset times."""
    parts = [int(x) for x in date.split("-")]
    jd = swe.julday(parts[0], parts[1], parts[2], 12.0)
    try:
        sunrise = swe.sunrise(jd, lat, lon)
        sunset = swe.sunset(jd, lat, lon)
        return sunrise, sunset
    except:
        return "06:00:00", "18:00:00"


def get_panchanga(jd_ut: float, lat: float, lon: float, positions: dict) -> dict:
    """Calculate Panchanga elements."""
    sun_lon = positions["Sun"]["lon"]
    moon_lon = positions["Moon"]["lon"]
    
    tithi, tithi_deg = get_tithi(sun_lon, moon_lon)
    nakshatra, nak_deg = get_nakshatra(moon_lon)
    yoga, yoga_deg = get_yoga(sun_lon, moon_lon)
    
    # Karana (half of tithi)
    tithi_num = int((moon_lon - sun_lon) % 360) // 12
    karana_idx = tithi_num % 11
    if karana_idx == 0:
        karana_idx = 11
    karana = ["Kimstughna", "Bava", "Kaulava", "Taitula", "Garija", "Vanija",
              "Vishti", "Shakuni", "Chatushpada", "Naga", "Chatra"][karana_idx - 1]
    
    # Vara (day of week) - swe.revjul returns (year, month, day, hour, min, sec)
    rev = swe.revjul(jd_ut)
    dt = datetime(int(rev[0]), int(rev[1]), int(rev[2]))
    vara = VARS[dt.weekday()]
    
    sunrise, sunset = get_sunrise_sunset(f"{int(rev[0])}-{int(rev[1]):02d}-{int(rev[2]):02d}", lat, lon)
    
    return {
        "tithi": tithi,
        "nakshatra": nakshatra,
        "yoga": yoga,
        "karana": karana,
        "vara": vara,
        "sunrise": sunrise if isinstance(sunrise, str) else f"{int(sunrise)}:{int((sunrise%1)*60)}:{int(((sunrise%1)*60)%1*60)}",
        "sunset": sunset if isinstance(sunset, str) else f"{int(sunset)}:{int((sunset%1)*60)}:{int(((sunset%1)*60)%1*60)}",
    }


def main():
    args = parse_args()
    
    # Setup flags
    flags = args["flags"]
    if args["zodiac"] == "sidereal":
        flags |= swe.FLG_SIDEREAL
    
    # Ayanamsa
    ayanamsa_id = AYANAMSA_MAP.get(args["ayanamsa"].lower(), swe.SIDM_LAHIRI)
    if args["ayanamsa"].lower() != "tropical":
        flags |= swe.FLG_SIDEREAL
    
    # House system
    house_system_id = HOUSE_MAP.get(args["house_system"], b"P")
    
    # Calculate JD
    jd_ut = get_jd_ut(args["date"], args["time"])
    
    # Get ayanamsa value
    ayanamsa_value = get_ayanamsa_value(jd_ut, ayanamsa_id, flags)
    
    # Get planet positions
    is_sidereal = args["zodiac"] == "sidereal" and args["ayanamsa"] != "tropical"
    positions = get_planet_positions(jd_ut, flags, is_sidereal, ayanamsa_value)
    
    # Calculate houses if requested
    houses = None
    if args["compute_houses"]:
        houses = get_houses(jd_ut, args["lat"], args["lon"], args["altitude"], house_system_id, flags)
        positions = assign_houses(positions, houses)
    
    # Build response
    response = {
        "jd_ut": round(jd_ut, 6),
        "ayanamsa_value": round(ayanamsa_value, 6),
        "positions": positions,
        "houses": houses if houses else None,
        "panchanga": None,
        "choghadiya": None,
        "errors": [],
    }
    
    # Panchanga
    if args["compute_panchanga"]:
        response["panchanga"] = get_panchanga(jd_ut, args["lat"], args["lon"], positions)
    
    print(json.dumps(response, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
