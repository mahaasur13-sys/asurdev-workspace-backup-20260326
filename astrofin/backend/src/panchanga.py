"""
Extended Panchanga & Choghadiya calculations.
All Panchanga formulas are sidereal-moon-based (Lahiri default).
"""
from __future__ import annotations
from datetime import datetime, timedelta
from typing import Any
import swisseph as swe

swe.set_ephe_path("/home/workspace/astrofin/backend/ephe")

NAKSHATRAS = [
    "Aswini", "Bharani", "Krittika", "Rohini", "Mrigashirsha",
    "Ardra", "Punarvasu", "Pushya", "Aslesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
    "Uttara Ashadha", "Shravana", "Dhanishtha", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]

NAKSHATRA_PADA_NAMES = ["Ma", "Ra", "Ta", "Pa"]

TITHIS_SHUKLA = [
    "Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi", "Poornima",
]
TITHIS_VADIYA = [
    "Pratipada", "Dvitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dvadashi", "Trayodashi", "Chaturdashi", "Amavasya",
]

KARANAS = [
    "Bava", "Balava", "Kaulava", "Taitula", "Garijani",
    "Vanij", "Vishti",
    "Sakuni", "Chatushtava", "Naga", "Naga",
]

YOGAS = [
    "Vishkumbha", "Preeti", "Aayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarma", "Dhruti", "Shoola", "Ganda",
    "Bhruti", "Shaubhagya", "Shobhana", "Amrita", "Chitra",
    "Siddha", "Vyatipata", "Variyan", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Brahmagupte", "Indigupte",
    "Vajra", "Siddhi", "Viyat",
]

VARAS = [
    "Ravivara", "Somavara", "Mangalavara", "Budhavara",
    "Guruvar", "Shukravara", "Shanivara",
]

NAKSHATRA_QUALITY = {
    "Rohini": 1, "Mrigashirsha": 1, "Uttara Phalguni": 1,
    "Hasta": 1, "Swati": 1, "Shravana": 1,
    "Dhanishtha": 1, "Purva Bhadrapada": 1, "Revati": 1,
    "Punarvasu": 1, "Pushya": 1, "Chitra": 1,
    "Aswini": 0, "Bharani": 0, "Krittika": 0, "Ardra": 0,
    "Vishakha": 0, "Anuradha": 0, "Uttara Ashadha": 0,
    "Shatabhisha": 0, "Uttara Bhadrapada": 0,
    "Aslesha": -1, "Magha": -1, "Mula": -1,
    "Jyeshtha": -1, "Purva Ashadha": -1,
}

YOGA_QUALITY = {
    "Amrita": 1, "Shobhana": 1, "Shubha": 1, "Siddha": 1, "Sadhya": 1,
    "Aayushman": 0, "Preeti": 0, "Bhruti": 0, "Saubhagya": 0,
    "Vyatipata": -1, "Atiganda": -1, "Ganda": -1,
    "Shoola": -1, "Parigha": -1, "Vajra": -1,
}

TITHI_QUALITY = {
    "Pratipada": 1, "Dvitiya": 1, "Tritiya": 1, "Panchami": 1,
    "Saptami": 1, "Dashami": 1,
    "Chaturthi": -1, "Ashtami": -1, "Navami": -1,
    "Ekadashi": 0, "Dvadashi": 0, "Trayodashi": 0,
    "Chaturdashi": 0, "Poornima": 0, "Amavasya": 0,
}

CHOGHADIYA_DAY = [
    ("Udveg", -1), ("Chal", 0), ("Labh", 1), ("Amrit", 1),
    ("Kaal", -1), ("Labh", 1), ("Udveg", -1), ("Kaal", -1),
]
CHOGHADIYA_NIGHT = [
    ("Amrit", 1), ("Kaal", -1), ("Labh", 1), ("Udveg", -1),
    ("Shubh", 1), ("Labh", 1), ("Udveg", -1), ("Kaal", -1),
]

CHALDEAN = ["Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon"]

PLANET_RULER_OF_DAY = {
    "Ravivara": "Sun", "Somavara": "Moon", "Mangalavara": "Mars",
    "Budhavara": "Mercury", "Guruvar": "Jupiter",
    "Shukravara": "Venus", "Shanivara": "Saturn",
}

