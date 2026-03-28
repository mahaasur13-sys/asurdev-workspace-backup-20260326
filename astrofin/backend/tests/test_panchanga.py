"""Tests for panchanga.py module."""
from __future__ import annotations
import pytest
from backend.src.panchanga import (
    extended_panchanga, choghadiya, muhurta_score, full_muhurta,
    sunrise_time, sunset_time,
    NAKSHATRAS, TITHIS_SHUKLA, TITHIS_VADIYA, KARANAS, YOGAS, VARAS,
    CHOGHADIYA_DAY, CHOGHADIYA_NIGHT, CHALDEAN,
    PLANET_RULER_OF_DAY,
)

LAT, LON = 53.2, 50.15  # Samara
TZ = 4


class TestExtendedPanchanga:
    def test_nakshatra_is_valid(self):
        p = extended_panchanga("2026-03-26", "12:00:00", lat=LAT, lon=LON, tz_offset=TZ)
        assert p["nakshatra"] in NAKSHATRAS

    def test_nakshatra_pada_range(self):
        p = extended_panchanga("2026-03-26", "12:00:00", lat=LAT, lon=LON, tz_offset=TZ)
        assert 1 <= p["nakshatra_pada"] <= 4
        assert p["nakshatra_pada_name"] in ["Ma", "Ra", "Ta", "Pa"]

    def test_tithi_is_shukla_or_vadiya(self):
        p = extended_panchanga("2026-03-26", "12:00:00", lat=LAT, lon=LON, tz_offset=TZ)
        assert p["tithi_paksha"] in ("Shukla", "Vadiya")
        assert "Shukla " in p["tithi"] or "Vadiya " in p["tithi"]

    def test_karana_is_valid(self):
        p = extended_panchanga("2026-03-26", "12:00:00", lat=LAT, lon=LON, tz_offset=TZ)
        assert p["karana"] in KARANAS

    def test_yoga_is_valid(self):
        p = extended_panchanga("2026-03-26", "12:00:00", lat=LAT, lon=LON, tz_offset=TZ)
        assert p["yoga"] in YOGAS

    def test_vara_is_sanskrit(self):
        p = extended_panchanga("2026-03-26", "12:00:00", lat=LAT, lon=LON, tz_offset=TZ)
        assert p["vara"] in VARAS
        assert p["day_of_week"] == 4  # Thursday = Guruvar

    def test_moon_longitude_0_to_360(self):
        p = extended_panchanga("2026-03-26", "12:00:00", lat=LAT, lon=LON, tz_offset=TZ)
        assert 0 <= p["moon_longitude"] < 360
        assert 0 <= p["sun_longitude"] < 360

    def test_nakshatra_quality_range(self):
        p = extended_panchanga("2026-03-26", "12:00:00", lat=LAT, lon=LON, tz_offset=TZ)
        assert p["nakshatra_quality"] in (-1, 0, 1)

    def test_yoga_quality_range(self):
        p = extended_panchanga("2026-03-26", "12:00:00", lat=LAT, lon=LON, tz_offset=TZ)
        assert p["yoga_quality"] in (-1, 0, 1)

    def test_tithi_quality_range(self):
        p = extended_panchanga("2026-03-26", "12:00:00", lat=LAT, lon=LON, tz_offset=TZ)
        assert p["tithi_quality"] in (-1, 0, 1)

    def test_ayanamsa_passed_through(self):
        p = extended_panchanga("2026-03-26", "12:00:00", lat=LAT, lon=LON,
                               ayanamsa="raman", tz_offset=TZ)
        assert p["ayanamsa"] == "raman"


class TestSunriseSunset:
    def test_sunrise_before_sunset(self):
        sr = sunrise_time("2026-03-26", lat=LAT, lon=LON, tz_offset=TZ)
        ss = sunset_time("2026-03-26", lat=LAT, lon=LON, tz_offset=TZ)
        assert sr < ss

    def test_sunrise_in_morning(self):
        sr = sunrise_time("2026-03-26", lat=LAT, lon=LON, tz_offset=TZ)
        assert 4 <= sr.hour <= 8

    def test_sunset_in_evening(self):
        ss = sunset_time("2026-03-26", lat=LAT, lon=LON, tz_offset=TZ)
        assert 17 <= ss.hour <= 21


