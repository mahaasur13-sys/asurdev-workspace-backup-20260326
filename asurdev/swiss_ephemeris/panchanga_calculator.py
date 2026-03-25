"""
Panchanga Calculator — Vedic Calendar Elements
===============================================
Optimized calculations with @lru_cache for all sub-functions.
60 precise Karana (0-59) with correct numbering.
"""

from functools import lru_cache
from typing import Dict, Tuple

# =============================================================================
# CONSTANTS
# =============================================================================

YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
    "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata",
    "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyan", "Parigha",
    "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti"
]

INAUSPICIOUS_YOGAS = {
    "Atiganda", "Shula", "Ganda", "Vyaghata", "Vajra", "Vyatipata", "Parigha", "Vaidhriti"
}
NEUTRAL_YOGAS = {"Vishkambha", "Shobhana", "Dhriti"}

TITHI_NAMES = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi",
    "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi",
    "Trayodashi", "Chaturdashi", "Purnima/Amavasya"
]

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

# 60 Karana names (11 base names cycle)
KARANA_NAMES_60 = [
    # First lunar day (Tithi 1) - 60 Karana per sidereal day
    "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti",
    "Shakuni", "Chatushpada", "Naga", "Kimstughna",
    # Tithi 2
    "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti",
    "Shakuni", "Chatushpada", "Naga", "Kimstughna",
    # Tithi 3
    "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti",
    "Shakuni", "Chatushpada", "Naga", "Kimstughna",
    # Tithi 4
    "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti",
    "Shakuni", "Chatushpada", "Naga", "Kimstughna",
    # Tithi 5
    "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti",
    "Shakuni", "Chatushpada", "Naga", "Kimstughna",
    # Tithi 6
    "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti",
    "Shakuni", "Chatushpada", "Naga", "Kimstughna",
]

# Weekday names
WEEKDAY_NAMES = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

# =============================================================================
# HELPER FUNCTIONS (cached)
# =============================================================================

