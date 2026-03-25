"""
Swiss Ephemeris Module — asurdev Sentinel v3.2
================================================
Modular ephemeris calculations using Swiss Ephemeris library.

Modules:
- swiss_ephemeris_tool: Main LangGraph tool with enforcement
- panchanga_calculator: Panchanga (Tithi, Nakshatra, Yoga, Karana, Vara)
- choghadiya_calculator: Choghadiya (day/night time periods)
- ashtakavarga_calculator: Bhinnashtakavarga & Sarvashtakavarga

Usage:
    from swiss_ephemeris import swiss_ephemeris
    
    result = swiss_ephemeris(
        date="2026-03-22",
        time="10:00:00",
        lat=55.7558,
        lon=37.6173,
        compute_panchanga=True,
        compute_choghadiya=True,
        compute_ashtakavarga=True,
    )
"""

from .swiss_ephemeris_tool import swiss_ephemeris, SwissEphemerisInput
from .panchanga_calculator import calculate_panchanga, get_nakshatra_trading_score
from .choghadiya_calculator import calculate_choghadiya, get_choghadiya_trading_score
from .ashtakavarga_calculator import calculate_ashtakavarga, interpret_ashtakavarga_for_trading

__all__ = [
    "swiss_ephemeris",
    "SwissEphemerisInput",
    "calculate_panchanga",
    "get_nakshatra_trading_score",
    "calculate_choghadiya",
    "get_choghadiya_trading_score",
    "calculate_ashtakavarga",
    "interpret_ashtakavarga_for_trading",
]
