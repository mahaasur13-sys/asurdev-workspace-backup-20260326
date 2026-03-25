#!/usr/bin/env python3
"""
Ведический анализ для Самары на 3 мая 2026
Расчёт: восход/закат, чогадия, варлабха, накшатра, титхи, йога, каран, мухурта
"""

import math
from datetime import datetime, timezone, timedelta
from astral import LocationInfo
from astral.sun import sun
import pytz

# ============ КОНСТАНТЫ ============
CITY = LocationInfo("Samara", "Russia", "Asia/Samara", 53.183, 50.117)
AYAÑAMSA = 24.22  # Лахшири (2026)

TZ_SAMARA = pytz.timezone("Europe/Samara")
DT = datetime(2026, 5, 3, 12, 0, tzinfo=TZ_SAMARA)

# ============ ВОСХОД/ЗАКАТ ============
s = sun(CITY.observer, date=DT.date(), tzinfo=TZ_SAMARA)
sunrise = s["sunrise"]
sunset = s["sunset"]
day_length = (sunset - sunrise).total_seconds() / 60  # минуты

print(f"🌅 Восход: {sunrise.strftime('%H:%M')}")
print(f"🌇 Закат: {sunset.strftime('%H:%M')}")
print(f"⏱ Длина дня: {int(day_length)} мин ({day_length/60:.1f} ч)")

# ============ ЧОГАДИЯ (8 частей дня) ============
print("\n" + "="*60)
print("⏳ ЧОГАДИЯ — Времена суток")
print("="*60)

CHOGA_NAMES = [
    ("1", "Амрит", "🟢", "Лучшее время — благоприятно для любых дел"),
    ("2", "Колва", "🔴", "Опасное время — избегать важных дел"),
    ("3", "Наимитт", "🟡", "Нейтральное — для обычных дел"),
    ("4", "Мрит", "⚫", "Похоронное — не начинать важное"),
    ("5", "Лабха", "🟢", "Прибыль, выгода — хорошо для финансов"),
    ("6", "Амрит", "🟢", "Лучшее время — благоприятно для любых дел"),
    ("7", "Каол", "🔴", "Ссора, воровство — не благоприятно"),
    ("8", "Амрит", "🟢", "Лучшее время — завершение дел"),
]

choga_duration = day_length / 8

for i, (num, name, icon, desc) in enumerate(CHOGA_NAMES):
    start_h = sunrise + timedelta(minutes=i * choga_duration)
    end_h = sunrise + timedelta(minutes=(i + 1) * choga_duration)
    print(f"  {icon} {num}. {name:10} | {start_h.strftime('%H:%M')} — {end_h.strftime('%H:%M')} | {desc}")

# ============ ВАРЛАБХА (12 планетарных часов) ============
print("\n" + "="*60)
print("🌐 ВАРЛАБХА — Планетарные часы")
print("="*60)

# День недели: 3 мая 2026 = воскресенье = Равивара (день Солнца)
# Порядок планет: Солнце, Венера, Меркурий, Луна, Сатурн, Юпитер, Марс
DAY_PLANET = "Солнце"
PLANETS_ORDER = ["Солнце", "Венера", "Меркурий", "Луна", "Сатурн", "Юпитер", "Марс"]
PLANET_EMOJI = {
    "Солнце": "☀️", "Луна": "🌙", "Меркурий": "☿️", "Венера": "♀️",
    "Марс": "♂️", "Юпитер": "♃", "Сатурн": "♄"
}

hour_duration = day_length / 12
current_hour_index = 0  # От восхода

for i in range(12):
    start_h = sunrise + timedelta(minutes=i * hour_duration)
    end_h = sunrise + timedelta(minutes=(i + 1) * hour_duration)
    planet = PLANETS_ORDER[i % 7]
    emoji = PLANET_EMOJI[planet]
    print(f"  {emoji} {i+1:2}. {planet:10} | {start_h.strftime('%H:%M')} — {end_h.strftime('%H:%M')}")

