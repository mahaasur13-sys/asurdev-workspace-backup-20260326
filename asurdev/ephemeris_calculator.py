#!/usr/bin/env python3
"""
asurdev Sentinel - Swiss Ephemeris Calculator
Точный расчёт планетных позиций для марта 2026
Использует: pyswisseph 2.10.03 + sepl_23.se1, semm_23.se1, seas_23.se1
"""

import swisseph as swe
import json
from datetime import datetime
from pathlib import Path

# Константы планет (без префикса SE в pyswisseph)
from swisseph import (
    SUN, MOON, MERCURY, VENUS, MARS, JUPITER, SATURN, 
    URANUS, NEPTUNE, PLUTO, CHIRON
)

# Путь к файлам эфемерид
EPHE_PATH = Path(__file__).parent / "ephemeris"
swe.set_ephe_path(str(EPHE_PATH))

# Флаги расчёта
FLG_SWIEPH = swe.FLG_SWIEPH | swe.FLG_SPEED

# Названия планет
PLANETS = {
    SUN: "Солнце",
    MOON: "Луна",
    MERCURY: "Меркурий",
    VENUS: "Венера",
    MARS: "Марс",
    JUPITER: "Юпитер",
    SATURN: "Сатурн",
    URANUS: "Уран",
    NEPTUNE: "Нептун",
    PLUTO: "Плутон",
    CHIRON: "Хирон",
}

# Знаки зодиака
SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", 
         "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]

# Накшатры (27 лунных станций)
NAKSHATRAS = [
    "Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Ардра",
    "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пхалгуни", "Уттара-пхалгуни",
    "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха",
    "Мула", "Пурва-ашадха", "Уттара-ашадха", "Шравана", "Дханишта", "Шатабхиша",
    "Пурва-бхадра", "Уттара-бхадра", "Ревати"
]


