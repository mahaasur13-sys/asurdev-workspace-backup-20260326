---
title: Placidus Houses — Placidus House System
type:: concept
id:: placidus
tags:: [concept, astrology, houses, placidus, munkasey, formulas]
description: Палацианская система домов — формулы расчёта куспидов по Munkasey + Swiss Ephemeris
icon: 🏠
related::
  - "[[houses_systems]]"
  - "[[whole_sign_houses]]"
  - "[[munkasey_formulas]]"
  - "[[ephemeris_calculations]]"
created: 2026-03-27
---

# Placidus House System

## Overview

| Параметр | Значение |
|----------|---------|
| **Код** | `P` |
| **Полное имя** | Placidus Houses (Палацидус) |
| **Автор** | Плацид (Placidus), ~17 век |
| **Тип** | Time-based (временная система) |
| **Формулы** | Munkasey "An Astrological House Formulary" |

> **Почему Placidus?** Placidus — наиболее распространённая система домов в современной астрологии. Времяподённый метод: границы домов определяются по времени прохождения меридиана через градусы эклиптики.

---

## Формулы расчёта

### 1. Julian Day (JD)

```
JD = day + (153*m + 2)//5 + 365*y + y//4 - y//100 + y//400 - 32045
JD += (hour + minute/60 + second/3600) / 24
```
где `a = (14 - month)//12`, `y = year + 4800 - a`, `m = month + 12*a - 3`

### 2. Локальное звёздное время (LST)

```
T = (JD - 2451545.0) / 36525.0
GST = 280.46061837 + 360.98564736629*(JD-2451545.0) + T²*(0.000387933 - T/38710000.0)
GST = GST mod 360
LST = (GST + longitude) mod 360
```

### 3. Асцендент (ASC)

```
ASC = arctan2(-cos(HA), sin(lat)*tan(ε) + cos(lat)*sin(HA))
```
где `ε = 23.4393°` (наклон эклиптики), `lat` = широта

### 4. Середина Неба (MC)

```
MC = arctan2(sin(LST)*cos(ε), cos(LST))
```

### 5. Куспиды Плацидуса

```
sin(Decl_Cusp) = sin(Geocentric_Dec) × cos(SemiArc) / cos(Geocentric_DEC)

SemiArc = |RA_ASC - RA_MC|   (если > 180°, то 360 - SemiArc)

Cusp 11 = MC + SemiArc/3
Cusp 12 = MC + 2*SemiArc/3
Cusp 2  = ASC + SemiArc/3
Cusp 3  = ASC + 2*SemiArc/3
```

---

## Реализация (Munkasey formulas)

**Файл:** `file 'AstroFinSentinelV5/core/placidus.py'` (копия из backup)

```python
import math
from dataclasses import dataclass

def julian_day(dt):
    a = (14 - dt.month) // 12
    y = dt.year + 4800 - a
    m = dt.month + 12 * a - 3
    jd = dt.day + (153*m + 2)//5 + 365*y + y//4 - y//100 + y//400 - 32045
    jd += (dt.hour + dt.minute/60 + dt.second/3600) / 24
    return jd

def calculate_placidus_cusps(asc, mc, ra_asc, ra_mc, latitude, declination):
    cusps = [0.0] * 12
    cusps[0] = asc       # House 1 = ASC
    cusps[9] = mc        # House 10 = MC
    cusps[3] = mc + 180  # House 4 = IC
    cusps[6] = asc + 180 # House 7 = DESC
    
    semi_arc = abs(ra_asc - ra_mc)
    if semi_arc > 180:
        semi_arc = 360 - semi_arc
    
    third_arc = semi_arc / 3
    cusps[10] = mc + third_arc      # Cusp 11
    cusps[11] = mc + 2*third_arc   # Cusp 12
    cusps[1]  = asc + third_arc    # Cusp 2
    cusps[2]  = asc + 2*third_arc  # Cusp 3
    
    return cusps
```

---

## Сравнение с другими системами

| Система | Код | Тип | Особенность |
|---------|-----|-----|-------------|
| **Placidus** | **P** | **Time** | Самая популярная, искажения в высоких широтах |
| Koch | K | Time | Американская традиция |
| Campanus | C | Space | Равнораспределённая по сфере |
| Regiomontanus | R | Space | |
| Alcabitius | A | Space | |
| Porphyry | O | Quadrant | Простая, делит квадранты |
| Whole Sign | W | Ecliptic | Древняя, дом = знак |
| Equal | E | Ecliptic | 30° от ASC |

---

## Использование в AstroFinSentinel

В проекте используется **Swiss Ephemeris** для точных планетарных позиций + формулы Munkasey:

```python
from core.ephemeris import get_planetary_positions
from core.placidus import calculate_placidus_cusps

positions = get_planetary_positions(dt, latitude, longitude)
asc = positions['ASC']
mc = positions['MC']
cusps = calculate_placidus_cusps(asc, mc, ra_asc, ra_mc, latitude, declination)
```

---

## Источники

- Munkasey, Michael P. — "An Astrological House Formulary"
- Munkasey, Michael P. — "The Astrological House Handbook"
- Placidus — историческая система, приписывается Ptolemy (蹭?) или неизвестному автору 17 века