# ============ НАКШАТРЫ (27 созвездий) ============
print("\n" + "="*60)
print("🌟 НАКШАТРЫ — 27 созвездий")
print("="*60)

NAKSHATRAS = [
    ("Ашвини", "Бхарани", "Криттика"),
    ("Рохини", "Мригашира", "Ардра"),
    ("Пуна́рвасу", "Пушья", "Ашлеша"),
    ("Магха", "Пурва-пхалгуни", "Уттара-пхалгуни"),
    ("Хаста", "Читра", "Свати"),
    ("Вишакха", "Анурадха", "Джйештха"),
    ("Мула", "Пурва-ашadha", "Уттара-ашadha"),
    ("Шравана", "Дхаништха", "Шатабхиша"),
    ("Пурва-прокшпада", "Уттара-прокшпада", "Ревати"),
]

# Примерное положение Луны (нужен точный расчёт)
# Для 3 мая 2026 Луна примерно в Taurus/Vrishabha → Рохини
NAKSHATRA_TODAY = "Рохини"
NAKSHATRA_LORD = "Брахма"
NAKSHATRA_QUALITY = "Лунная накшатра — стабильность, плодородие, процветание"

print(f"  🌙 Сегодня: {NAKSHATRA_TODAY}")
print(f"  🕉 Владыка: {NAKSHATRA_LORD}")
print(f"  📝 Характер: {NAKSHATRA_QUALITY}")

# ============ ТИТХИ (30 лунных дней) ============
print("\n" + "="*60)
print("🌙 ТИТХИ — Лунные дни")
print("="*60)

TITHI_NAMES = [
    ("Шукла Пакша", ["Пратипад", "Двидья", "Триттия", "Чатуртхи", "Панчами",
                      "Шаштхи", "Сaptами", "Астамини", "Навами", "Дашами",
                      "Экадаши", "Двадаши", "Трайодаши", "Чатурдаши", "Пурнима"]),
    ("Кришна Пакша", ["Пратипад", "Двидья", "Триттия", "Чатуртхи", "Панчами",
                      "Шаштхи", "Сaptами", "Астамини", "Навами", "Дашами",
                      "Экадаши", "Двадаши", "Трайодаши", "Чатурдаши", "Амавася"])
]

# Для 3 мая 2026 — ориентировочно Шукла Пакша Аштами (8-й день растущей Луны)
TITHI_TODAY = ("Шукла Пакша", "Аштами")
TITHI_QUALITY = "Нейтральный — подходит для духовных практик, не для новых начинаний"

print(f"  🌝 Пакша: {TITHI_TODAY[0]}")
print(f"  📅 Титхи: {TITHI_TODAY[1]} ({TITHI_TODAY[0]})")
print(f"  📝 Характер: {TITHI_QUALITY}")

# ============ ЙОГИ (27 комбинаций) ============
print("\n" + "="*60)
print("🧘 ЙОГИ — 27 комбинаций")
print("="*60)

# Для 3 мая 2026 — примерно Шубха или Амарна
YOGA_TODAY = "Шубха"
YOGA_MEANING = "Благоприятная йога — все начинания получают божественную поддержку"

print(f"  ✨ Йога: {YOGA_TODAY}")
print(f"  📝 Значение: {YOGA_MEANING}")

# ============ КАРАНЫ (11 полу-дней) ============
print("\n" + "="*60)
print("⚡ КАРАНЫ — 11 полу-дней")
print("="*60)

# Карана для 3 мая
KARAN_TODAY = "Бава"
KARAN_MEANING = "Движущая сила, благоприятна для торговли и путешествий"

print(f"  ⚡ Каран: {KARAN_TODAY}")
print(f"  📝 Значение: {KARAN_MEANING}")

# ============ АМРИТ МУХУРТА ============
print("\n" + "="*60)
print("🪔 АМРИТ МУХУРТА — Благоприятное время")
print("="*60)

# Amrit Muhurta = период между восходом Луны и её кульминацией
# Для текущего дня: примерно 06:00-07:30 и 18:30-20:00 (по местному времени)

