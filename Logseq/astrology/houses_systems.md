---
title: House Systems — Системы астрологических домов
type:: concept
id:: houses_systems
tags:: [concept, astrology, houses, munkasey]
description: Обзор 8+ систем домов с формулами Munkasey
icon: 🏠
related::
  - "[[placidus]]"
  - "[[whole_sign_houses]]"
  - "[[munkasey_formulas]]"
  - "[[electoral_agent]]"
created: 2026-03-27
---

# House Systems — Системы домов

## Доступные системы (Munkasey)

| Код | Система | Тип | Описание |
|-----|---------|-----|---------|
| **P** | **Placidus** | Time | Самая популярная в мире, искажается >66° широты |
| K | Koch | Time | Американская традиция, основа на "месте рождения" |
| C | Campanus | Space | Равнораспределённая по вертикальной сфере |
| R | Regiomontanus | Space | Историческая система, похожа на Campanus |
| A | Alcabitius | Space | Для высоких широт, RA-based |
| O | Porphyry | Quadrant | Простое деление квадрантов на 3 |
| W | Whole Sign | Ecliptic | Дом 1 = знак ASC, древняя система |
| E | Equal (от ASC) | Ecliptic | 30° от ASC, без учёта квадрантов |

---

## Munkasey House Formulas

**Источник:** Michael P. Munkasey — "An Astrological House Formulary"

### Формулы включены в `core/houses.py`:

```
houses.py
├── julian_day()                          # JD для любой даты
├── julian_day_to_local_sidereal_time()    # JD → LST
├── calculate_ascendant()                  # ASC
├── calculate_midheaven()                  # MC
├── calculate_placidus_cusps()            # Placidus ✅
├── calculate_porphyry_cusps()            # Porphyry
├── calculate_equal_houses()              # Equal
├── calculate_whole_sign_houses()          # Whole Sign
├── calculate_alcabitius_cusps()          # Alcabitius
└── HouseCalculator                        # Главный класс
```

---

## Быстрый старт

```python
from core.houses import HouseCalculator
from datetime import datetime

calc = HouseCalculator('P')  # Placidus
result = calc.calculate(
    jd=2459847.5,
    latitude=55.75,
    longitude=37.62
)
print(result['cusps'])  # 12 cusps
```

---

## Whole Sign Houses (Авестийская система)

| Дом | Знак | Управитель |
|-----|------|-----------|
| 1 | ASC sign | Управитель знака |
| 2 | Следующий | Управитель |
| ... | ... | ... |

---

## Geo-agnostic: Whole Sign vs Placidus

| Критерий | Whole Sign | Placidus |
|----------|-----------|----------|
| География | Не зависит | Зависит от широты |
| Искажения | Нет | Есть >66° |
| Традиция | Ведическая | Западная |
| Популярность | Растёт | #1 в мире |

> **Выбор:** Для натальной астрологии — Placidus. Для Muhurta/Electoral — Whole Sign (без искажений).
