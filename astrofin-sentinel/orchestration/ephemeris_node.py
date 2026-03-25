"""
Ephemeris Node — Astronomical Data Provider
===========================================
Рассчитывает астрономические позиции для астрологического анализа.

Использует:
- Swiss Ephemeris (swe) для точных позиций планет
- Кэш для повторных запросов
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional
import math

from agents.base.base_agent import (
    BaseAgent,
    SentinelState,
    AgentResult,
    RawAstroData,
    Confidence,
    Action,
)


class EphemerisNode:
    """
    Получает астрономические данные для заданного времени и места.

    В продакшене использует `sweph` (Swiss Ephemeris).
    Заглушка работает на основе приближённых расчётов.
    """

    # ─── Константы ────────────────────────────────────────

    NAKSHATRAS = [
        "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashirsha",
        "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
        "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
        "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Shadha",
        "Uttara Shadha", "Shravana", "Dhanishtha", "Shatabhisha",
        "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
    ]

    ZODIAC_SIGNS = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]

    CHOGHADIYA_TABLE = [
        ("Amrita", True),
        ("Chara", True),
        ("Labha", True),
        ("Shubha", True),
        ("Charana", None),
        ("Dubia", None),
        ("Krodha", False),
        ("Mrityu", False),
    ]

    def __init__(self):
        self._cache: dict[str, RawAstroData] = {}

    def get_astro_data(
        self,
        timestamp_utc: str,
        latitude: float,
        longitude: float,
    ) -> RawAstroData:
        """
        Получает полные астрологические данные для момента.

        Args:
            timestamp_utc: ISO timestamp, например "2026-03-24T12:00:00Z"
            latitude: широта в градусах
            longitude: долгота в градусах

        Returns:
            RawAstroData с рассчитанными позициями
        """
        cache_key = f"{timestamp_utc}_{latitude:.2f}_{longitude:.2f}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        dt = datetime.fromisoformat(timestamp_utc.replace("Z", "+00:00"))

        # ── Расчёт позиций (упрощённый без Swiss Ephemeris) ──
        jd = self._to_julian_date(dt)

        moon_sign_idx, moon_degree = self._calc_moon_position(jd)
        moon_sign = self.ZODIAC_SIGNS[moon_sign_idx]

        # Фаза Луны (0-100%)
        moon_phase = self._calc_moon_phase(jd)

        # Накшатра
        nakshatra_idx = int(moon_degree / (360 / 27))
        nakshatra = self.NAKSHATRAS[nakshatra_idx % 27]

        # Тидхи (1-15 в каждой половине месяца)
        tithi_idx = int((jd % 30) / 2) + 1
        tithi = f"{tithi_idx}"

        # Йога (комбинация Sun + Moon position)
        yoga_idx = int((moon_sign_idx + int(moon_degree / 10)) % 27)
        yoga = self.NAKSHATRAS[yoga_idx]

        # Карана
        karana_idx = int(moon_degree / 15) % 11
        karana = f"K{ karana_idx + 1}"

        # Choghadiya (8 частей дня по ~3 часа)
        day_fraction = (dt.hour * 60 + dt.minute) / (24 * 60)
        choghadiya_slot = int(day_fraction * 8) % 8
        choghadiya_type, is_auspicious_raw = self.CHOGHADIYA_TABLE[choghadiya_slot]

        # Окно Choghadiya
        slot_minutes = 24 * 60 // 8
        start_min = choghadiya_slot * slot_minutes
        end_min = start_min + slot_minutes
        choghadiya_window_start = f"{start_min // 60:02d}:{start_min % 60:02d}"
        choghadiya_window_end = f"{end_min // 60:02d}:{end_min % 60:02d}"

        astro = RawAstroData(
            timestamp_utc=timestamp_utc,
            latitude=latitude,
            longitude=longitude,
            moon_sign=moon_sign,
            moon_degree=moon_degree,
            moon_phase=moon_phase,
            nakshatra=nakshatra,
            yoga=yoga,
            tithi=tithi,
            karana=karana,
            choghadiya_type=choghadiya_type,
            choghadiya_window_start=choghadiya_window_start,
            choghadiya_window_end=choghadiya_window_end,
            is_auspicious=bool(is_auspicious_raw),
            raw={
                "jd": jd,
                "nakshatra_idx": nakshatra_idx,
                "choghadiya_slot": choghadiya_slot,
            },
        )

        self._cache[cache_key] = astro
        return astro

    def _to_julian_date(self, dt: datetime) -> float:
        """Конвертирует datetime в Julian Date."""
        y = dt.year
        m = dt.month
        d = dt.day + (dt.hour + dt.minute / 60 + dt.second / 3600) / 24

        if m <= 2:
            y -= 1
            m += 12

        A = int(y / 100)
        B = 2 - A + int(A / 4)

        return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + B - 1524.5

    def _calc_moon_position(self, jd: float) -> tuple[int, float]:
        """
        Приближённый расчёт положения Луны.
        Returns: (sign_index, degree_in_sign)
        """
        T = (jd - 2451545.0) / 36525

        # Средняя долгота Луны
        L = (218.3164477 +
             481267.88123421 * T +
             0.529775 * T**2)

        # Средняя аномалия Луны
        M = (134.9633964 +
             477198.8675055 * T +
             0.0087214 * T**2)

        # Аргумент широты
        F = (93.2720950 +
             483202.0175233 * T +
             -0.0036539 * T**2)

        # Элонгация
        Om = (125.04452 - 1934.1362619 * T +
              0.0020708 * T**2)

        # Упрощённое положение
        elon = L + 6.289 * math.sin(math.radians(M))

        # Нормализуем
        elon_norm = elon % 360
        sign_idx = int(elon_norm / 30)
        deg_in_sign = elon_norm % 30

        return sign_idx, deg_in_sign

    def _calc_moon_phase(self, jd: float) -> str:
        """
        Возвращает название фазы Луны.
        """
        # Новолуние = JD 2451557.5 + 29.53059 * n
        synodic = 29.53059
        days_since_new = (jd - 2451557.5) % synodic
        phase_pct = days_since_new / synodic

        if phase_pct < 0.0625:
            return "New Moon"
        elif phase_pct < 0.1875:
            return "Waxing Crescent"
        elif phase_pct < 0.3125:
            return "First Quarter"
        elif phase_pct < 0.4375:
            return "Waxing Gibbous"
        elif phase_pct < 0.5625:
            return "Full Moon"
        elif phase_pct < 0.6875:
            return "Waning Gibbous"
        elif phase_pct < 0.8125:
            return "Last Quarter"
        elif phase_pct < 0.9375:
            return "Waning Crescent"
        else:
            return "New Moon"