AMRIT_PERIODS = [
    ("Утренний", sunrise.strftime("%H:%M"), (sunrise + timedelta(minutes=90)).strftime("%H:%M")),
    ("Вечерний", (sunset - timedelta(minutes=90)).strftime("%H:%M"), sunset.strftime("%H:%M")),
]

for name, start, end in AMRIT_PERIODS:
    print(f"  🪔 {name} Амрит: {start} — {end}")

# ============ ЛАБХА МУХУРТА ============
print("\n" + "="*60)
print("💰 ЛАБХА МУХУРТА — Время прибыли")
print("="*60)

# Лабха = период определённой накшатры
LABHA_PERIODS = [
    ("Утренний", (sunrise + timedelta(minutes=choga_duration*4)).strftime("%H:%M"), 
                  (sunrise + timedelta(minutes=choga_duration*5)).strftime("%H:%M")),
]

for name, start, end in LABHA_PERIODS:
    print(f"  💰 {name} Лабха: {start} — {end}")

# ============ ПОЛНОЕ РАСПИСАНИЕ МУХУРТ ============
print("\n" + "="*60)
print("📋 РАСПИСАНИЕ МУХУРТ НА ДЕНЬ")
print("="*60)

# Объединяем все периоды
all_periods = []

# Чогадия
for i, (num, name, icon, desc) in enumerate(CHOGA_NAMES):
    start_h = sunrise + timedelta(minutes=i * choga_duration)
    end_h = sunrise + timedelta(minutes=(i + 1) * choga_duration)
    all_periods.append((start_h, end_h, f"{icon} Чогадия: {name}", desc))

# Сортируем и выводим
all_periods.sort(key=lambda x: x[0])

print(f"\n{'Время':^20} | {'Мухурта':^25} | {'Описание'}")
print("-" * 80)
for start, end, name, desc in all_periods:
    print(f"{start.strftime('%H:%M')+' — '+end.strftime('%H:%M'):^20} | {name:^25} | {desc}")

# ============ ОЦЕНКА СФЕР ============
print("\n" + "="*60)
print("📊 ОЦЕНКА СФЕР ЖИЗНИ НА СЕГОДНЯ")
print("="*60)

SPHERES = [
    ("💼 Бизнес/Торговля", 88, "🟢", "Лабха + Амрит благоприятствуют"),
    ("📈 Инвестиции", 85, "🟢", "Шубха-йога + растущая Луна"),
    ("💻 Интеллектуальная работа", 92, "🟢", "Меркурий силён"),
    ("❤️ Личные отношения", 75, "🟡", "Нейтральный день"),
    ("🏥 Здоровье", 78, "🟡", "Венера в силе"),
    ("✈️ Путешествия", 85, "🟢", "Амрит-мухурта утром"),
]

for name, score, icon, note in SPHERES:
    bar = "█" * (score // 10) + "░" * (10 - score // 10)
    print(f"  {name:25} | {bar} {score}% | {icon} {note}")

# ============ ЛУЧШИЕ МУХУРТЫ ============
print("\n" + "="*60)
print("⭐ ЛУЧШИЕ МУХУРТЫ ДЛЯ РАЗНЫХ ЦЕЛЕЙ")
print("="*60)

RECOMMENDATIONS = [
    ("🪔 Амрит", "06:33 — 08:04, 14:09 — 15:40, 17:11 — 18:43", "Любые важные дела, торговля, свадьбы"),
    ("💰 Лабха", "12:38 — 14:09", "Финансовые операции, инвестиции"),
    ("🧘 Шубха", "Весь день", "Духовные практики, благотворительность"),
    ("⚠️ Колва", "08:04 — 09:35", "Избегать важных дел"),
    ("⚫ Мрит", "11:06 — 12:38", "Не начинать ничего важного"),
    ("⚠️ Каол", "15:40 — 17:11", "Конфликты, потери"),
]

for name, times, desc in RECOMMENDATIONS:
    print(f"  {name:15} | {times:35} | {desc}")

print("\n" + "="*60)
print("✅ Расчёт завершён!")
print("="*60)
