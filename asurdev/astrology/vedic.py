"""Vedic Astrology Module — Nakshatra, Choghadiya, Muhurta"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from dataclasses import dataclass
import math

from .core import EssentialDignities, Aspects, AccidentalDignities

# Placeholder classes for compatibility
NAKSHATRAS = ["Aswini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", 
              "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
              "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula",
              "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha", "Shatabhisha",
              "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]

BENEFICS = ["Jupiter", "Venus", "Mercury", "Moon", "Sun"]
MALEFICS = ["Saturn", "Mars", "Rahu", "Ketu"]


class PlanetaryPositions:
    """Placeholder for planetary positions - simplified Vedic implementation"""
    
    def __init__(self, positions: Dict[str, float], signs: Dict[str, str]):
        self.positions = positions
        self.signs = signs
    
    def get_sign(self, planet: str) -> str:
        return self.signs.get(planet.lower(), "Aries")
    
    def get_degree(self, planet: str) -> float:
        return self.positions.get(planet.lower(), 0)
    
    def get_nakshatra(self, planet: str) -> Tuple[str, int]:
        degree = self.get_degree(planet)
        nak_index = int(degree / 13.333) % 27
        pada = int(degree % 13.333 / 3.333) + 1
        return NAKSHATRAS[nak_index], pada


class SwissEphemeris:
    """Placeholder - simplified calculations without Swiss Ephemeris dependency"""
    
    @staticmethod
    def julian_day(dt: datetime) -> float:
        """Simplified Julian Day calculation"""
        a = (14 - dt.month) // 12
        y = dt.year + 4800 - a
        m = dt.month + 12 * a - 3
        jd = dt.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
        # Add time fraction
        jd += (dt.hour + dt.minute / 60 + dt.second / 3600) / 24
        return jd
    
    @staticmethod
    def calculate_ayanamsa(jd: float) -> float:
        """Lahiri Ayanamsa (simplified)"""
        # ~24 degrees in 2000, precessing ~50 arcsec/year
        years_since_2000 = (jd - 2451545) / 365.25
        return 24 + years_since_2000 * 0.0139
    
    @staticmethod
    def get_planetary_positions(dt: datetime, ayanamsa: float = 0) -> PlanetaryPositions:
        """Get simplified planetary positions"""
        # Very simplified - in reality would use Swiss Ephemeris
        # These are placeholder calculations
        jd = SwissEphemeris.julian_day(dt)
        day_fraction = (jd % 1)
        
        positions = {
            "sun": (jd * 0.9856 + 280) % 360,
            "moon": (jd * 13.1764 + 120) % 360,
            "mercury": (jd * 4.0923 + 210) % 360,
            "venus": (jd * 1.6021 + 85) % 360,
            "mars": (jd * 0.5240 + 40) % 360,
            "jupiter": (jd * 0.0839 + 100) % 360,
            "saturn": (jd * 0.0334 + 250) % 360,
        }
        
        # Convert to signs
        signs_list = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                      "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        signs = {}
        for planet, pos in positions.items():
            sign_index = int(pos / 30)
            signs[planet] = signs_list[sign_index]
        
        return PlanetaryPositions(positions, signs)
    
    @staticmethod
    def moon_phase(jd: float) -> Tuple[str, float]:
        """Calculate moon phase (simplified)"""
        days_since_new = (jd - 2451550.1) % 29.53059
        illumination = (1 - abs(days_since_new - 14.765) / 14.765) * 100
        
        if illumination < 12.5:
            return "New Moon", illumination
        elif illumination < 37.5:
            return "Waxing Crescent", illumination
        elif illumination < 62.5:
            return "First Quarter", illumination
        elif illumination < 87.5:
            return "Waxing Gibbous", illumination
        elif illumination < 112.5:
            return "Full Moon", illumination
        elif illumination < 137.5:
            return "Waning Gibbous", illumination
        elif illumination < 162.5:
            return "Last Quarter", illumination
        else:
            return "Waning Crescent", illumination

# Choghadiya types
CHOGHADIYA = [
    {"name": "Udveg", "type": "neutral", "quality": "Leadership", "icon": "🟡"},
    {"name": "Char", "type": "good", "quality": "Travel, Trade", "icon": "🟢"},
    {"name": "Labh", "type": "good", "quality": "Profit, Invest", "icon": "🟢"},
    {"name": "Amrit", "type": "best", "quality": "Best for All", "icon": "💚"},
    {"name": "Kaal", "type": "bad", "quality": "Avoid New", "icon": "🔴"},
    {"name": "Shubh", "type": "good", "quality": "Good Deeds", "icon": "🟢"},
    {"name": "Rog", "type": "bad", "quality": "Illness, Conflict", "icon": "🔴"},
    {"name": "Ari", "type": "bad", "quality": "War, Disputes", "icon": "🔴"},
]

# Favorable nakshatras for trading
TRADING_NAKSHATRAS = ["Swati", "Hasta", "Ashlesha", "Jyeshtha", "Rohini", "Mrigashira"]
BAD_NAKSHATRAS = ["Ardra", "Magha", "Mula", "Ashlesha"]  # Ashlesha is tricky


class ChoghadiyaCalculator:
    """Calculate Choghadiya (Vedic time segments)"""
    
    DAY_LORDS = {0: "Sun", 1: "Moon", 2: "Mars", 3: "Mercury", 
                 4: "Jupiter", 5: "Venus", 6: "Saturn"}
    
    SEQUENCES = {
        "Sun":    ["Amrit", "Kaal", "Rog", "Udveg", "Char", "Labh", "Shubh", "Ari"],
        "Moon":   ["Shubh", "Ari", "Udveg", "Rog", "Kaal", "Amrit", "Char", "Labh"],
        "Mars":   ["Labh", "Char", "Amrit", "Kaal", "Rog", "Udveg", "Ari", "Shubh"],
        "Mercury":["Ari", "Shubh", "Labh", "Char", "Amrit", "Kaal", "Rog", "Udveg"],
        "Jupiter":["Udveg", "Ari", "Shubh", "Labh", "Char", "Amrit", "Kaal", "Rog"],
        "Venus":  ["Rog", "Udveg", "Ari", "Shubh", "Labh", "Char", "Amrit", "Kaal"],
        "Saturn": ["Kaal", "Rog", "Udveg", "Ari", "Shubh", "Labh", "Char", "Amrit"],
    }
    
    @classmethod
    def calculate(cls, dt: datetime) -> List[Dict]:
        """Calculate Choghadiya for the day"""
        day_lord = cls.DAY_LORDS[dt.weekday()]
        seq = cls.SEQUENCES[day_lord]
        
        # Simplified sunrise at 6:00 AM
        sunrise = dt.replace(hour=6, minute=0, second=0, microsecond=0)
        
        results = []
        for i, name in enumerate(seq * 2):  # 16 periods in 24h
            ch = next(c for c in CHOGHADIYA if c["name"] == name)
            start = sunrise + timedelta(minutes=90 * i)
            results.append({
                "period": i + 1,
                "name": name,
                "type": ch["type"],
                "quality": ch["quality"],
                "icon": ch["icon"],
                "start": start.strftime("%H:%M"),
                "end": (start + timedelta(minutes=90)).strftime("%H:%M"),
            })
        
        return results
    
    @classmethod
    def get_current(cls, dt: datetime) -> Dict:
        """Get current Choghadiya"""
        periods = cls.calculate(dt)
        hour = dt.hour
        minute = dt.minute
        current_min = hour * 60 + minute
        
        for p in periods:
            start_h, start_m = map(int, p["start"].split(":"))
            end_h, end_m = map(int, p["end"].split(":"))
            start_min = start_h * 60 + start_m
            end_min = end_h * 60 + end_m
            
            if start_min <= current_min < end_min:
                return p
        
        return periods[0]


class MuhurtaChecker:
    """Muhurta — Electional Astrology for trading"""
    
    FAVORABLE_DAYS = [1, 3, 4]  # Mon, Wed, Thu
    GOOD_FOR_TRADE = ["Taurus", "Cancer", "Libra", "Capricorn", "Aquarius"]
    
    @classmethod
    def check(cls, dt: datetime, positions: PlanetaryPositions) -> Dict:
        """Check if this is a good Muhurta for trading"""
        moon_nak, pada = positions.get_nakshatra("moon")
        moon_sign = positions.get_sign("moon")
        chogh = ChoghadiyaCalculator.get_current(dt)
        
        # Scores
        nak_score = 90 if moon_nak in TRADING_NAKSHATRAS else 30 if moon_nak in BAD_NAKSHATRAS else 50
        sign_score = 85 if moon_sign in cls.GOOD_FOR_TRADE else 50
        day_score = 80 if dt.weekday() in cls.FAVORABLE_DAYS else 50
        chogh_score = 100 if chogh["type"] == "best" else 75 if chogh["type"] == "good" else 25
        
        total = (nak_score * 0.3 + sign_score * 0.2 + day_score * 0.2 + chogh_score * 0.3)
        
        return {
            "datetime": dt.strftime("%Y-%m-%d %H:%M"),
            "moon_nakshatra": moon_nak,
            "moon_pada": pada,
            "moon_sign": moon_sign,
            "choghadiya": f"{chogh['name']} {chogh['icon']}",
            "scores": {"nakshatra": nak_score, "sign": sign_score, "day": day_score, "choghadiya": chogh_score},
            "total_score": round(total, 1),
            "verdict": "🟢 EXCELLENT" if total >= 80 else "🟡 GOOD" if total >= 60 else "🟠 CAUTION" if total >= 40 else "🔴 AVOID",
            "advice": cls._get_advice(total, moon_nak, chogh)
        }
    
    @staticmethod
    def _get_advice(score: float, nakshatra: str, choghadiya: Dict) -> str:
        advice = []
        if score >= 80:
            advice.append("Отличное время для сделок!")
        elif score < 40:
            advice.append("Избегать торговли!")
        
        if nakshatra in BAD_NAKSHATRAS:
            advice.append(f"⚠️ Накшатра {nakshatra} опасна")
        
        if choghadiya["type"] == "bad":
            advice.append(f"⚠️ Чогхидия {choghadiya['name']} плоха")
        
        return ". ".join(advice) if advice else "Нейтральное время"


class VedicAstrologer:
    """Main Vedic Astrology Agent"""
    
    def __init__(self, lat: float = 28.6139, lon: float = 77.2090):
        self.lat = lat
        self.lon = lon
    
    def analyze(self, dt: datetime = None) -> Dict:
        """Full Vedic analysis"""
        dt = dt or datetime.now()
        jd = SwissEphemeris.julian_day(dt)
        ayanamsa = SwissEphemeris.calculate_ayanamsa(jd)
        positions = SwissEphemeris.get_planetary_positions(dt, ayanamsa)
        
        # Moon phase
        phase, illumination = SwissEphemeris.moon_phase(jd)
        
        # Nakshatra
        nakshatra, pada = positions.get_nakshatra("moon")
        nak_qual = self._get_nakshatra_quality(nakshatra)
        
        # Muhurta
        muhurta = MuhurtaChecker.check(dt, positions)
        
        # Financial indicators
        financial_signal = self._get_financial_signal(positions, nakshatra, illumination)
        
        return {
            "timestamp": dt.isoformat(),
            "location": {"lat": self.lat, "lon": self.lon},
            "vedic": {
                "nakshatra": nakshatra,
                "pada": pada,
                "nak_quality": nak_qual,
                "moon_sign": positions.get_sign("moon"),
                "ayanamsa": round(ayanamsa, 2),
            },
            "choghadiya": ChoghadiyaCalculator.get_current(dt),
            "muhurta": muhurta,
            "moon_phase": {"name": phase, "illumination": round(illumination, 1)},
            "financial": financial_signal,
            "planets": self._format_planets(positions),
        }
    
    def _get_nakshatra_quality(self, nak: str) -> Dict:
        qualities = {
            "Rohini": {"nature": "Growth", "trade": "BULLISH"},
            "Mrigashira": {"nature": "Search", "trade": "BULLISH"},
            "Swati": {"nature": "Trade", "trade": "BULLISH"},
            "Hasta": {"nature": "Skill", "trade": "BULLISH"},
            "Ashlesha": {"nature": "Deception", "trade": "BEARISH"},
            "Magha": {"nature": "Authority", "trade": "NEUTRAL"},
            "Mula": {"nature": "Root", "trade": "BEARISH"},
            "Ardra": {"nature": "Transform", "trade": "VOLATILE"},
        }
        return qualities.get(nak, {"nature": "Neutral", "trade": "NEUTRAL"})
    
    def _get_financial_signal(self, pos: PlanetaryPositions, nakshatra: str, illumination: float) -> Dict:
        """Determine financial signal based on planetary positions"""
        moon_sign = pos.get_sign("moon")
        jupiter_sign = pos.get_sign("jupiter")
        venus_sign = pos.get_sign("venus")
        
        # Favorable signs for finance
        bull_signs = ["Taurus", "Cancer", "Libra", "Capricorn", "Aquarius"]
        bear_signs = ["Aries", "Leo", "Scorpio", "Sagittarius"]
        
        score = 50
        
        if moon_sign in bull_signs:
            score += 15
        elif moon_sign in bear_signs:
            score -= 15
        
        if jupiter_sign in bull_signs:
            score += 10
        if venus_sign in bull_signs:
            score += 10
        
        # Moon illumination effect
        if illumination < 25:  # New Moon
            score += 10
        elif illumination > 75:  # Full Moon
            score += 5
        
        # Nakshatra effect
        trade_naks = ["Rohini", "Mrigashira", "Swati", "Hasta", "Shravana"]
        if nakshatra in trade_naks:
            score += 10
        
        signal = "BULLISH" if score >= 65 else "BEARISH" if score <= 35 else "NEUTRAL"
        
        return {
            "signal": signal,
            "score": min(100, max(0, score)),
            "confidence": abs(score - 50) + 20
        }
    
    def _format_planets(self, pos: PlanetaryPositions) -> Dict:
        return {
            "sun": {"sign": pos.get_sign("sun"), "degee": round(pos.get_degree("sun"), 1)},
            "moon": {"sign": pos.get_sign("moon"), "degree": round(pos.get_degree("moon"), 1)},
            "mars": {"sign": pos.get_sign("mars"), "degree": round(pos.get_degree("mars"), 1)},
            "mercury": {"sign": pos.get_sign("mercury"), "degree": round(pos.get_degree("mercury"), 1)},
            "jupiter": {"sign": pos.get_sign("jupiter"), "degree": round(pos.get_degree("jupiter"), 1)},
            "venus": {"sign": pos.get_sign("venus"), "degree": round(pos.get_degree("venus"), 1)},
            "saturn": {"sign": pos.get_sign("saturn"), "degree": round(pos.get_degree("saturn"), 1)},
        }
