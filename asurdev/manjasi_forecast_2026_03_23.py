#!/usr/bin/env python3
"""
Манкаси Прогноз на 23.03.2026
==============================
Система анализа домов по Майклу Манкаси
"""

import json

# Данные на 23.03.2026 из эфемерид
ephemeris = {
  "date": "2026-03-23",
  "day_of_week": "Monday",
  "planets": {
    "Солнце": {"sign": "Овен", "degree": 2.86, "nakshatra": "Ашвини", "nakshatra_pada": 1},
    "Луна": {"sign": "Близнецы", "degree": 2.21, "nakshatra": "Мригашира", "nakshatra_pada": 3},
    "Меркурий": {"sign": "Рыбы", "degree": 8.83, "nakshatra": "Уттарабхадра", "nakshatra_pada": 2},
    "Венера": {"sign": "Овен", "degree": 21.15, "nakshatra": "Бхарани", "nakshatra_pada": 3},
    "Марс": {"sign": "Рыбы", "degree": 16.45, "nakshatra": "Уттарабхадра", "nakshatra_pada": 4},
    "Юпитер": {"sign": "Рак", "degree": 15.33, "nakshatra": "Пушья", "nakshatra_pada": 4},
    "Сатурн": {"sign": "Овен", "degree": 4.49, "nakshatra": "Ашвини", "nakshatra_pada": 2},
    "Уран": {"sign": "Телец", "degree": 28.41, "nakshatra": "Мригашира", "nakshatra_pada": 2},
    "Нептун": {"sign": "Овен", "degree": 1.88, "nakshatra": "Ашвини", "nakshatra_pada": 1},
    "Плутон": {"sign": "Водолей", "degree": 5.06, "nakshatra": "Дханишта", "nakshatra_pada": 4},
    "Хирон": {"sign": "Овен", "degree": 25.22, "nakshatra": "Бхарани", "nakshatra_pada": 4}
  },
  "aspects": [
    {"planet1": "Солнце", "planet2": "Сатурн", "angle": 1.6, "type": "соединение"},
    {"planet1": "Солнце", "planet2": "Нептун", "angle": 1.0, "type": "соединение"},
    {"planet1": "Луна", "planet2": "Уран", "angle": 3.8, "type": "соединение"},
    {"planet1": "Меркурий", "planet2": "Марс", "angle": 7.6, "type": "соединение"},
    {"planet1": "Венера", "planet2": "Хирон", "angle": 4.1, "type": "соединение"},
    {"planet1": "Сатурн", "planet2": "Нептун", "angle": 2.6, "type": "соединение"},
    {"planet1": "Марс", "planet2": "Юпитер", "angle": 118.9, "type": "трин"},
    {"planet1": "Луна", "planet2": "Плутон", "angle": 117.1, "type": "трин"}
  ]
}

MANKASI_FORGER_SYSTEM = {
    "Овен": {"ruler": "Марс", "element": "Fire", "quadrant": 1},
    "Телец": {"ruler": "Венера", "element": "Earth", "quadrant": 4},
    "Близнецы": {"ruler": "Меркурий", "element": "Air", "quadrant": 4},
    "Рак": {"ruler": "Луна", "element": "Water", "quadrant": 1},
    "Лев": {"ruler": "Солнце", "element": "Fire", "quadrant": 1},
    "Дева": {"ruler": "Меркурий", "element": "Earth", "quadrant": 2},
    "Весы": {"ruler": "Венера", "element": "Air", "quadrant": 2},
    "Скорпион": {"ruler": "Плутон", "element": "Water", "quadrant": 2},
    "Стрелец": {"ruler": "Юпитер", "element": "Fire", "quadrant": 3},
    "Козерог": {"ruler": "Сатурн", "element": "Earth", "quadrant": 3},
    "Водолей": {"ruler": "Уран", "element": "Air", "quadrant": 3},
    "Рыбы": {"ruler": "Нептун", "element": "Water", "quadrant": 3}
}

EXALTATION = {
    "Солнце": "Овен", "Луна": "Телец", "Меркурий": "Дева",
    "Венера": "Рыбы", "Марс": "Козерог", "Юпитер": "Рак", "Сатурн": "Весы"
}
FALL = {
    "Солнце": "Весы", "Луна": "Скорпион", "Меркурий": "Рыбы",
    "Венера": "Дева", "Марс": "Рак", "Юпитер": "Козерог", "Сатурн": "Овен"
}

