#!/usr/bin/env python3
"""
asurdev Sentinel — Forecast for 22.03.2026
============================================
"""

import math
from datetime import datetime

MOON_PHASES = ["New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
               "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent"]

NAKSHATRAS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
              "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
              "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
              "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha",
              "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"]

ZODIAC_SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
                "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

EXALTATION = {
    "Sun": {"sign": "Aries", "degree": 19},
    "Moon": {"sign": "Taurus", "degree": 3},
    "Mercury": {"sign": "Virgo", "degree": 15},
    "Venus": {"sign": "Pisces", "degree": 27},
    "Mars": {"sign": "Capricorn", "degree": 28},
    "Jupiter": {"sign": "Cancer", "degree": 15},
    "Saturn": {"sign": "Libra", "degree": 21},
}

FALL = {
    "Sun": "Libra", "Moon": "Scorpio", "Mercury": "Pisces",
    "Venus": "Virgo", "Mars": "Cancer", "Jupiter": "Capricorn", "Saturn": "Aries"
}


def calculate_julian_date(dt: datetime) -> float:
    year, month, day = dt.year, dt.month, dt.day + dt.hour/24 + dt.minute/1440
    if month <= 2:
        year -= 1
        month += 12
    A = int(year / 100)
    B = 2 - A + int(A / 4)
    return int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + B - 1524.5


def get_moon_position(jd: float):
    D = jd - 2451550.1
    T = D / 36525
    L0 = (218.3164477 + 481267.88123421 * T) % 360
    l = (134.9633964 + 477198.8675055 * T) % 360
    F = (93.2720950 + 483202.0175233 * T) % 360
    moon_lon = (L0 + 6.289 * math.sin(math.radians(l))) % 360
    moon_lat = 5.128 * math.sin(math.radians(F))
    return moon_lon, moon_lat


def get_sun_position(jd: float) -> float:
    D = jd - 2451550.1
    T = D / 36525
    L0 = (280.46646 + 36000.76983 * T) % 360
    M = (357.5291092 + 35999.0502909 * T) % 360
    C = 1.914602 * math.sin(math.radians(M)) + 0.019993 * math.sin(math.radians(2 * M))
    return (L0 + C) % 360


def get_moon_phase(jd: float):
    D = jd - 2451550.1
    age = D % 29.530588853
    idx = int((age / 29.530588853) * 8) % 8
    illumination = (1 - math.cos(math.radians(age / 29.530588853 * 360))) / 2
    return MOON_PHASES[idx], illumination, age


def get_nakshatra(jd: float):
    D = jd - 2451550.1
    age = D % 29.530588853
    nak_index = int((age / 29.530588853) * 27) % 27
    pada = int((age % 29.530588853) / 3.75) + 1
    return NAKSHATRAS[nak_index], pada


def get_zodiac_sign(degree: float):
    sign_index = int(degree / 30) % 12
    degree_in_sign = degree % 30
    return ZODIAC_SIGNS[sign_index], degree_in_sign


def calculate_dignity_score(planet: str, sign: str) -> int:
    score = 0
    if planet in EXALTATION and EXALTATION[planet]["sign"] == sign:
        score += 5
    if planet in FALL and FALL[planet] == sign:
        score -= 4
    fire_signs = ["Aries", "Leo", "Sagittarius"]
    earth_signs = ["Taurus", "Virgo", "Capricorn"]
    if sign in fire_signs and planet in ["Sun", "Jupiter"]:
        score += 3
    elif sign in earth_signs and planet in ["Moon", "Venus"]:
        score += 3
    return score


NAKSHATRA_PROPS = {
    "Ashwini": {"element": "Fire", "signal": "BULLISH", "desc": "Быстрое действие"},
    "Bharani": {"element": "Earth", "signal": "BULLISH", "desc": "Сила, плодовитость"},
    "Krittika": {"element": "Fire", "signal": "NEUTRAL", "desc": "Острый, критический"},
    "Rohini": {"element": "Earth", "signal": "STRONG_BULLISH", "desc": "Рост, процветание"},
    "Mrigashira": {"element": "Air", "signal": "NEUTRAL", "desc": "Поиск"},
    "Ardra": {"element": "Water", "signal": "BEARISH", "desc": "Разрушение, трансформация"},
    "Punarvasu": {"element": "Earth", "signal": "BULLISH", "desc": "Восстановление"},
    "Pushya": {"element": "Air", "signal": "STRONG_BULLISH", "desc": "Изобилие"},
    "Ashlesha": {"element": "Water", "signal": "BEARISH", "desc": "Обман"},
    "Magha": {"element": "Earth", "signal": "NEUTRAL", "desc": "Власть"},
    "Purva Phalguni": {"element": "Fire", "signal": "BULLISH", "desc": "Дружба"},
    "Uttara Phalguni": {"element": "Earth", "signal": "BULLISH", "desc": "Помощь"},
    "Hasta": {"element": "Air", "signal": "NEUTRAL", "desc": "Мастерство"},
    "Chitra": {"element": "Water", "signal": "BULLISH", "desc": "Прибыль"},
    "Swati": {"element": "Air", "signal": "NEUTRAL", "desc": "Независимость"},
    "Vishakha": {"element": "Fire", "signal": "BEARISH", "desc": "Амбиции"},
    "Anuradha": {"element": "Water", "signal": "BULLISH", "desc": "Лояльность"},
    "Jyeshtha": {"element": "Earth", "signal": "BEARISH", "desc": "Опасность"},
    "Mula": {"element": "Water", "signal": "BEARISH", "desc": "Корень"},
    "Purva Ashadha": {"element": "Fire", "signal": "BULLISH", "desc": "Победа"},
    "Uttara Ashadha": {"element": "Earth", "signal": "STRONG_BULLISH", "desc": "Победа, истина"},
    "Shravana": {"element": "Air", "signal": "BULLISH", "desc": "Слушание"},
    "Dhanishtha": {"element": "Earth", "signal": "NEUTRAL", "desc": "Богатство"},
    "Shatabhisha": {"element": "Water", "signal": "BEARISH", "desc": "Изоляция"},
    "Purva Bhadrapada": {"element": "Fire", "signal": "NEUTRAL", "desc": "Переход"},
    "Uttara Bhadrapada": {"element": "Earth", "signal": "BULLISH", "desc": "Добродетель"},
    "Revati": {"element": "Water", "signal": "BULLISH", "desc": "Путешествие"},
}


