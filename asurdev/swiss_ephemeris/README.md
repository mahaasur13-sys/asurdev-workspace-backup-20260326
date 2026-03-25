# Swiss Ephemeris Module — asurdev Sentinel v3.2

## Структура модуля

```
swiss_ephemeris/
├── __init__.py                    # Публичный API
├── AGENT_PROMPT.md                # Enforcement правила для агентов
├── swiss_ephemeris_tool.py        # Главный инструмент (LangGraph tool)
├── panchanga_calculator.py        # Panchanga (Tithi, Nakshatra, Yoga, Karana, Vara)
├── choghadiya_calculator.py       # Choghadiya (day + night periods)
├── ashtakavarga_calculator.py     # Bhinnashtakavarga + Sarvashtakavarga
└── ephe/                          # Ephemeris files
    ├── de421.bsp → symlink
    └── seas_18.dat → symlink
```

## Быстрый старт

```python
from swiss_ephemeris import swiss_ephemeris

# Вызов Swiss Ephemeris
result = swiss_ephemeris(
    date="2026-03-22",
    time="10:00:00",
    lat=55.7558,
    lon=37.6173,
    ayanamsa="lahiri",
    zodiac="sidereal",
    house_system="W",
    compute_houses=True,
    compute_panchanga=True,
    compute_choghadiya=True,
    compute_ashtakavarga=True,
)

# Данные из result
positions = result["positions"]        # Позиции планет
houses = result["houses"]              # Дома
panchanga = result["panchanga"]        # Panchanga
choghadiya = result["choghadiya"]     # Все периоды Choghadiya
current_ch = result["current_choghadiya"]  # Текущий период
ashtak = result["ashtakavarga_trading"]   # Ashtakavarga для торговли
```

## Panchanga данные

```python
{
    "vara": "Sunday",              # День недели
    "tithi": "Shukla Chaturthi",  # Тидхи (лунный день)
    "nakshatra": "Revati",         # Накшатра (27 лунных стоянок)
    "nakshatra_pada": 2,           # Пада (четверть накшатры)
    "yoga": "Shukla",              # Йога (27 комбинаций)
    "yoga_category": "Auspicious", # Категория йоги
    "karana": "Shakuni",           # Карана (60 вариантов)
    "karana_number_60": 7,         # Точный номер 0-59
    "sunrise": "07:15:30",
    "sunset": "19:42:15"
}
```

## Choghadiya

```python
{
    "day_parts": [
        {"period": 1, "type": "Udveg", "start": "07:15:30", "end": "08:46:52", "auspicious": False},
        {"period": 2, "type": "Char", "start": "08:46:52", "end": "10:18:15", "auspicious": True},
        ...
    ],
    "night_parts": [...],
    "current_choghadiya": {"type": "Rog", "auspicious": False, "quality": "..."}
}
```

## Ashtakavarga

```python
{
    "signal": "BEARISH",
    "confidence": 72.5,
    "overall_score": 26.0,
    "total_bindus": 31,
    "best_houses": [7, 6, 8],
    "benefic_receptors": [6, 7, 8],
    "malefic_receptors": [1, 2, 3],
    "house_analysis": {
        "House_1": {"bindus": 2, "quality": "Weak"},
        "House_7": {"bindus": 5, "quality": "Excellent"},
        ...
    }
}
```

## Enforcement правила

Все агенты **ОБЯЗАНЫ** вызывать `swiss_ephemeris` **ПЕРВЫМ** перед любой астрологической работой:

```python
# ❌ ЗАПРЕЩЕНО
nakshatra = calculate_nakshatra(moon_lon)

# ✅ ОБЯЗАТЕЛЬНО
eph = swiss_ephemeris(date=..., time=..., lat=..., lon=..., compute_panchanga=True)
nakshatra = eph["panchanga"]["nakshatra"]
```

## Кэширование

Все функции кэшируются через `@lru_cache`:

- `_jd_to_hms()` — 2048 entries
- `calculate_panchanga()` — 512 entries  
- `calculate_choghadiya()` — 512 entries
- `calculate_ashtakavarga()` — 1024 entries
- `_cached_compute()` — 1024 entries

Полный расчёт с кэшированием: **< 1ms** для повторных вызовов.

## Оптимизация Ashtakavarga

Ashtakavarga теперь использует:
- Tuple-based cache keys (house numbers as tuple)
- Pre-computed BAV tables from Parashara
- Minimal operations per calculation

10,000+ вызовов/сек на RTX 3060.