NAKSHATRA_KEYS = {
    "Ашвини": {"element": "Fire", "nature": "Быстрое действие, исцеление", "deity": "Ашвини"},
    "Бхарани": {"element": "Earth", "nature": "Сила, плодовитость, творчество", "deity": "Яма"},
    "Мригашира": {"element": "Air", "nature": "Поиск, исследование", "deity": "Сома"},
    "Пушья": {"element": "Air", "nature": "Изобилие, защита", "deity": "Брихаспати"},
    "Уттарабхадра": {"element": "Water", "nature": "Благость, добродетель", "deity": "Ахи Буддхья"},
    "Дханишта": {"element": "Earth", "nature": "Богатство, скорость", "deity": "Васу"}
}

def calculate_planet_strength(planet, sign):
    score = 0
    if planet in EXALTATION and EXALTATION[planet] == sign:
        score += 5
    if planet in FALL and FALL[planet] == sign:
        score -= 4
    rulers = {"Овен": "Марс", "Телец": "Венера", "Близнецы": "Меркурий", "Рак": "Луна",
              "Лев": "Солнце", "Дева": "Меркурий", "Весы": "Венера", "Скорпион": "Плутон",
              "Стрелец": "Юпитер", "Козерог": "Сатурн", "Водолей": "Уран", "Рыбы": "Нептун"}
    if rulers.get(sign) == planet:
        score += 4
    return score