def analyze_date(dt: datetime) -> dict:
    jd = calculate_julian_date(dt)
    moon_lon, moon_lat = get_moon_position(jd)
    sun_lon = get_sun_position(jd)
    moon_phase, illumination, age = get_moon_phase(jd)
    nakshatra, pada = get_nakshatra(jd)
    moon_sign, moon_deg = get_zodiac_sign(moon_lon)
    sun_sign, sun_deg = get_zodiac_sign(sun_lon)
    nak_prop = NAKSHATRA_PROPS.get(nakshatra, {"element": "Unknown", "signal": "NEUTRAL", "desc": ""})
    moon_dignity = calculate_dignity_score("Moon", moon_sign)
    
    # Signal calculation
    signal_score = 0
    if moon_phase in ["New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous"]:
        signal_score += 15
    else:
        signal_score -= 15
    
    if nak_prop["signal"] == "STRONG_BULLISH":
        signal_score += 20
    elif nak_prop["signal"] == "BULLISH":
        signal_score += 10
    elif nak_prop["signal"] == "BEARISH":
        signal_score -= 15
    
    signal_score += moon_dignity * 3
    
    if illumination > 0.9:
        signal_score *= 0.8
    
    if signal_score > 40:
        verdict = "STRONG_BULLISH"
    elif signal_score > 15:
        verdict = "BULLISH"
    elif signal_score > -15:
        verdict = "NEUTRAL"
    elif signal_score > -40:
        verdict = "BEARISH"
    else:
        verdict = "STRONG_BEARISH"
    
    return {
        "datetime": dt.strftime("%Y-%m-%d %H:%M UTC"),
        "moon": {"phase": moon_phase, "illumination": f"{illumination*100:.1f}%", "age_days": f"{age:.2f}",
                 "nakshatra": nakshatra, "pada": pada, "sign": moon_sign, "degree": f"{moon_deg:.2f}°", "dignity": moon_dignity},
        "sun": {"sign": sun_sign, "degree": f"{sun_deg:.2f}°"},
        "nakshatra": nak_prop,
        "signal_score": signal_score,
        "verdict": verdict,
        "confidence": min(abs(signal_score) + 30, 95),
    }


def main():
    target_date = datetime(2026, 3, 22, 12, 0)  # 22.03.2026 12:00 UTC
    
    print("=" * 60)
    print("🔮 asurdev SENTINEL — FORECAST")
    print("=" * 60)
    print(f"📅 Target Date: {target_date.strftime('%d.%m.%Y')} (Sunday)")
    print("=" * 60)
    
    analysis = analyze_date(target_date)
    
    print(f"\n🌙 LUNAR STATE")
    print(f"   Phase: {analysis['moon']['phase']}")
    print(f"   Illumination: {analysis['moon']['illumination']}")
    print(f"   Age: {analysis['moon']['age_days']} days")
    
    print(f"\n⭐ NAKSHATRA")
    print(f"   Name: {analysis['moon']['nakshatra']} (Pada {analysis['moon']['pada']})")
    print(f"   Element: {analysis['nakshatra']['element']}")
    print(f"   Signal: {analysis['nakshatra']['signal']}")
    print(f"   Description: {analysis['nakshatra']['desc']}")
    
    print(f"\n🏛️ ZODIAC POSITIONS")
    print(f"   Moon: {analysis['moon']['sign']} {analysis['moon']['degree']} (Dignity: {analysis['moon']['dignity']})")
    print(f"   Sun:  {analysis['sun']['sign']} {analysis['sun']['degree']}")
    
    print(f"\n📊 SIGNAL CALCULATION")
    print(f"   Score: {analysis['signal_score']}")
    print(f"   Verdict: {analysis['verdict']}")
    print(f"   Confidence: {analysis['confidence']:.0f}%")
    
    print("\n" + "=" * 60)
    print(f"🎯 FINAL FORECAST: {analysis['verdict']}")
    print("=" * 60)
    
    # Technical check
    print("\n📈 TECHNICAL NOTE:")
    print("   Date is Sunday — typically low liquidity")
    print("   Weekend effect may amplify moves")
    
    # Risk
    print("\n⚠️ RISK PARAMETERS:")
    if analysis['verdict'] in ["STRONG_BULLISH", "BULLISH"]:
        print("   Max Risk: 2-3%")
        print("   Position Size: 15-20%")
        print("   Stop Loss: Below key support")
    elif analysis['verdict'] == "NEUTRAL":
        print("   Max Risk: 5%")
        print("   Position Size: 10%")
        print("   Range-bound strategy")
    else:
        print("   Max Risk: 2-3%")
        print("   Position Size: 10-15%")
        print("   Focus on shorts or cash")


if __name__ == "__main__":
    main()
