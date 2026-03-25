"""
ephemeris_node — вычисляет верифицированные астроданные через Swiss Ephemeris.

Этот узел ДОЛЖЕН выполниться ДО любого LLM агента.
LLM получает ТОЛЬКО интерпретации, НИКОГДА сырые расчёты.
"""

import hashlib
import logging
from datetime import datetime
from typing import Literal

from contracts.sentinel_state import (
    SentinelState,
    RawAstroData,
    MoonPhaseData,
    PlanetaryAspect,
    RetrogradeStatus,
)

logger = logging.getLogger(__name__)

# ============================================================
# SWISS EPHEMERIS WRAPPER (with caching)
# ============================================================

_ephemeris_cache: dict[str, RawAstroData] = {}
_ephemeris_verified: bool = False


def _get_ephemeris() -> tuple:
    """
    Returns (swisseph_module, is_available).
    Caches result after first import attempt.
    """
    global _ephemeris_verified
    if _ephemeris_verified:
        import swisseph
        return swisseph, True
    
    try:
        import swisseph as swe
        _ephemeris_verified = True
        return swe, True
    except ImportError:
        logger.warning("Swiss Ephemeris not available, using simplified calculations")
        return None, False


def _calculate_moon_phase(date: datetime, swe_module) -> MoonPhaseData:
    """Вычисляет лунную фазу через Swiss Ephemeris."""
    
    jd = swe_module.julday(date.year, date.month, date.day, date.hour + date.minute / 60)
    
    moon_result = swe_module.calc(jd, swe_module.MOON)
    moon_xx = moon_result[0] if isinstance(moon_result, tuple) else moon_result
    moon_lon = moon_xx[0]
    
    sun_result = swe_module.calc(jd, swe_module.SUN)
    sun_xx = sun_result[0] if isinstance(sun_result, tuple) else sun_result
    sun_lon = sun_xx[0]
    
    # Phase calculation (0.0-1.0)
    diff = (moon_lon - sun_lon) % 360
    phase = diff / 360
    illumination = (1 - abs(diff - 180) / 180) * 100
    
    # Phase name
    if phase < 0.03 or phase > 0.97:
        phase_name = "New Moon"
    elif phase < 0.22:
        phase_name = "Waxing Crescent"
    elif phase < 0.28:
        phase_name = "First Quarter"
    elif phase < 0.47:
        phase_name = "Waxing Gibbous"
    elif phase < 0.53:
        phase_name = "Full Moon"
    elif phase < 0.72:
        phase_name = "Waning Gibbous"
    elif phase < 0.78:
        phase_name = "Last Quarter"
    else:
        phase_name = "Waning Crescent"
    
    # Zodiac
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    sign_idx = int(moon_lon // 30) % 12
    sign_deg = moon_lon % 30
    
    return MoonPhaseData(
        phase_name=phase_name,
        phase_value=round(phase, 6),
        illumination_pct=round(illumination, 2),
        days_since_new_moon=round(phase * 29.53, 2),
        zodiac_sign=signs[sign_idx],
        zodiac_degree=round(sign_deg, 2),
        timestamp=date,
    )


def _calculate_planetary_positions(date: datetime, swe_module) -> dict[str, float]:
    """Вычисляет положения планет в градусах."""
    
    jd = swe_module.julday(date.year, date.month, date.day, date.hour + date.minute / 60)
    
    planets = {
        "sun": swe_module.SUN,
        "moon": swe_module.MOON,
        "mercury": swe_module.MERCURY,
        "venus": swe_module.VENUS,
        "mars": swe_module.MARS,
        "jupiter": swe_module.JUPITER,
        "saturn": swe_module.SATURN,
    }
    
    positions = {}
    for name, planet_id in planets.items():
        result = swe_module.calc(jd, planet_id)
        xx = result[0] if isinstance(result, tuple) else result
        positions[name] = xx[0] % 360  # Normalize to 0-360
    
    return positions


def _calculate_aspects(date: datetime, swe_module) -> list[PlanetaryAspect]:
    """Вычисляет планетные аспекты с orb <= 3°."""
    
    positions = _calculate_planetary_positions(date, swe_module)
    aspects = []
    
    # Key pairs to check
    pairs = [
        ("jupiter", "saturn"),  # Great Conjunction cycle
        ("mars", "saturn"),     # Tension
        ("venus", "mars"),      # Passion/harmony
        ("mercury", "venus"),   # Communication/values
        ("sun", "moon"),        # Lunation cycle
    ]
    
    aspect_degrees = {
        "conjunction": 0,
        "sextile": 60,
        "square": 90,
        "trine": 120,
        "opposition": 180,
    }
    
    for p1, p2 in pairs:
        if p1 not in positions or p2 not in positions:
            continue
        
        diff = abs(positions[p1] - positions[p2])
        if diff > 180:
            diff = 360 - diff
        
        for aspect_name, ideal_deg in aspect_degrees.items():
            orb = abs(diff - ideal_deg)
            if orb <= 3.0:  # Strict orb for accuracy
                aspects.append(PlanetaryAspect(
                    date=date.strftime("%Y-%m-%d"),
                    planet1=p1,
                    planet2=p2,
                    aspect_name=aspect_name,
                    exact_degree=round(diff, 2),
                    orb=round(orb, 2),
                    timestamp=date,
                ))
    
    return aspects


def _check_retrogrades(date: datetime, swe_module) -> list[RetrogradeStatus]:
    """Проверяет ретроградность планет."""
    
    # Need to compare speeds across multiple days
    statuses = []
    
    planets_check = ["mercury", "venus", "mars", "jupiter", "saturn"]
    
    for i in range(-3, 4):  # Check 7 days
        d = datetime(date.year, date.month, date.day) + timedelta(days=i)
        jd = swe_module.julday(d.year, d.month, d.day, 12)
        
        for planet_name in planets_check:
            planet_id = getattr(swe_module, planet_name.upper())
            result = swe_module.calc(jd, planet_id)
            xx = result[0] if isinstance(result, tuple) else result
            speed = xx[3] if len(xx) > 3 else 0  # Speed in deg/day
            
            if i == 0:  # Current day
                is_retrograde = speed < 0
                statuses.append(RetrogradeStatus(
                    planet=planet_name,
                    is_retrograde=is_retrograde,
                    speed_deg_per_day=round(speed, 4),
                    recommendation="Exercise caution" if is_retrograde else "Normal conditions",
                ))
    
    return statuses


# ============================================================
# SIMPLIFIED FALLBACK (no Swiss Ephemeris)
# ============================================================

def _simplified_moon_phase(date: datetime) -> MoonPhaseData:
    """Упрощённый расчёт без Swiss Ephemeris. Менее точный."""
    
    # Known new moon: Jan 6, 2000 (JD 2451550.1)
    a = (14 - date.month) // 12
    y = date.year + 4800 - a
    m = date.month + 12 * a - 3
    jd = (date.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 
          - 32045 - 2451545)  # Days from J2000.0
    
    days_since_new = (jd + date.hour / 24 + date.minute / 1440) % 29.530588853
    phase = days_since_new / 29.530588853
    
    illumination = (1 - abs(phase - 0.5) * 2) * 50 if phase <= 0.5 else (1 - abs(phase - 0.5) * 2) * 50
    
    if phase < 0.03 or phase > 0.97:
        phase_name = "New Moon"
    elif phase < 0.22:
        phase_name = "Waxing Crescent"
    elif phase < 0.28:
        phase_name = "First Quarter"
    elif phase < 0.47:
        phase_name = "Waxing Gibbous"
    elif phase < 0.53:
        phase_name = "Full Moon"
    elif phase < 0.72:
        phase_name = "Waning Gibbous"
    elif phase < 0.78:
        phase_name = "Last Quarter"
    else:
        phase_name = "Waning Crescent"
    
    return MoonPhaseData(
        phase_name=phase_name,
        phase_value=round(phase, 4),
        illumination_pct=round(illumination, 1),
        days_since_new_moon=round(days_since_new, 2),
        zodiac_sign="Unknown",
        zodiac_degree=0.0,
        timestamp=date,
    )


# ============================================================
# NODE FUNCTION
# ============================================================

def ephemeris_node(state: SentinelState) -> SentinelState:
    """
    LangGraph node: вычисляет верифицированные астроданные.
    
    ДОЛЖЕН выполниться до любого LLM агента.
    Результат кэшируется по hash(symbol + date).
    
    Returns:
        Updated state with astro_data populated
    """
    global _ephemeris_cache
    
    now = datetime.utcnow()
    cache_key = f"{state.symbol}:{now.strftime('%Y-%m-%d')}"
    
    logger.info(f"[ephemeris_node] Computing astro data for {state.symbol}")
    
    # Check cache
    if cache_key in _ephemeris_cache:
        cached = _ephemeris_cache[cache_key]
        logger.info(f"[ephemeris_node] Using cached data (hash={cached.calculation_hash[:8]})")
        return {**state.model_dump(), "astro_data": cached, "astro_data_verified": True}
    
    # Get Swiss Ephemeris
    swe, has_swe = _get_ephemeris()
    
    if has_swe:
        logger.info("[ephemeris_node] Using Swiss Ephemeris")
        moon = _calculate_moon_phase(now, swe)
        positions = _calculate_planetary_positions(now, swe)
        aspects = _calculate_aspects(now, swe)
        retrogrades = _check_retrogrades(now, swe)
        source = "swisseph"
    else:
        logger.warning("[ephemeris_node] Swiss Ephemeris not available, using simplified")
        moon = _simplified_moon_phase(now)
        positions = {}
        aspects = []
        retrogrades = []
        source = "simplified_fallback"
    
    # Calculate hash for deduplication
    hash_input = f"{state.symbol}:{moon.phase_value}:{len(aspects)}:{now.isoformat()}"
    calc_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    astro_data = RawAstroData(
        moon=moon,
        planetary_positions=positions,
        aspects=aspects,
        retrogrades=retrogrades,
        calculation_hash=calc_hash,
        calculated_at=now,
        ephemeris_source=source,
    )
    
    # Cache
    _ephemeris_cache[cache_key] = astro_data
    
    logger.info(
        f"[ephemeris_node] Completed: moon={moon.phase_name}, "
        f"aspects={len(aspects)}, retrogrades={[r.planet for r in retrogrades if r.is_retrograde]}"
    )
    
    return {
        **state.model_dump(),
        "astro_data": astro_data,
        "astro_data_verified": True,
        "errors": state.errors + ([f"Simplified ephemeris used (Swiss not available)"] if source == "simplified_fallback" else []),
    }


from datetime import timedelta