def analyze_mankasi_day():
    print("=" * 70)
    print("🔮 МАНКАСИ ПРОГНОЗ НА 23.03.2026")
    print("=" * 70)
    print(f"\n📅 Дата: {ephemeris['date']} ({ephemeris['day_of_week']})")
    
    print("\n" + "=" * 70)
    print("I. ПОЛОЖЕНИЯ ПЛАНЕТ (Транзиты)")
    print("=" * 70)
    
    strengths = {}
    for planet, data in ephemeris["planets"].items():
        sign = data["sign"]
        strength = calculate_planet_strength(planet, sign)
        strengths[planet] = strength
        status = "⚡"
        if strength >= 4:
            status = "✨ ЭКЗАЛЬТАЦИЯ"
        elif strength <= -3:
            status = "⚠️ ПАДЕНИЕ"
        print(f"  {planet:10} → {sign:12} {data['degree']:5.1f}°  [{data['nakshatra']}] {status}")
    
    sorted_planets = sorted(strengths.items(), key=lambda x: x[1], reverse=True)
    
    print("\n" + "=" * 70)
    print("II. ПЛАНЕТАРНЫЕ КУЗНЕЦЫ МАНКАСИ")
    print("=" * 70)
    print("\nКузнец — это планета, которая управляет управителем знака,")
    print("в котором находится анализируемая планета.\n")
    
    for planet, data in ephemeris["planets"].items():
        sign = data["sign"]
        ruler = MANKASI_FORGER_SYSTEM.get(sign, {}).get("ruler", "Неизвестно")
        element = MANKASI_FORGER_SYSTEM.get(sign, {}).get("element", "")
        print(f"  {planet} в {sign}:")
        print(f"    → Управитель знака: {ruler}")
        print(f"    → Элемент: {element}")
        print()
    
    print("=" * 70)
    print("III. НАКШАТРАЛЬНЫЙ АНАЛИЗ")
    print("=" * 70)
    
    moon = ephemeris["planets"]["Луна"]
    moon_nak = NAKSHATRA_KEYS.get(moon["nakshatra"], {})
    
    print(f"\n🌙 Луна: {moon['sign']} {moon['degree']:.1f}°")
    print(f"   Накшатра: {moon['nakshatra']} (пада {moon['nakshatra_pada']})")
    print(f"   Элемент: {moon_nak.get('element', 'Unknown')}")
    print(f"   Характер: {moon_nak.get('nature', 'Unknown')}")
    
    print("\n📍 Распределение по накшатрам:")
    nakshatra_count = {}
    for planet, data in ephemeris["planets"].items():
        nak = data["nakshatra"]
        if nak not in nakshatra_count:
            nakshatra_count[nak] = []
        nakshatra_count[nak].append(planet)
    
    for nak, planets in sorted(nakshatra_count.items()):
        nak_info = NAKSHATRA_KEYS.get(nak, {})
        print(f"  {nak}: {', '.join(planets)} ({nak_info.get('element', '')})")
    
    print("\n" + "=" * 70)
    print("IV. КЛЮЧЕВЫЕ АСПЕКТЫ")
    print("=" * 70)
    
    major_aspects = [a for a in ephemeris["aspects"] if a["type"] in ["соединение", "трин"]]
    for asp in major_aspects:
        print(f"  {asp['planet1']} {asp['type']} {asp['planet2']} ({asp['angle']:.1f}°)")
    
    print("\n" + "=" * 70)
    print("V. ПРОГНОЗ ПО ДОМАМ МАНКАСИ")
    print("=" * 70)
    
    houses = {
        1: "Личность — Солнце+Сатурн+Нептун в Овне (соединение). Кузнец — Марс.",
        2: "Ресурсы — Венера в Овне. Управитель — Марс в Рыбах (падение)."
           "Слабость II дома.",
        3: "Коммуникация — Луна+Уран в Близнецах/Тельце. Нестабильность."
           "Быстрые мысли, переменчивость.",
        4: "Дом/Семья — Хирон в Овне. Травматические паттерны дома."
           "Работа с корнями.",
        5: "Творчество/Дети — Трин Луна-Плутон. Глубокое творческое преобразование."
           "Интенсивные эмоции.",
        6: "Служение/Здоровье — Меркурий+Марс в Рыбах. Уязвимость к инфекциям."
           "Нужна осторожность с пищеварением.",
        7: "Партнёрство — Плутон в Водолее. Трансформация в отношениях."
           "Неожиданные встречи.",
        8: "Трансформация — Плутон в Водолее. Глубинная работа с реальностью."
           "Эзотерика, оккультизм.",
        9: "Философия — Юпитер в Раке (экзальтация!). Расширение духовности."
           "Сильная удача в делах веры.",
        10: "Карьера — Овен на куспиде. Солнце+Сатурн — амбиции."
            "Конфликт между эго и структурой.",
        11: "Надежды — Плутон в Водолее. Переосмысление социальных связей."
            "Нестандартные проекты.",
        12: "Ограничения — Нептун в Овне. Иллюзии, самообман."
            "Опасность дезориентации."
    }
    
    for house, desc in houses.items():
        print(f"\n  {house:2d} Дом: {desc}")
    
    print("\n" + "=" * 70)
    print("VI. ИТОГОВЫЙ ПРОГНОЗ")
    print("=" * 70)
    
    print("""
  📌 ОБЩАЯ ХАРАКТЕРИСТИКА ДНЯ:
  
  ★ СОЛНЕЧНОЕ СОЕДИНЕНИЕ (Сатурн + Нептун) — редкий паттерн.
    - Сатурн-Нептун: ограничения + иллюзии = разочарование или прозрение
    - Марс как кузнец — агрессивное проявление через ограничения
    - Овен — огненная энергия без фильтра
    
  ★ ЛУНА в БЛИЗНЕЦАХ + соединение с Ураном:
    - Быстрые эмоциональные переключения
    - Неожиданные новости
    - Интеллектуальная активность vs эмоциональная нестабильность
    
  ★ ЮПИТЕР в РАКЕ (экзальтация):
    - Лучший аспект дня!
    - Духовное расширение, обучение
    - Хорошее время для религиозных/философских дел
    
  ★ ТРИН МАРС-ЮПИТЕР:
    - Гармоничный аспект для роста
    - Удача через действия
    - Возможны путешествия
    
  ★ ТРИН ЛУНА-ПЛУТОН:
    - Глубокая эмоциональная трансформация
    - Интенсивные переживания
    - Работа с бессознательным

  ⚠️ ОПАСНОСТИ:
  - Сатурн+Нептун = мошенничество, обман
  - Меркурий+Марс в Рыбах = недопонимание, ложные слухи
  - Избегать: подписания контрактов, спекуляций

  ✨ БЛАГОПРИЯТНО:
  - Духовные практики
  - Философия, образование
  - Путешествия (особенно водные)
  - Творчество (5 дом через трин Луна-Плутон)
""")

if __name__ == "__main__":
    analyze_mankasi_day()