@lru_cache(maxsize=1024)
def _jd_to_hms(jd_val: float) -> str:
    """Convert Julian Day to HH:MM:SS string."""
    import swisseph as swe
    d = swe.revjul(jd_val)
    hours = d[3]
    h = int(hours)
    m = int((hours - h) * 60)
    s = int(((hours - h) * 60 - m) * 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


@lru_cache(maxsize=512)
def _get_weekday_idx(jd_sunrise: float) -> int:
    """Get weekday index from JD (0=Sunday)."""
    import swisseph as swe
    d = swe.revjul(jd_sunrise)
    from datetime import datetime
    dt = datetime(int(d[0]), int(d[1]), int(d[2]))
    return dt.weekday()


# =============================================================================
# MAIN PANCHANGA CALCULATION (cached)
# =============================================================================

@lru_cache(maxsize=512)
def calculate_panchanga(
    jd: float,
    sun_lon: float,
    moon_lon: float,
    sunrise_jd: float,
    sunset_jd: float,
    weekday_idx: int
) -> Dict:
    """
    Calculate complete Panchanga (5 limbs of Hindu calendar).
    
    Args:
        jd: Julian Day (UT) for the time of interest
        sun_lon: Sun's ecliptic longitude (degrees)
        moon_lon: Moon's ecliptic longitude (degrees)
        sunrise_jd: Julian Day of sunrise
        sunset_jd: Julian Day of sunset
        weekday_idx: 0=Sunday, 1=Monday, ... 6=Saturday
    
    Returns:
        Dict with vara, tithi, nakshatra, yoga, karana, sunrise, sunset
    """
    # ----- TITHI -----
    diff = (moon_lon - sun_lon) % 360.0
    tithi_num = int(diff // 12) + 1
    paksha = "Shukla" if tithi_num <= 15 else "Krishna"
    tithi = f"{paksha} {TITHI_NAMES[(tithi_num - 1) % 15]}"
    
    # ----- NAKSHATRA -----
    nakshatra_num = int((moon_lon % 360.0) // (360.0 / 27)) + 1
    nakshatra = NAKSHATRA_NAMES[(nakshatra_num - 1) % 27]
    
    # Nakshatra pada (quarter) - each nakshatra has 4 padas
    nak_degrees = (moon_lon % (360.0 / 27))  # degrees within nakshatra
    nak_span = 360.0 / 27  # ~13°20'
    pada = int(nak_degrees / (nak_span / 4)) % 4 + 1
    
    # ----- YOGA -----
    yoga_deg = (sun_lon + moon_lon) % 360.0
    yoga_span = 360.0 / 27
    yoga_num = int(yoga_deg // yoga_span) + 1
    yoga_progress = yoga_deg % yoga_span
    yoga_remaining = yoga_span - yoga_progress
    yoga = YOGA_NAMES[(yoga_num - 1) % 27]
    yoga_category = "Inauspicious" if yoga in INAUSPICIOUS_YOGAS else "Neutral" if yoga in NEUTRAL_YOGAS else "Auspicious"
    
    # ----- KARANA (60 precise) -----
    # Karana = half of a tithi. There are 60 unique Karana in a sidereal day.
    # The formula: (moon_lon - sun_lon) / 6 gives the 60 Karana index (0-59)
    karana_num_60 = int(diff // 6) % 60
    karana = KARANA_NAMES_60[karana_num_60 % 60]
    
    # ----- VARA (weekday) -----
    vara = WEEKDAY_NAMES[weekday_idx % 7]
    
    return {
        "vara": vara,
        "vara_index": weekday_idx,
        "tithi": tithi,
        "tithi_number": tithi_num,
        "tithi_paksha": paksha,
        "nakshatra": nakshatra,
        "nakshatra_number": nakshatra_num,
        "nakshatra_pada": pada,
        "yoga": yoga,
        "yoga_number": yoga_num,
        "yoga_category": yoga_category,
        "yoga_progress_deg": round(yoga_progress, 4),
        "yoga_remaining_deg": round(yoga_remaining, 4),
        "karana": karana,
        "karana_number_60": karana_num_60,  # 0-59 precise numbering
        "sunrise": _jd_to_hms(sunrise_jd),
        "sunrise_jd": sunrise_jd,
        "sunset": _jd_to_hms(sunset_jd),
        "sunset_jd": sunset_jd,
    }


def calculate_panchanga_raw(
    jd: float,
    sun_lon: float,
    moon_lon: float,
    sunrise_jd: float,
    sunset_jd: float
) -> Dict:
    """Non-cached version that computes weekday internally."""
    weekday_idx = _get_weekday_idx(sunrise_jd)
    return calculate_panchanga(jd, sun_lon, moon_lon, sunrise_jd, sunset_jd, weekday_idx)


# =============================================================================
# TRADING SCORES (for financial astrology)
# =============================================================================

NAKSHATRA_TRADING_SCORES = {
    "Ashwini": {"signal": "BULLISH", "score": 65},
    "Bharani": {"signal": "BULLISH", "score": 60},
    "Krittika": {"signal": "NEUTRAL", "score": 55},
    "Rohini": {"signal": "STRONG_BULLISH", "score": 85},
    "Mrigashira": {"signal": "BULLISH", "score": 75},
    "Ardra": {"signal": "VOLATILE", "score": 40},
    "Punarvasu": {"signal": "NEUTRAL", "score": 60},
    "Pushya": {"signal": "BULLISH", "score": 70},
    "Ashlesha": {"signal": "BEARISH", "score": 30},  # Deceptive
    "Magha": {"signal": "NEUTRAL", "score": 50},
    "Purva Phalguni": {"signal": "BULLISH", "score": 70},
    "Uttara Phalguni": {"signal": "BULLISH", "score": 75},
    "Hasta": {"signal": "BULLISH", "score": 75},
    "Chitra": {"signal": "VOLATILE", "score": 55},
    "Swati": {"signal": "STRONG_BULLISH", "score": 80},
    "Vishakha": {"signal": "VOLATILE", "score": 50},
    "Anuradha": {"signal": "BULLISH", "score": 70},
    "Jyeshtha": {"signal": "BEARISH", "score": 35},
    "Mula": {"signal": "BEARISH", "score": 35},
    "Purva Ashadha": {"signal": "NEUTRAL", "score": 55},
    "Uttara Ashadha": {"signal": "BULLISH", "score": 75},
    "Shravana": {"signal": "BULLISH", "score": 70},
    "Dhanishta": {"signal": "NEUTRAL", "score": 55},
    "Shatabhisha": {"signal": "VOLATILE", "score": 45},
    "Purva Bhadrapada": {"signal": "NEUTRAL", "score": 50},
    "Uttara Bhadrapada": {"signal": "BULLISH", "score": 65},
    "Revati": {"signal": "BULLISH", "score": 70},
}

# =============================================================================
# NAKSHATRA SUITABLE ACTIVITIES (for Muhurta)
# =============================================================================

NAKSHATRA_SUITABLE_ACTIVITIES = {
    "Ashwini": {
        "recommended": ["путешествие", "спорт", "быстрые действия"],
        "avoid": ["хирургия", "долгосрочные проекты"],
        "description": "Быстрая, но может быть непредсказуемой"
    },
    "Bharani": {
        "recommended": ["созидание", "сельское хозяйство", "начало"],
        "avoid": ["отпуска", "развлечения"],
        "description": "Сильная энергия для начала проектов"
    },
    "Krittika": {
        "recommended": ["очищение", "ритуалы", "свадьба"],
        "avoid": ["компромиссы", "нерешительность"],
        "description": "Острая, хороша для разрезания узлов"
    },
    "Rohini": {
        "recommended": ["брак", "путешествие", "прибыльные дела"],
        "avoid": ["споры", "агрессия"],
        "description": "Лучшая для процветания и роста"
    },
    "Mrigashira": {
        "recommended": ["охота", "путешествие", "торговля"],
        "avoid": ["посев", "стабильные проекты"],
        "description": "Ищущая, для поиска возможностей"
    },
    "Ardra": {
        "recommended": ["разрушение зла", "революция", "изобретения"],
        "avoid": ["новые начинания", "бракосочетание"],
        "description": "Деструктивная сила, но трансформационная"
    },
    "Punarvasu": {
        "recommended": ["возврат", "восстановление", "образование"],
        "avoid": ["риск", "ссоры"],
        "description": "Возрождение, вторая попытка"
    },
    "Pushya": {
        "recommended": ["благотворительность", "ритуалы", "церемонии"],
        "avoid": ["путешествия", "переезд"],
        "description": "Самая благоприятная для духовных дел"
    },
    "Ashlesha": {
        "recommended": ["тайные дела", "магия", "гипноз"],
        "avoid": ["юридические дела", "открытые действия"],
        "description": "Коварная, требует осторожности"
    },
    "Magha": {
        "recommended": ["ритуалы предков", "наследование", "церемонии"],
        "avoid": ["новые проекты", "путешествия"],
        "description": "Связана с предками и традициями"
    },
    "Purva Phalguni": {
        "recommended": ["брак", "удовольствия", "искусство"],
        "avoid": ["тяжёлый труд", "серьёзные дела"],
        "description": "Вечеринка, любовь и наслаждение"
    },
    "Uttara Phalguni": {
        "recommended": ["дружба", "партнёрство", "служение"],
        "avoid": ["изоляция", "эгоистичные дела"],
        "description": "Дружеская, для коллективной работы"
    },
    "Hasta": {
        "recommended": ["handiwork", "медицина", "образование"],
        "avoid": ["грубость", "насилие"],
        "description": "Ловкость рук, целительство"
    },
    "Chitra": {
        "recommended": ["искусство", "дизайн", "украшение"],
        "avoid": ["рутина", "скука"],
        "description": "Красота, творчество, живопись"
    },
    "Swati": {
        "recommended": ["торговля", "независимая работа", "путешествие"],
        "avoid": ["подчинение", "руководство"],
        "description": "Независимая, для коммерции"
    },
    "Vishakha": {
        "recommended": ["амбициозные проекты", "победа", "армия"],
        "avoid": ["мелкие дела", "нерешительность"],
        "description": "Двойственная, с целеустремлённостью"
    },
    "Anuradha": {
        "recommended": ["дружба", "церемонии", "благотворительность"],
        "avoid": ["изоляция", "одиночество"],
        "description": "Почитание, успех через покровительство"
    },
    "Jyeshtha": {
        "recommended": ["защита", "манипуляция", "стратегия"],
        "avoid": ["откровенность", "новые начинания"],
        "description": "Главенство, но с препятствиями"
    },
    "Mula": {
        "recommended": ["разрушение зла", "корни", "революция"],
        "avoid": ["брак", "нежные дела"],
        "description": "Корень, глубокое разрушение"
    },
    "Purva Ashadha": {
        "recommended": ["непобедимость", "победа", "военные дела"],
        "avoid": ["компромиссы", "слабость"],
        "description": "Несёт непобедимость при правильных условиях"
    },
    "Uttara Ashadha": {
        "recommended": ["справедливость", "закон", "долгосрочные проекты"],
        "avoid": ["обман", "манипуляции"],
        "description": "Праведность, успех через честность"
    },
    "Shravana": {
        "recommended": ["образование", "слушание", "ритуалы"],
        "avoid": ["грубость", "насилие"],
        "description": "Слушание богов, духовный рост"
    },
    "Dhanishta": {
        "recommended": ["богатство", "музыка", "движение"],
        "avoid": ["статичность", "застой"],
        "description": "Звёздная, для накопления"
    },
    "Shatabhisha": {
        "recommended": ["тайные знания", "медицина", "оккультизм"],
        "avoid": ["поверхностность", "мелочность"],
        "description": "Тайная сила, исцеление"
    },
    "Purva Bhadrapada": {
        "recommended": ["очищение", "духовные практики", "философия"],
        "avoid": ["поверхностные развлечения"],
        "description": "Два лица, трансформация"
    },
    "Uttara Bhadrapada": {
        "recommended": ["благотворительность", "духовность", "партнёрство"],
        "avoid": ["эгоизм", "жадность"],
        "description": "Истинная праведность"
    },
    "Revati": {
        "recommended": ["брак", "путешествие", "процветание"],
        "avoid": ["грубость", "насилие"],
        "description": "Защита, плодородие, богатство"
    },
}


@lru_cache(maxsize=128)
def get_nakshatra_suitable_activities(nakshatra: str) -> Dict:
    """Get suitable activities for a nakshatra."""
    return NAKSHATRA_SUITABLE_ACTIVITIES.get(
        nakshatra,
        {
            "recommended": ["общие дела"],
            "avoid": ["неизвестно"],
            "description": "Информация недоступна"
        }
    )


@lru_cache(maxsize=128)
def get_nakshatra_trading_score(nakshatra: str) -> Tuple[str, int]:
    """Get trading signal and score for a nakshatra."""
    data = NAKSHATRA_TRADING_SCORES.get(nakshatra, {"signal": "NEUTRAL", "score": 50})
    return data["signal"], data["score"]
