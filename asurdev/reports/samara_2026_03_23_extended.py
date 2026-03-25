#!/usr/bin/env python3
"""
Ведический анализ для Самары — 23 марта 2026
Расширенный анализ с чогадией по времени
"""

from datetime import datetime, timezone
import math

# === КОНСТАНТЫ ===
LAT = 53.183  # Самара
LON = 50.117
TZ_OFFSET = 4  # MSK+1 (март 2026 — без перехода на летнее?)

# Дата
Y = 2026
M = 3
D = 23

# ============================================================
# РАСЧЁТ ВОСХОДА/ЗАКАТА СОЛНЦА (упрощённый алгоритм)
# ============================================================
def day_of_year(y, m, d):
    n1 = math.floor(275 * m / 9)
    n2 = math.floor((m + 9) / 12)
    n3 = (1 + math.floor((y - 4 * math.floor(y / 4) + 2) / 3))
    n = n1 - (n2 * n3) + d - 30
    return n

def sunrise_sunset(y, m, d, lat, lon, is_sunrise=True):
    """Упрощённый расчёт восхода/заката"""
    n = day_of_year(y, m, d)
    
    # Среднее солнечное полуденное время
    Jp = n + (12 - lon) / 24
    
    # Среднее время солнечных суток
    M = (0.9856 * Jp) - 3.289
    
    # Уравнение времени (приближение)
    L = M + (1.916 * math.sin(math.radians(M))) + (0.020 * math.sin(math.radians(2*M))) + 282.634
    L = L % 360
    
    # Склонение Солнца
    decl = math.degrees(math.asin(math.sin(math.radians(L)) * math.sin(math.radians(23.439))))
    
    # Часовой угол
    lat_rad = math.radians(lat)
    decl_rad = math.radians(decl)
    
    cos_ha = (math.sin(math.radians(-0.833)) - math.sin(lat_rad) * math.sin(decl_rad)) / \
             (math.cos(lat_rad) * math.cos(decl_rad))
    
    # Границы
    if cos_ha > 1:
        return None  # Полярная ночь
    if cos_ha < -1:
        return None  # Полярный день
    
    ha = math.degrees(math.acos(cos_ha))
    
    # Время
    if is_sunrise:
        UT = 12 - (ha / 15) - (lon / 15)
    else:
        UT = 12 + (ha / 15) - (lon / 15)
    
    # Коррекция уравнения времени
    UT = UT + 0.005  # ~18 секунд
    
    # Конвертация в MSK
    hours = int(UT + TZ_OFFSET)
    mins = int((UT + TZ_OFFSET - hours) * 60)
    secs = int(((UT + TZ_OFFSET - hours) * 60 - mins) * 60)
    
    return f"{hours:02d}:{mins:02d}:{secs:02d}"

# ============================================================
# РАСЧЁТ ЧОГАДИИ (8 частей дня)
# ============================================================
CHOGADIYA_NAMES = [
    "Амрит",     # 0 — Лучшее время для всего
    "Колва",     # 1 — Опасное время
    "Наимитт",   # 2 — Нейтральное
    "Мрит",      # 3 — Похоронное (не использовать)
    "Лабх",      # 4 — Прибыль
    "Амрит",     # 5 — Повтор Амрита
    "Каол",      # 6 — Ссора, воровство
    "Амрит",     # 7 — Третий Амрит
]

CHOGADIYA_MEANINGS = {
    "Амрит": "🟢 АМРИТ — Лучшее время! Благоприятно для любых дел, новых начинаний, торговли, свадьбы",
    "Колва": "🔴 КОЛВА — Опасное время. Избегать важных дел, путешествий",
    "Наимитт": "🟡 НАИМИТТ — Нейтральное. Для обычных дел",
    "Мрит": "⚫ МРИТ — Похоронное. Категорически не благоприятно для важных дел",
    "Лабх": "🟢 ЛАБХА — Прибыль, выгода. Хорошо для финансовых операций",
    "Каол": "🔴 КАОЛ — Ссора, воровство. Не благоприятно",
}

