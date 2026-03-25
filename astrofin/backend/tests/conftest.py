"""Pytest configuration and fixtures for AstroFin tests."""

import asyncio
import sys
from datetime import datetime
from typing import Dict, Any

import pytest

# Add project root to path
sys.path.insert(0, "/home/workspace/astrofin")


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_context() -> Dict[str, Any]:
    """Sample context for agent testing."""
    return {
        "symbol": "BTC",
        "price": 68250.0,
        "datetime": datetime.now(),
        "query": "Analyze BTC for swing trade",
        "timeframe": "SWING",
        "lat": 40.7128,
        "lon": -74.0060,
    }


@pytest.fixture
def mock_ephemeris() -> Dict[str, Any]:
    """Mock ephemeris data for testing without API calls."""
    return {
        "planets": {
            "sun": {"sign": "Aries", "degrees": 15.5, "longitude": 45.5},
            "moon": {"sign": "Cancer", "degrees": 22.3, "longitude": 112.3},
            "mars": {"sign": "Capricorn", "degrees": 8.1, "longitude": 278.1},
            "mercury": {"sign": "Pisces", "degrees": 3.7, "longitude": 353.7},
            "jupiter": {"sign": "Sagittarius", "degrees": 25.2, "longitude": 265.2},
            "venus": {"sign": "Aquarius", "degrees": 18.9, "longitude": 318.9},
            "saturn": {"sign": "Capricorn", "degrees": 5.4, "longitude": 275.4},
            "rahu": {"sign": "Cancer", "degrees": 12.0, "longitude": 112.0},
        },
        "datetime": "2026-03-25 12:00:00",
        "panchanga": {
            "nakshatra": "Punarvasu",
            "nakshatra_pada": 2,
            "yoga": "Shobhana",
            "vara": "Wednesday",
            "tithi": "Shukla Ekadashi",
            "karana": "Balava",
            "yoga_category": "Auspicious",
        },
    }


@pytest.fixture
def mock_polygon_response() -> Dict[str, Any]:
    """Mock Polygon.io response for testing."""
    return {
        "status": "ok",
        "symbol": "BTC",
        "unusual_volume": 5,
        "large_sweeps": 2,
        "put_call_ratio": 0.65,
        "gamma_exposure": 150000,
        "snapshot": {"last_price": 68250, "volume": 25000000000},
    }


@pytest.fixture
def mock_market_data() -> Dict[str, Any]:
    """Mock market data for technical analysis tests."""
    return {
        "rsi": 58.5,
        "macd": {"macd": 125.5, "signal": 98.2, "histogram": 27.3},
        "bollinger": {"upper": 71000, "middle": 68250, "lower": 65500},
        "volume": {"trend": "increasing", "recent_avg": 25000, "older_avg": 21000},
    }