def _jd(dt: datetime, tz_offset: int) -> float:
    utc = dt - timedelta(hours=tz_offset)
    return swe.utc_to_jd(
        utc.year, utc.month, utc.day,
        utc.hour, utc.minute, utc.second, 1
    )[0]

def _jd_to_datetime(jd_ut: float, tz_offset: int) -> datetime:
    comp = swe.jdut1_to_utc(jd_ut, 1)
    year, month, day, hour_frac = comp[:4]
    minute = int((hour_frac % 1) * 60)
    second = int(((hour_frac % 1) * 60 - minute) * 60)
    utc = datetime(int(year), int(month), int(day), int(hour_frac), minute, second)
    return utc + timedelta(hours=tz_offset)

def _ayanamsa_correction(jd: float, ayanamsa: str | int) -> float:
    if not isinstance(ayanamsa, str):
        # Already a SIDM code int — use it directly
        swe.set_sid_mode(int(ayanamsa))
        return swe.get_ayanamsa(jd)
    if ayanamsa.lower() == "tropical":
        return 0.0
    codes = {
        "lahiri": swe.SIDM_LAHIRI,
        "raman": swe.SIDM_RAMAN,
        "krmika": swe.SIDM_KRISHNAMURTI,
        "suryasiddhanta": swe.SIDM_SURYASIDDHANTA,
    }
    code = codes.get(ayanamsa.lower(), swe.SIDM_LAHIRI)
    swe.set_sid_mode(code)
    return swe.get_ayanamsa(jd)

def _tropical_to_sidereal(tropical_long: float, ayanamsa_corr: float) -> float:
    return (tropical_long - ayanamsa_corr) % 360

def _get_sidereal_longitude(jd: float, planet_idx: int, ayanamsa: str) -> float:
    pos = swe.calc_ut(jd, planet_idx, swe.FLG_SWIEPH | swe.FLG_SPEED)[0]
    tropical = pos[0] % 360
    ay_corr = _ayanamsa_correction(jd, ayanamsa)
    return _tropical_to_sidereal(tropical, ay_corr)

def _get_day_of_week(jd: float) -> int:
    return int(jd + 1.5) % 7