def calculate_chogadiya_times(sunrise_str):
    """Рассчитать времена чогадий"""
    parts = sunrise_str.split(':')
    h = int(parts[0])
    m = int(parts[1])
    sunrise_minutes = h * 60 + m
    
    # Длина дня (предполагаем 12 часов 10 минут для марта)
    day_length_minutes = 12 * 60 + 10
    
    # Каждая чогадия = 1/8 дня
    chogadiya_duration = day_length_minutes / 8
    
    times = []
    for i, name in enumerate(CHOGADIYA_NAMES):
        start_min = sunrise_minutes + i * chogadiya_duration
        end_min = start_min + chogadiya_duration
        
        start_h = int(start_min // 60)
        start_m = int(start_min % 60)
        end_h = int(end_min // 60)
        end_m = int(end_min % 60)
        
        times.append({
            'index': i,
            'name': name,
            'start': f"{start_h:02d}:{start_m:02d}",
            'end': f"{end_h:02d}:{end_m:02d}",
            'duration_minutes': int(chogadiya_duration)
        })
    
    return times

# ============================================================
# РАСЧЁТ ВАРЛАБХА / ВАРПРАВРИТИ
# ============================================================
# Варлабха = Час планеты (время от восхода до заката делится на 12)
# Вара = день недели
# Праврити = убывающая или растущая Луна

PLANET_HOURS = {
    0: "Солнце",   # Воскресенье
    1: "Луна",     # Понедельник
    2: "Марс",     # Вторник
    3: "Меркурий", # Среда
    4: "Юпитер",   # Четверг
    5: "Венера",   # Пятница
    6: "Сатурн",   # Суббота
}

def calculate_planet_hour(sunrise_str, target_time_str):
    """Какой планетарный час идёт в данное время"""
    parts = sunrise_str.split(':')
    h = int(parts[0])
    m = int(parts[1])
    sunrise_minutes = h * 60 + m
    
    h2, m2 = map(int, target_time_str.split(':'))
    target_minutes = h2 * 60 + m2
    
    day_minutes = 12 * 60 + 10  # Примерная длина дня
    hour_duration = day_minutes / 12
    
    elapsed = target_minutes - sunrise_minutes
    if elapsed < 0:
        elapsed += 24 * 60
    
    hour_index = int(elapsed / hour_duration) % 12
    day_of_week = datetime(Y, M, D).weekday()  # 0=Пн
    
    planet = PLANET_HOURS[day_of_week]
    
    # Чередование: день/ночь
    is_day = elapsed < day_minutes
    if is_day:
        planet_index = day_of_week
    else:
        planet_index = (day_of_week + 6) % 7  # Ночью наоборот
    
    current_planet = PLANET_HOURS[planet_index]
    
    return current_planet, hour_index

# ============================================================
# ОСНОВНОЙ РАСЧЁТ
# ============================================================
print("=" * 70)
print("🔮 РАСШИРЕННЫЙ ВЕДИЧЕСКИЙ АНАЛИЗ — САМАРА 🔮")
print("=" * 70)
print(f"\n📍 Локация: Самара ({LAT}°N, {LON}°E)")
print(f"📅 Дата: {D}.{M:02d}.{Y}")
print(f"☀️ День недели: Воскресенье (Равивара)")

sunrise = sunrise_sunset(Y, M, D, LAT, LON, is_sunrise=True)
sunset = sunrise_sunset(Y, M, D, LAT, LON, is_sunrise=False)

print(f"\n🌅 ВОСХОД СОЛНЦА: {sunrise}")
print(f"🌇 ЗАКАТ СОЛНЦА: {sunset}")

# Чогадия
print("\n" + "=" * 70)
print("⏰ РАСЧЁТ ЧОГАДИИ (ВРЕМЕНА СУТОК)")
print("=" * 70)

chogadiyas = calculate_chogadiya_times(sunrise)

for ch in chogadiyas:
    emoji = "🟢" if ch['name'] == "Амрит" else ("🔴" if ch['name'] in ["Колва", "Каол", "Мрит"] else "🟡")
    print(f"\n{emoji} ЧОГАДИЯ {ch['index'] + 1}/8: {ch['name']}")
    print(f"   Время: {ch['start']} — {ch['end']} ({ch['duration_minutes']} минут)")
    print(f"   Значение: {CHOGADIYA_MEANINGS.get(ch['name'], '')}")

# Текущая чогадия (для 18:20)
current_time = "18:20"
print("\n" + "-" * 70)
print(f"📍 Текущее время ({current_time}):")

for i, ch in enumerate(chogadiyas):
    start_h, start_m = map(int, ch['start'].split(':'))
    end_h, end_m = map(int, ch['end'].split(':'))
    
    cur_h, cur_m = map(int, current_time.split(':'))
    
    start_total = start_h * 60 + start_m
    end_total = end_h * 60 + end_m
    cur_total = cur_h * 60 + cur_m
    
    # Учитываем, что день может перевалить за полночь
    if end_total < start_total:  # Переход через полночь
        if cur_total >= start_total or cur_total < end_total:
            print(f"\n   ▶️ АКТИВНАЯ ЧОГАДИЯ: {ch['name']}")
            print(f"   Осталось: {end_total - cur_total if cur_total >= start_total else end_total - cur_total + 24*60} минут")
            break
    elif start_total <= cur_total < end_total:
        print(f"\n   ▶️ АКТИВНАЯ ЧОГАДИЯ: {ch['name']}")
        remaining = end_total - cur_total
        print(f"   Осталось: {remaining} минут")
        break

# Варлабха
print("\n" + "=" * 70)
print("🌐 ВАРЛАБХА (ПЛАНЕТАРНЫЕ ЧАСЫ)")
print("=" * 70)

sample_times = ["07:00", "09:00", "12:00", "15:00", "18:00", "21:00"]
print("\nПланетарные часы на день:")
for t in sample_times:
    planet, hour_idx = calculate_planet_hour(sunrise, t)
    print(f"   {t} — Час {hour_idx + 1}: {planet}")

# Мухурта (45 минут = 1/2 планетарного часа)
print("\n" + "=" * 70)
print("🪔 МУХУРТА (45-минутные периоды)")
print("=" * 70)
print("\nДля точного мухурты нужно указать цель activity:")
print("   • Мухурта для торговли")
print("   • Мухурта для свадьбы")
print("   • Мухурта для путешествия")
print("   • Мухурта для начала бизнеса")
print("\n⚠️ Для детального расчёта мухурты обратитесь к ведическому пандиту")
