"""
Indian Astrology (Panchang) - Muhurta, Choghadiya, Yoga
Calculations via PyEphem
"""
import ephem
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class Nakshatra:
    name: str
    lord: str
    quality: str
    deity: str


NAKSHATRAS = [
    Nakshatra("Ashwini", "Ketu", "Light", "Aswini"),
    Nakshatra("Bharani", "Venus", "Mobile", "Yama"),
    Nakshatra("Krittika", "Sun", "Sharp", "Agni"),
    Nakshatra("Rohini", "Moon", "Stable", "Brahma"),
    Nakshatra("Mrigashira", "Mars", "Mobile", "Soma"),
    Nakshatra("Ardra", "Rahu", "Sharp", "Rudra"),
    Nakshatra("Punarvasu", "Jupiter", "Benefic", "Aditi"),
    Nakshatra("Pushya", "Saturn", "Fixed", "Brihaspati"),
    Nakshatra("Ashlesha", "Mercury", "Poison", "Agni"),
    Nakshatra("Magha", "Ketu", "Royal", "Pitri"),
    Nakshatra("Purva Phalguni", "Venus", "Benefic", "Bhaga"),
    Nakshatra("Uttara Phalguni", "Sun", "Benefic", "Aryaman"),
    Nakshatra("Hasta", "Moon", "Light", "Savitr"),
    Nakshatra("Chitra", "Mars", "Sharp", "Tvashtar"),
    Nakshatra("Swati", "Rahu", "Mobile", "Vayu"),
    Nakshatra("Vishakha", "Jupiter", "Mixed", "Indra-Agni"),
    Nakshatra("Anuradha", "Saturn", "Light", "Mitra"),
    Nakshatra("Jyeshtha", "Mercury", "Sharp", "Indra"),
    Nakshatra("Mula", "Ketu", "Root", "Nirriti"),
    Nakshatra("Purva Ashadha", "Venus", "Invincible", "Aph"),
    Nakshatra("Uttara Ashadha", "Sun", "Fixed", "Vishwa"),
    Nakshatra("Shravana", "Moon", "Mobile", "Vishnu"),
    Nakshatra("Dhanishtha", "Mars", "Rich", "Vasava"),
    Nakshatra("Shatabhisha", "Rahu", "Hidden", "Varuna"),
    Nakshatra("Purva Bhadrapada", "Jupiter", "Silent", "Aja-Ekapada"),
    Nakshatra("Uttara Bhadrapada", "Saturn", "Useful", "Ahirbudhya"),
    Nakshatra("Revati", "Mercury", "Rich", "Pushan"),
]


@dataclass
class Choghadiya:
    name: str
    type: str
    quality: str


CHOGHADIYAS = [
    Choghadiya("Amrit", "Good", "Nectar"),
    Choghadiya("Shubh", "Good", "Auspicious"),
    Choghadiya("Labh", "Good", "Profit"),
    Choghadiya("Char", "Neutral", "Moveable"),
    Choghadiya("Ushada", "Mixed", "Innovation"),
    Choghadiya("Vyatipata", "Bad", "Misfortune"),
    Choghadiya("Sadhya", "Neutral", "Favorable"),
    Choghadiya("Kaul", "Good", "Wealth"),
]


def calculate_nakshatra(dt: datetime, lat: float, lon: float) -> Tuple[Nakshatra, float]:
    try:
        date_str = dt.strftime("%Y/%m/%d")
        time_str = dt.strftime("%H:%M:%S")
        
        observer = ephem.Observer()
        observer.lat = str(lat)
        observer.lon = str(lon)
        observer.date = f"{date_str} {time_str}"
        
        moon = ephem.Moon(observer)
        moon_ecl_lon = float(moon.hlon)
        
        nak_index = int((moon_ecl_lon % 360) / 13.333) % 27
        nak_pos = (moon_ecl_lon % 360) % 13.333
        
        return NAKSHATRAS[nak_index], nak_pos
    except Exception:
        return NAKSHATRAS[0], 0.0


def calculate_choghadiya(dt: datetime) -> Tuple[Choghadiya, datetime]:
    sunrise = _get_sunrise(dt)
    weekday = dt.weekday()
    
    choghadiya_start = sunrise + timedelta(hours=weekday * 24 / 8)
    
    hour_of_day = ((dt.hour * 60 + dt.minute) % (24 * 60)) / (24 * 60) * 8
    chogh_index = int(hour_of_day) % 8
    
    return CHOGHADIYAS[chogh_index], choghadiya_start


def _get_sunrise(dt: datetime) -> datetime:
    try:
        date_str = dt.strftime("%Y/%m/%d")
        observer = ephem.Observer()
        observer.lat = "28.6139"
        observer.lon = "77.2090"
        observer.date = date_str
        
        sunrise = observer.next_rising(ephem.Sun())
        return datetime.fromtimestamp(sunrise.datetime())
    except Exception:
        return dt.replace(hour=6, minute=30, second=0)


