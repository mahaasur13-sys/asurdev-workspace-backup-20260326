---
type:: method
id:: ephemeris_calculations
tags:: [method, astrology, swiss-ephemeris, planetary-positions, houses, _impl]
aliases:: [Ephemeris, Planetary Calculations, Swiss Ephemeris Wrapper, Natal Chart]
related:: [aspects_calculations, electoral_agent, bradley_agent, gann_agent, cycle_agent]
created:: 2026-03-27
updated:: 2026-03-27
---

# Ephemeris Calculations

> Расчёт планетарных позиций, домов и натальных карт.
> Файл: `core/ephemeris.py`

## Концепция

Обертка над **Swiss Ephemeris** (pyswisseph) для точного расчёта положений планет в эклиптических координатах. Используется всеми астро-агентами.

```
Дата + Время + Координаты → NatalChart (позиции + дома)
```

**Fallback:** если Swiss Ephemeris не установлен — используется упрощённый расчёт (для тестирования).

---

## Зависимости

```python
try:
    import swisseph as swe
    HAS_SWISS_EPHEMERIS = True
except ImportError:
    HAS_SWISS_EPHEMERIS = False
    # fallback: _simple_position()
```

---

## Planet Constants (Swiss Ephemeris IDs)

| ID | Planet | Sanskrit |
|----|--------|---------|
| 0 | Sun | Surya |
| 1 | Moon | Chandra |
| 2 | Mercury | Budha |
| 3 | Venus | Shukra |
| 4 | Mars | Mangala |
| 5 | Jupiter | Brihaspati |
| 6 | Saturn | Shani |
| 7 | Uranus | — |
| 8 | Neptune | — |
| 9 | Pluto | — |
| 10 | North Node | Rahu |
| 15 | Chiron | — |

---

## Dataclasses

### PlanetPosition

```python
@dataclass
class PlanetPosition:
    planet: str          # "sun", "moon", "mars", ...
    longitude: float     # degrees 0-360 (ecliptic)
    speed: float          # daily motion in degrees
    retrograde: bool     # True if speed < 0
```

### HouseCusps

```python
@dataclass
class HouseCusps:
    houses: list[float]   # 12 houses, 0-indexed
    ascendant: float     # ASC (house 1 cusp)
    mc: float            # Medium Coeli / Midheaven
    vertex: float        # Vertex
```

### NatalChart

```python
@dataclass
class NatalChart:
    planets: dict[str, PlanetPosition]
    houses: HouseCusps
    timestamp: datetime
    latitude: float
    longitude: float
```

---

## House Systems

| System | Code | Описание |
|--------|------|---------|
| Placidus | `P` | Most common — разделение по времени |
| Whole Sign | — | Все дома = 30°each sign |
| Equal | `E` | Equal 30° houses from ASC |

---

## Coordinate Systems

### Tropical (default)

```
longitude в градусах от 0° Aries (весеннего равноденствия)
```

### Sidereal (для Vedic)

```python
calculate_natal_chart(
    birth_time,
    latitude,
    longitude,
    use_sidereal=True,
    ayanamsha=1  # Raseshwara
)
```

---

## Usage

```python
from core.ephemeris import (
    PlanetPosition,
    NatalChart,
    calculate_natal_chart,
    get_current_positions,
    get_planetary_positions,
    HAS_SWISS_EPHEMERIS,
)

# Натальная карта
chart = calculate_natal_chart(
    birth_time=datetime(1990, 5, 15, 12, 0),
    latitude=55.7558,   # Москва
    longitude=37.6173,
)
print(chart.planets["sun"].longitude)    # 24.5°
print(chart.planets["moon"].longitude)   # 180.3°
print(chart.houses.ascendant)            # 67.2°
print(chart.houses.mc)                   # 220.1°

# Текущие позиции
positions = get_current_positions(
    latitude=55.7558,
    longitude=37.6173,
)
print(positions.planets["jupiter"].retrograde)  # True/False

# Только планеты (dict)
pos_dict = get_planetary_positions(
    dt=datetime(2026, 3, 27),
    latitude=53.2,
    longitude=50.1,
)
```

---

## Julian Day

Внутренняя функция для конвертации datetime → Julian Day:

```python
def _julian_day(dt: datetime) -> float:
    year = dt.year
    month = dt.month
    day = dt.day + dt.hour/24 + dt.minute/1440 + dt.second/86400

    if month <= 2:
        year -= 1
        month += 12

    A = int(year / 100)
    B = 2 - A + int(A / 4)

    return int(365.25*(year+4716)) + int(30.6001*(month+1)) + day + B - 1524.5
```

---

## Формулы планет (fallback, без Swiss Ephemeris)

```python
def _simple_position(planet: str, jd: float) -> tuple:
    base = {
        "sun": 0, "moon": 100, "mercury": 180,
        "venus": 220, "mars": 50, "jupiter": 290, "saturn": 320,
    }
    period = {
        "sun": 365.25, "moon": 27.32, "mercury": 87.97,
        "venus": 224.7, "mars": 686.98, "jupiter": 4332.59, "saturn": 10759.22,
    }
    p = base.get(planet, 0)
    t = period.get(planet, 365.25)
    longitude = (p + 360 * (jd - 2451545) / t) % 360
    speed = 360 / t
    return longitude, speed
```

⚠️ **Точность: НЕ HIGH. Только для тестирования без Swiss Ephemeris.**

---

## Как используется астро-агентами

```
core/ephemeris.py
       │
       ├── get_current_positions() → текущий момент
       │           │
       │           └── @require_ephemeris decorator
       │                     │
       │                     └── Все агенты астро-пула
       │
       ├── calculate_natal_chart() → натальная карта
       │           │
       │           ├── BradleyAgent (S&P паттерны)
       │           ├── GannAgent (углы + даты)
       │           └── CycleAgent (циклы планет)
       │
       └── get_planetary_positions() → только планеты
                    │
                    └── aspects.py (углы между планетами)
```

---

## Ректификация (TODO)

| Функция | Статус | Описание |
|---------|--------|---------|
| `calculate_planet()` | ✅ Готово | Одинокая планета |
| `calculate_houses()` | ✅ Готово | Дома (Placidus) |
| `calculate_natal_chart()` | ✅ Готово | Полная карта |
| `get_current_positions()` | ✅ Готово | Текущие позиции |
| Sidereal mode | ✅ Готово | Ведический расчёт |
| Ayanamsha | ✅ Готово | Raseshwara (1) |
| Дробные дома (Vargas) | ❌ TODO | Divisional charts |
| Planetary wars (Graha yuddha) | ❌ TODO | Войны планет |
| Yoga combinations | ❌ TODO | Йога-комбинации |

---

## Known Issues

| # | Описание | Статус |
|---|---------|--------|
| 1 | Swiss Ephemeris требует лицензию sweph | ⚠️ Лицензия |
| 2 | `_simple_position()` не точна — только для fallback | ⚠️ Тестирование |
| 3 | House calculation — только Placidus | 📋 TODO: Equal, Whole Sign |
| 4 | No Nakshatra calculations | 📋 TODO |

---

## TODO

- [ ] Добавить Whole Sign house system
- [ ] Добавить Nakshatra (лунные станции, 27 порций)
- [ ] Добавить Dasa system (Vimsottari Dasa)
- [ ] Интегрировать Graha yuddha (planetary wars)

---

## См. также

- [[aspects_calculations]] — аспекты между планетами
- [[electoral_agent]] — Muhurta timing
- [[bradley_agent]] — Bradley model
- [[gann_agent]] — Gann angles
- [[cycle_agent]] — Market cycles
- [[agents_index]] — все агенты