def julian_day(date_str: str) -> float:
    """Конвертация даты в юлианский день."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return swe.julday(dt.year, dt.month, dt.day, 12.0)


def get_planet_position(jd: float, planet_id: int) -> tuple[float, float, float]:
    """Получить эклиптическую долготу, широту и скорость планеты."""
    result = swe.calc(jd, planet_id, FLG_SWIEPH)
    return result[0][0], result[0][1], result[0][3]  # lng, lat, speed


def zodiac_position(longitude: float) -> tuple[str, float]:
    """Конвертация долготы в знак и градусы внутри знака."""
    sign_index = int(longitude // 30)
    degree_in_sign = longitude % 30
    return SIGNS[sign_index], degree_in_sign


def nakshatra_position(longitude: float) -> tuple[str, float]:
    """Расчёт накшатры (27 лунных станций)."""
    nak_index = int(longitude // (13 + 1/3)) % 27
    degree_in_nakshatra = (longitude % (13 + 1/3)) / (13 + 1/3) * 100
    return NAKSHATRAS[nak_index], degree_in_nakshatra


def calculate_day(date_str: str, lat: float = 55.75, lon: float = 37.62) -> dict:
    """Полный расчёт дня."""
    jd = julian_day(date_str)
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    
    positions = {}
    for planet_id, name in PLANETS.items():
        lng, lat_planet, speed = get_planet_position(jd, planet_id)
        sign, deg_in_sign = zodiac_position(lng)
        nak, nak_deg = nakshatra_position(lng)
        
        positions[name] = {
            "longitude": round(lng, 4),
            "sign": sign,
            "degree_in_sign": round(deg_in_sign, 2),
            "nakshatra": nak,
            "nakshatra_pada": int(nak_deg // 25) + 1,
            "latitude": round(lat_planet, 4),
            "speed": round(speed, 4),
        }
    
    # Луна для текущего дня
    moon_lng = positions["Луна"]["longitude"]
    moon_sign, moon_deg = zodiac_position(moon_lng)
    moon_nak, moon_nak_deg = nakshatra_position(moon_lng)
    
    return {
        "date": date_str,
        "date_display": dt.strftime("%d %B %Y"),
        "day_of_week": dt.strftime("%A"),
        "jd": round(jd, 6),
        "planets": positions,
        "moon": {
            "sign": moon_sign,
            "degree": round(moon_deg, 2),
            "nakshatra": moon_nak,
            "nakshatra_pada": int(moon_nak_deg // 25) + 1,
        },
        "location": {"lat": lat, "lon": lon},
    }


def calculate_aspects_day(date_str: str) -> list[dict]:
    """Расчёт аспектов на день."""
    jd = julian_day(date_str)
    positions = {}
    
    for planet_id, name in PLANETS.items():
        lng, _, _ = get_planet_position(jd, planet_id)
        positions[name] = lng
    
    aspects_found = []
    planets = list(positions.keys())
    
    for i, p1 in enumerate(planets):
        for p2 in planets[i+1:]:
            diff = abs(positions[p1] - positions[p2])
            if diff > 180:
                diff = 360 - diff
            
            # Определение аспекта
            aspect_info = None
            if diff <= 10:
                aspect_info = {"type": "соединение", "symbol": " ✶ ", "name_ru": "соединение"}
            elif 55 <= diff <= 65:
                aspect_info = {"type": "секстиль", "symbol": " ✶ ", "name_ru": "секстиль"}
            elif 85 <= diff <= 95:
                aspect_info = {"type": "квадрат", "symbol": " □ ", "name_ru": "квадрат"}
            elif 115 <= diff <= 125:
                aspect_info = {"type": "трин", "symbol": " △ ", "name_ru": "трин"}
            elif 175 <= diff <= 185:
                aspect_info = {"type": "оппозиция", "symbol": " ☍ ", "name_ru": "оппозиция"}
            
            if aspect_info:
                aspects_found.append({
                    "planet1": p1,
                    "planet2": p2,
                    "angle": round(diff, 1),
                    **aspect_info
                })
    
    return aspects_found


def generate_month(year: int, month: int, lat: float = 55.75, lon: float = 37.62) -> list:
    """Генерация данных на месяц."""
    data = []
    days_in_month = 31 if month in [1,3,5,7,8,10,12] else 30
    if month == 2:
        days_in_month = 29 if (year % 4 == 0 and year % 100 != 0) or year % 400 == 0 else 28
    
    for day in range(1, days_in_month + 1):
        date_str = f"{year:04d}-{month:02d}-{day:02d}"
        day_data = calculate_day(date_str, lat, lon)
        aspects = calculate_aspects_day(date_str)
        day_data["aspects"] = aspects
        data.append(day_data)
    
    return data


def save_json(data: list, filename: str):
    """Сохранение в JSON."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    print("🪐 asurdev Sentinel - Swiss Ephemeris Calculator")
    print("=" * 50)
    print(f"Версия Swiss Ephemeris: {swe.version}")
    print(f"Путь к эфемеридам: {EPHE_PATH}")
    print()
    
    # Тестовый расчёт - 21 марта 2026
    test_day = calculate_day("2026-03-21", 55.75, 37.62)
    print(f"📅 {test_day['date_display']} ({test_day['day_of_week']})")
    print(f"   Юлианский день: {test_day['jd']}")
    print()
    
    print("🪐 Позиции планет:")
    for name, pdata in test_day["planets"].items():
        print(f"   {name:10} {pdata['sign']:12} {pdata['degree_in_sign']:5.2f}°  "
              f"Накшатра: {pdata['nakshatra']} ({pdata['nakshatra_pada']} пада)")
    
    print()
    print("🌙 Луна:")
    m = test_day["moon"]
    print(f"   Знак: {m['sign']} {m['degree']}°")
    print(f"   Накшатра: {m['nakshatra']} ({m['nakshatra_pada']} пада)")
    
    # Аспекты
    aspects = calculate_aspects_day("2026-03-21")
    print()
    print("✧ Аспекты на 21 марта:")
    for asp in aspects:
        print(f"   {asp['planet1']} {asp['symbol']} {asp['planet2']} ({asp['angle']}°)")
    
    # Генерация месяца
    print()
    print("📊 Генерация марта 2026...")
    march_2026 = generate_month(2026, 3, 55.75, 37.62)
    save_json(march_2026, "march_2026_ephemeris.json")
    print(f"   ✓ Сохранено: march_2026_ephemeris.json ({len(march_2026)} дней)")