def get_muhurta_score(dt: datetime, lat: float, lon: float, action: str = "buy") -> Dict:
    nakshatra, nak_pos = calculate_nakshatra(dt, lat, lon)
    choghadiya, _ = calculate_choghadiya(dt)
    
    score = 50
    factors = []
    
    good_nakshatras = ["Rohini", "Mrigashira", "Pushya", "Hasta", "Swati", "Shravana", "Dhanishtha", "Revati"]
    if nakshatra.name in good_nakshatras:
        score += 20
        factors.append(f"Good nakshatra: {nakshatra.name}")
    elif nakshatra.name in ["Ashlesha", "Jyeshtha", "Mula"]:
        score -= 20
        factors.append(f"Difficult nakshatra: {nakshatra.name}")
    
    if choghadiya.type == "Good":
        score += 15
        factors.append(f"Good choghadiya: {choghadiya.name}")
    elif choghadiya.type == "Bad":
        score -= 15
        factors.append(f"Bad choghadiya: {choghadiya.name}")
    
    weekday = dt.weekday()
    if action.lower() == "buy" and weekday in [1, 2, 4, 6]:
        score += 10
        factors.append("Good day for buying")
    elif action.lower() == "sell" and weekday in [0, 3, 5]:
        score += 10
        factors.append("Good day for selling")
    
    score = max(0, min(100, score))
    
    return {
        "score": score,
        "nakshatra": nakshatra.name,
        "nakshatra_lord": nakshatra.lord,
        "choghadiya": choghadiya.name,
        "choghadiya_type": choghadiya.type,
        "factors": factors,
        "recommendation": "good" if score >= 60 else "neutral" if score >= 40 else "bad"
    }


def get_planetary_positions(dt: datetime, lat: float, lon: float) -> Dict:
    try:
        date_str = dt.strftime("%Y/%m/%d")
        time_str = dt.strftime("%H:%M:%S")
        
        observer = ephem.Observer()
        observer.lat = str(lat)
        observer.lon = str(lon)
        observer.date = f"{date_str} {time_str}"
        
        planets = {}
        for name in ["Mercury", "Venus", "Mars", "Jupiter", "Saturn"]:
            body = getattr(ephem, name)(observer)
            planets[name.lower()] = {
                "ecl_lon": float(body.hlon),
                "ecl_lat": float(body.hlat),
                "sign": _ecl_to_sign(float(body.hlon))
            }
        
        moon = ephem.Moon(observer)
        planets["moon"] = {
            "ecl_lon": float(moon.hlon),
            "ecl_lat": float(moon.hlat),
            "sign": _ecl_to_sign(float(moon.hlon)),
            "phase": _moon_phase(float(moon.hlon))
        }
        
        return planets
    except Exception:
        return {}


def _ecl_to_sign(ecl_lon: float) -> str:
    signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    return signs[int(ecl_lon / 30) % 12]


def _moon_phase(ecl_lon: float) -> str:
    phase = (ecl_lon % 360) / 360 * 8
    if phase < 1 or phase > 7:
        return "New Moon"
    elif phase < 2:
        return "Waxing Crescent"
    elif phase < 3:
        return "First Quarter"
    elif phase < 4:
        return "Waxing Gibbous"
    elif phase < 5:
        return "Full Moon"
    elif phase < 6:
        return "Waning Gibbous"
    elif phase < 7:
        return "Last Quarter"
    else:
        return "Waning Crescent"


class IndianAstrologer:
    def __init__(self, lat: float = 28.6139, lon: float = 77.2090):
        self.lat = lat
        self.lon = lon
    
    def analyze(self, symbol: str, action: str = "buy") -> Dict:
        now = datetime.now()
        
        muhurta = get_muhurta_score(now, self.lat, self.lon, action)
        planets = get_planetary_positions(now, self.lat, self.lon)
        nakshatra, nak_pos = calculate_nakshatra(now, self.lat, self.lon)
        
        signal = "NEUTRAL"
        confidence = 50
        
        if muhurta["recommendation"] == "good":
            signal = "BULLISH"
            confidence = 70
        elif muhurta["recommendation"] == "bad":
            signal = "BEARISH"
            confidence = 70
        
        return {
            "signal": signal,
            "confidence": confidence,
            "summary": f"Nakshatra: {nakshatra.name}, Choghadiya: {muhurta['choghadiya']}",
            "details": {
                "muhurta_score": muhurta["score"],
                "nakshatra": nakshatra.name,
                "nakshatra_lord": nakshatra.lord,
                "nakshatra_quality": nakshatra.quality,
                "choghadiya": muhurta["choghadiya"],
                "choghadiya_type": muhurta["choghadiya_type"],
                "factors": muhurta["factors"],
                "planets": planets,
                "recommendation": muhurta["recommendation"]
            }
        }


def get_indian_astrologer(lat: float = 28.6139, lon: float = 77.2090) -> IndianAstrologer:
    return IndianAstrologer(lat, lon)


if __name__ == "__main__":
    ia = IndianAstrologer()
    result = ia.analyze("BTC", "buy")
    print(f"Signal: {result['signal']}")
    print(f"Confidence: {result['confidence']}%")
    print(f"Summary: {result['summary']}")
    print(f"Muhurta Score: {result['details']['muhurta_score']}")
