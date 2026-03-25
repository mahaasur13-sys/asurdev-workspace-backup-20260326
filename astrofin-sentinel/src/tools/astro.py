import swisseph as swe
from datetime import datetime
from typing import Optional
from dataclasses import dataclass


# Zodiac signs and nakshatras
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha", "Shatabhisha",
    "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

ZODIAC_SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

KARANAS = ["Bava", "Kaul", "Taitil", "Gari", "Vanija", "Vishti", "Sakuni", "Chatushtika", "Naga", "Kinstughna"]

YOGAS = [
    "Shubh", "Amrit", "Marut", "Kaal", "Naga", "Sinha", "Dhaya", "Ganda",
    "Vriddhi", "Dhruva", "Harshana", "Vajra", "Sukarma", "Dhruti", "Sula", "Vyatipata",
    "Variyan", "Parigha", "Shiva", "Siddha", "Sadhya", "Subha", "Brahmanya", "Aindra"
]


@dataclass
class AstroData:
    julian_day: float
    sun_long: float
    moon_long: float
    moon_phase: str
    moon_phase_deg: float
    nakshatra: str
    nakshatra_long: float
    yoga: str
    karana: str
    lunar_day: str
    zodiac_sign: str
    is_shukla_paksha: bool
    tithi: int
    tithi_name: str


class AstroCalculator:
    def __init__(self, ephemeris_path: Optional[str] = None):
        if ephemeris_path:
            swe.set_ephe_path(ephemeris_path)
        else:
            swe.set_ephe_path("./data/ephe")

    def calculate(self, dt: datetime, lat: float, lon: float) -> AstroData:
        """Calculate full astrological data for a given UTC datetime and location."""
        # Convert to Julian Day
        jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0 + dt.second/3600.0)

        # Calculate Sun and Moon positions
        sun = swe.calc_ut(jd, swe.SUN)[0]
        moon = swe.calc_ut(jd, swe.MOON)[0]

        sun_long = sun[0]
        moon_long = moon[0]

        # Moon phase (0-360 degrees)
        moon_phase_deg = moon_long - sun_long
        if moon_phase_deg < 0:
            moon_phase_deg += 360

        # Determine phase name
        if moon_phase_deg < 90:
            moon_phase = "New Moon"
        elif moon_phase_deg < 180:
            moon_phase = "First Quarter"
        elif moon_phase_deg < 270:
            moon_phase = "Full Moon"
        else:
            moon_phase = "Last Quarter"

        # Nakshatra (lunar mansion) - 27 divisions
        nakshatra_idx = int(moon_long // (360 / 27)) % 27
        nakshatra = NAKSHATRAS[nakshatra_idx]
        nakshatra_long = (moon_long % (360 / 27)) / (360 / 27) * 100  # Position within nakshatra %

        # Yoga calculation
        yoga_long = (sun_long + moon_long) % 360
        yoga_idx = int(yoga_long // (360 / 27)) % 27
        yoga = YOGAS[yoga_idx]

        # Karana calculation
        tithi_long = moon_phase_deg / 360 * 60  # Tithis are 1/60 of the zodiac
        karana_idx = int(tithi_long) % 10
        karana = KARANAS[karana_idx]

        # Lunar day (Paksha)
        is_shukla_paksha = moon_phase_deg < 180
        lunar_day = "Shukla Paksha" if is_shukla_paksha else "Krishna Paksha"

        # Tithi name
        tithi = int(moon_phase_deg // 12) + 1  # Each tithi is 12 degrees
        tithi_name = f"{tithi}"

        # Zodiac sign
        sign_idx = int(sun_long // 30) % 12
        zodiac_sign = ZODIAC_SIGNS[sign_idx]

        return AstroData(
            julian_day=jd,
            sun_long=sun_long,
            moon_long=moon_long,
            moon_phase=moon_phase,
            moon_phase_deg=moon_phase_deg,
            nakshatra=nakshatra,
            nakshatra_long=nakshatra_long,
            yoga=yoga,
            karana=karana,
            lunar_day=lunar_day,
            zodiac_sign=zodiac_sign,
            is_shukla_paksha=is_shukla_paksha,
            tithi=tithi,
            tithi_name=tithi_name
        )

    def is_favorable_for_trading(self, astro: AstroData) -> tuple[bool, float, str]:
        """
        Determine if current astro conditions are favorable for trading.
        Returns (is_favorable, strength_score 0-1, interpretation).
        """
        score = 0.5
        factors = []
        recs = []

        # Moon phase favorability
        if astro.moon_phase in ["New Moon", "First Quarter"]:
            score += 0.15
            factors.append(f"Favorable moon phase: {astro.moon_phase}")
            recs.append("Bullish bias - good for entries")
        elif astro.moon_phase == "Full Moon":
            score -= 0.1
            factors.append(f"Caution: {astro.moon_phase} - high volatility")
            recs.append("Expect volatility, reduce position size")
        else:
            factors.append(f"Neutral moon phase: {astro.moon_phase}")

        # Nakshatra favorability
        favorable_nakshatras = ["Rohini", "Mrigashira", "Pushya", "Swati", "Hasta", "Chitra", "Shravana", "Revati"]
        if astro.nakshatra in favorable_nakshatras:
            score += 0.1
            factors.append(f"Favorable nakshatra: {astro.nakshatra}")
        elif astro.nakshatra in ["Ashlesha", "Jyeshtha", "Mula", "Ashwini"]:
            score -= 0.1
            factors.append(f"Difficult nakshatra: {astro.nakshatra}")

        # Yoga favorability
        favorable_yogas = ["Shubh", "Amrit", "Siddha", "Sadhya", "Subha", "Brahmanya"]
        difficult_yogas = ["Kaal", "Naga", "Sula", "Vyatipata", "Variyan"]

        if astro.yoga in favorable_yogas:
            score += 0.1
            factors.append(f"Favorable yoga: {astro.yoga}")
        elif astro.yoga in difficult_yogas:
            score -= 0.15
            factors.append(f"Difficult yoga: {astro.yoga}")

        # Shukla Paksha (waxing moon) generally favorable for buying
        if astro.is_shukla_paksha:
            score += 0.05
            factors.append("Waxing moon (Shukla Paksha) - positive momentum")

        # Normalize score
        score = max(0.0, min(1.0, score))

        interpretation = "; ".join(factors)
        recommendation = "; ".join(recs) if recs else "Neutral conditions - follow technicals"

        return score > 0.55, score, interpretation


if __name__ == "__main__":
    calc = AstroCalculator()
    now = datetime.utcnow()
    astro = calc.calculate(now, 25.2048, 55.2708)  # Dubai coordinates

    print(f"Moon Phase: {astro.moon_phase} ({astro.moon_phase_deg:.1f}°)")
    print(f"Nakshatra: {astro.nakshatra} ({astro.nakshatra_long:.1f}% in)")
    print(f"Yoga: {astro.yoga}")
    print(f"Paksha: {astro.lunar_day}")
    print(f"Karana: {astro.karana}")

    favorable, strength, interp = calc.is_favorable_for_trading(astro)
    print(f"\nFavorable: {favorable}, Strength: {strength:.2f}")
    print(f"Interpretation: {interp}")
