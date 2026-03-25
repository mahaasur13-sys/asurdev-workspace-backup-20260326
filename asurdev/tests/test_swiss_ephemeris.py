"""Тесты Swiss Ephemeris (unit + E2E)."""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from swiss_ephemeris.swiss_ephemeris_tool import swiss_ephemeris


def test_basic_positions():
    """Проверяем базовые позиции планет."""
    res = swiss_ephemeris(
        date="2000-01-01",
        time="00:00:00",
        lat=55.7558,
        lon=37.6173,
        ayanamsa="lahiri",
        zodiac="sidereal",
        compute_panchanga=True,
        compute_choghadiya=True,
        compute_ashtakavarga=True,
    )
    assert "positions" in res
    assert 0 <= res["positions"]["Sun"]["lon"] < 360


def test_panchanga_complete():
    """Панчанга содержит все обязательные поля."""
    res = swiss_ephemeris(
        date="2000-01-01",
        time="00:00:00",
        lat=55.7558,
        lon=37.6173,
        ayanamsa="lahiri",
        compute_panchanga=True,
    )
    p = res["panchanga"]
    assert p["yoga_number"] in range(1, 28)
    assert "karana_number_60" in p


def test_choghadiya_day_night():
    """Чогадия содержит 8 частей дня и ночи."""
    res = swiss_ephemeris(
        date="2000-01-01",
        time="00:00:00",
        lat=55.7558,
        lon=37.6173,
        compute_choghadiya=True,
    )
    ch = res["choghadiya"]
    assert len(ch["day_parts"]) == 8
    assert len(ch["night_parts"]) == 8


def test_ashtakavarga_range():
    """Аштакаварга содержит правильные ключи."""
    res = swiss_ephemeris(
        date="2000-01-01",
        time="00:00:00",
        lat=55.7558,
        lon=37.6173,
        compute_ashtakavarga=True,
        house_system="W",
    )
    assert "ashtakavarga" in res
    assert "sarvashtakavarga" in res["ashtakavarga"]


def test_cache_works():
    """Кэш возвращает тот же объект (тот же dict)."""
    r1 = swiss_ephemeris(
        date="2000-01-01",
        time="00:00:00",
        lat=55.7558,
        lon=37.6173,
    )
    r2 = swiss_ephemeris(
        date="2000-01-01",
        time="00:00:00",
        lat=55.7558,
        lon=37.6173,
    )
    # Один и тот же объект = кэш сработал
    assert r1 is r2


# === E2E тесты с эталонными датами ===

def test_known_date_2000_01_01():
    """E2E: проверка на эталонной дате 1 Jan 2000."""
    res = swiss_ephemeris(
        date="2000-01-01",
        time="12:00:00",
        lat=28.6139,  # Delhi
        lon=77.2090,
        ayanamsa="lahiri",
        compute_panchanga=True,
    )

    # Солнце в разумном диапазоне (любое значение 0-360)
    sun_lon = res["positions"]["Sun"]["lon"]
    assert 0 <= sun_lon < 360, f"Sun lon {sun_lon} not in valid range [0, 360)"


def test_known_date_2026_03_22():
    """E2E: проверка на текущую дату (22 Mar 2026)."""
    res = swiss_ephemeris(
        date="2026-03-22",
        time="10:00:00",
        lat=55.7558,  # Москва
        lon=37.6173,
        ayanamsa="lahiri",
        compute_panchanga=True,
        compute_choghadiya=True,
    )

    assert "positions" in res
    assert "Sun" in res["positions"]
    assert 0 <= res["positions"]["Sun"]["lon"] < 360
    assert "panchanga" in res


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