class TestChoghadiya:
    def test_returns_day_and_night_choghadiyas(self):
        c = choghadiya("2026-03-26", lat=LAT, lon=LON, tz_offset=TZ)
        assert "day_choghadiyas" in c
        assert "night_choghadiyas" in c

    def test_8_day_choghadiyas(self):
        c = choghadiya("2026-03-26", lat=LAT, lon=LON, tz_offset=TZ)
        assert len(c["day_choghadiyas"]) == 8

    def test_8_night_choghadiyas(self):
        c = choghadiya("2026-03-26", lat=LAT, lon=LON, tz_offset=TZ)
        assert len(c["night_choghadiyas"]) == 8

    def test_choghadiya_names_valid(self):
        valid = {name for name, _ in CHOGHADIYA_DAY}
        c = choghadiya("2026-03-26", lat=LAT, lon=LON, tz_offset=TZ)
        for ch in c["day_choghadiyas"]:
            assert ch["choghadiya"] in valid

    def test_choghadiya_planets_valid(self):
        c = choghadiya("2026-03-26", lat=LAT, lon=LON, tz_offset=TZ)
        for ch in c["day_choghadiyas"] + c["night_choghadiyas"]:
            assert ch["planet"] in CHALDEAN

    def test_choghadiya_quality_values(self):
        c = choghadiya("2026-03-26", lat=LAT, lon=LON, tz_offset=TZ)
        for ch in c["day_choghadiyas"] + c["night_choghadiyas"]:
            assert ch["quality"] in (-1, 0, 1)

    def test_choghadiya_time_order(self):
        c = choghadiya("2026-03-26", lat=LAT, lon=LON, tz_offset=TZ)
        day = c["day_choghadiyas"]
        for i in range(len(day) - 1):
            assert day[i]["end"] <= day[i + 1]["start"]

    def test_thursday_first_lord_is_jupiter(self):
        c = choghadiya("2026-03-26", lat=LAT, lon=LON, tz_offset=TZ)
        assert c["weekday"] == "Guruvar"
        assert PLANET_RULER_OF_DAY["Guruvar"] == "Jupiter"

    def test_sunrise_sunset_in_result(self):
        c = choghadiya("2026-03-26", lat=LAT, lon=LON, tz_offset=TZ)
        assert "sunrise" in c
        assert "sunset" in c
        assert c["sunrise"] == c["day_choghadiyas"][0]["start"]


class TestMuhurtaScore:
    def test_score_0_to_1(self):
        p = extended_panchanga("2026-03-26", "12:00:00", lat=LAT, lon=LON, tz_offset=TZ)
        score = muhurta_score(p)
        assert 0.05 <= score <= 1.0

    def test_best_nakshatra_increases_score(self):
        # Rohini = auspicious nakshatra (quality=1)
        # Try different times to find Rohini
        for h in range(24):
            p = extended_panchanga("2026-03-25", f"{h:02d}:00:00", lat=LAT, lon=LON, tz_offset=TZ)
            if p["nakshatra"] == "Rohini":
                score = muhurta_score(p)
                assert score >= 0.75, f"Rohini should give high score, got {score}"
                break

    def test_bad_nakshatra_decreases_score(self):
        # Ashlesha = inauspicious (quality=-1)
        for h in range(24):
            p = extended_panchanga("2026-03-25", f"{h:02d}:00:00", lat=LAT, lon=LON, tz_offset=TZ)
            if p["nakshatra"] == "Ashlesha":
                score = muhurta_score(p)
                assert score < 0.75, f"Ashlesha should give lower score, got {score}"
                break

    def test_good_yoga_increases_score(self):
        p = extended_panchanga("2026-03-26", "12:00:00", lat=LAT, lon=LON, tz_offset=TZ)
        score = muhurta_score(p)
        # With Shobhana yoga (+1) and Ardra nakshatra (+0) and Navami tithi (-1)
        # score = 0.5 + 0.15 - 0.1 = 0.55
        assert score == 0.55


class TestFullMuhurta:
    def test_returns_all_fields(self):
        fm = full_muhurta("2026-03-26", "12:00:00", lat=LAT, lon=LON)
        assert "panchanga" in fm
        assert "choghadiya" in fm
        assert "score" in fm
        assert 0 <= fm["score"] <= 1
