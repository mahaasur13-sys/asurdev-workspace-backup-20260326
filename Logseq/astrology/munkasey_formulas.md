---
title: Munkasey Formulas — Формулы домов Манкаси
type:: concept
id:: munkasey_formulas
tags:: [concept, astrology, houses, munkasey, formulas]
description: Полный набор формул из книги Michael P. Munkasey
icon: 🧮
related::
  - "[[placidus]]"
  - "[[houses_systems]]"
  - "[[electoral_agent]]"
created: 2026-03-27
---

# Munkasey Formulas

**Источник:** Michael P. Munkasey — "An Astrological House Formulary"

## 8 систем домов

```
1. Placidus      (P)  — Time-based
2. Koch          (K)  — Time-based  
3. Campanus      (C)  — Space-based
4. Regiomontanus (R)  — Space-based
5. Alcabitius    (A)  — Space-based
6. Porphyry      (O)  — Quadrant
7. Whole Sign    (W)  — Ecliptic
8. Equal         (E)  — Ecliptic (from ASC)
```

## Формулы

### Julian Day
```python
a = (14 - month) // 12
y = year + 4800 - a
m = month + 12*a - 3
JD = day + (153*m + 2)//5 + 365*y + y//4 - y//100 + y//400 - 32045
```

### LST
```python
T = (JD - 2451545.0) / 36525.0
GST = 280.46061837 + 360.98564736629*(JD-2451545.0) + T²*(0.000387933 - T/38710000.0)
LST = (GST + longitude) mod 360
```

### ASC
```python
ASC = arctan2(-cos(LST), sin(lat)*tan(ε) + cos(lat)*sin(LST))
```

### MC
```python
MC = arctan2(sin(LST)*cos(ε), cos(LST))
```

### Placidus
```python
SemiArc = |RA_ASC - RA_MC|
Cusp11 = MC + SemiArc/3
Cusp12 = MC + 2*SemiArc/3
Cusp2  = ASC + SemiArc/3
Cusp3  = ASC + 2*SemiArc/3
```

### Porphyry
```python
Cusp11 = MC + (ASC-MC)/3
Cusp12 = MC + 2*(ASC-MC)/3
```

### Alcabitius
```python
RA_diff = RA_ASC - RA_MC
Cusp11 = RA_MC + RA_diff/3
Cusp12 = RA_MC + 2*RA_diff/3
```

### Whole Sign
```python
ASC_sign_start = floor(ASC / 30) * 30
Cusp[i] = ASC_sign_start + i*30
```

## Реализация

**Файл:** `file 'AstroFinSentinelV5/core/houses.py'`

## Использование

```python
from core.houses import HouseCalculator, HOUSE_SYSTEMS

calc = HouseCalculator('P')  # Placidus
houses = calc.calculate(jd=jd, latitude=lat, longitude=lon)
print(houses['cusps'])  # [cusp1, cusp2, ..., cusp12]
```