def extended_panchanga(
    date: str,
    time: str,
    lat: float = 40.7128,
    lon: float = -74.0060,
    ayanamsa: str = "lahiri",
    tz_offset: int = 4,
) -> dict[str, Any]:
    dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S")
    jd = _jd(dt, tz_offset)

    moon_long = _get_sidereal_longitude(jd, swe.MOON, ayanamsa)
    sun_long  = _get_sidereal_longitude(jd, swe.SUN, ayanamsa)

    nak_idx = int(moon_long // (360.0 / 27)) % 27
    nak = NAKSHATRAS[nak_idx]
    nak_remaining = moon_long % (360.0 / 27)
    pada = int(nak_remaining // (360.0 / 108)) + 1
    pada_name = NAKSHATRA_PADA_NAMES[pada - 1]

    diff = (moon_long - sun_long) % 360
    tithi_idx = int(diff // 12) % 15
    paksha = "Shukla" if diff <= 180 else "Vadiya"
    tithis = TITHIS_SHUKLA if paksha == "Shukla" else TITHIS_VADIYA
    tithi = f"{paksha} {tithis[tithi_idx]}"

    karana_raw = int(diff // 6) % 60
    if karana_raw < 7:
        karana = KARANAS[karana_raw]
    else:
        fixed_idx = ((karana_raw - 7) % 4)
        karana = KARANAS[7 + fixed_idx]

    yoga_idx = int((sun_long + moon_long) // (360.0 / 27)) % 27
    yoga = YOGAS[yoga_idx]

    day_idx = _get_day_of_week(jd)
    vara = VARAS[day_idx]

    nak_quality   = NAKSHATRA_QUALITY.get(nak, 0)
    yoga_quality  = YOGA_QUALITY.get(yoga, 0)
    tithi_name    = tithis[tithi_idx]
    tithi_quality = TITHI_QUALITY.get(tithi_name, 0)

    return {
        "nakshatra": nak,
        "nakshatra_pada": pada,
        "nakshatra_pada_name": pada_name,
        "nakshatra_quality": nak_quality,
        "tithi": tithi,
        "tithi_paksha": paksha,
        "tithi_idx": tithi_idx,
        "tithi_quality": tithi_quality,
        "karana": karana,
        "yoga": yoga,
        "yoga_quality": yoga_quality,
        "vara": vara,
        "day_of_week": day_idx,
        "moon_longitude": round(moon_long, 4),
        "sun_longitude": round(sun_long, 4),
        "ayanamsa": ayanamsa,
        "tz_offset": tz_offset,
    }

def sunrise_time(date: str, lat: float, lon: float, tz_offset: int = 4) -> datetime:
    dt = datetime.strptime(date, "%Y-%m-%d")
    jd = _jd(dt, tz_offset)
    try:
        _, tret = swe.rise_trans(
            jd, swe.SUN,
            swe.BIT_DISC_CENTER + swe.CALC_RISE,
            (lon, lat, 0),
        )
        return _jd_to_datetime(tret[0], tz_offset)
    except Exception:
        return dt.replace(hour=6, minute=0, second=0)

def sunset_time(date: str, lat: float, lon: float, tz_offset: int = 4) -> datetime:
    dt = datetime.strptime(date, "%Y-%m-%d")
    jd = _jd(dt, tz_offset)
    try:
        _, tret = swe.rise_trans(
            jd, swe.SUN,
            swe.BIT_DISC_CENTER + swe.CALC_SET,
            (lon, lat, 0),
        )
        return _jd_to_datetime(tret[0], tz_offset)
    except Exception:
        return dt.replace(hour=18, minute=0, second=0)

def choghadiya(
    date: str,
    lat: float = 40.7128,
    lon: float = -74.0060,
    tz_offset: int = 4,
) -> dict[str, Any]:
    rise = sunrise_time(date, lat, lon, tz_offset)
    sets = sunset_time(date, lat, lon, tz_offset)

    day_len = (sets - rise).total_seconds() / 3600
    night_len = 24 - day_len
    day_prahar_h = day_len / 8.0
    night_prahar_h = night_len / 8.0

    day_idx = _get_day_of_week(_jd(rise, tz_offset))
    weekday_name = VARAS[day_idx]
    first_lord = PLANET_RULER_OF_DAY[weekday_name]
    lord_idx = CHALDEAN.index(first_lord)

    def _lord(n: int) -> str:
        return CHALDEAN[(lord_idx + n) % 7]

    def _build_prahar(start: datetime, prahar_h: float, template: list) -> list:
        result = []
        for i, (name, quality) in enumerate(template):
            s = start + timedelta(hours=i * prahar_h)
            e = start + timedelta(hours=(i + 1) * prahar_h)
            result.append({
                "choghadiya": name,
                "quality": quality,
                "planet": _lord(i),
                "start": s.strftime("%H:%M"),
                "end": e.strftime("%H:%M"),
            })
        return result

    day_choghs = _build_prahar(rise, day_prahar_h, CHOGHADIYA_DAY)
    night_choghs = _build_prahar(sets, night_prahar_h, CHOGHADIYA_NIGHT)

    return {
        "date": date,
        "location": {"lat": lat, "lon": lon},
        "sunrise": rise.strftime("%H:%M"),
        "sunset": sets.strftime("%H:%M"),
        "weekday": weekday_name,
        "day_choghadiyas": day_choghs,
        "night_choghadiyas": night_choghs,
    }

def muhurta_score(panchanga: dict) -> float:
    score = 0.5
    nq = panchanga.get("nakshatra_quality", 0)
    if nq == 1:
        score += 0.3
    elif nq == -1:
        score -= 0.25
    yq = panchanga.get("yoga_quality", 0)
    if yq == 1:
        score += 0.15
    elif yq == -1:
        score -= 0.15
    tq = panchanga.get("tithi_quality", 0)
    if tq == 1:
        score += 0.1
    elif tq == -1:
        score -= 0.1
    return max(0.05, min(score, 1.0))

def full_muhurta(date: str, time: str, lat: float, lon: float,
                 ayanamsa: str = "lahiri", tz_offset: int = 4) -> dict[str, Any]:
    p = extended_panchanga(date, time, lat, lon, ayanamsa, tz_offset)
    c = choghadiya(date, lat, lon, tz_offset)
    score = muhurta_score(p)
    return {"panchanga": p, "choghadiya": c, "score": score}
