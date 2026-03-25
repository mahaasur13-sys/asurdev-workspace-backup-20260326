# Справочник формул домов гороскопа
## Michael P. Munkasey — "An Astrological House Formulary"

> **Источник:** Michael P. Munkasey, "An Astrological House Formulary" (формулы адаптированы из открытых обсуждений на Astro.com, Scribd, GitHub)

---

## Системы домов

### 1. PLACIDUS

**Тип:** Временная (Time-Based)
**История:** 1603 год, Плиниус де Титис

**Принцип:** Делит дневную дугу (от восхода до заката) и ночную дугу на 6 равных частей каждую.

**Формулы:**

```
 SemiArc = RA_Asc - RA_MC (для полудиапазона)
 
 Куспы 11, 12, 2, 3:
 
  sin(Declination_of_Cusp) = sin(Geocentric_Dec) × cos(SemiArc) / cos(Geocentric_DEC)
  
  Для дома 11:
    RA_Cusp11 = RA_MC + (1/3) × SemiArc
    
  Для дома 12:
    RA_Cusp12 = RA_MC + (2/3) × SemiArc
    
  Для дома 2:
    RA_Cusp2 = RA_Asc + (1/3) × SemiArc_Night
    
  Для дома 3:
    RA_Cusp3 = RA_Asc + (2/3) × SemiArc_Night
```

---

### 2. KOCH

**Тип:** Временная (Time-Based)
**История:** 1962 год, Вальтер Эрнст Кох

**Принцип:** Делит расстояние от Асцендента до Середины Неба (куспиды 12 и 11) пропорционально времени восхода.

**Формулы:**

```
 ASC = arctan( (cos(Obliquity) × sin(HourAngle)) / 
                (sin(Obliquity) × cos(Latitude) - 
                 cos(Obliquity) × sin(Latitude) × cos(HourAngle)) )
 
 MC = arctan( tan(RA_Sun) / cos(Obliquity) )
 
 Для домов 11 и 12:
   Cusp11 = Asc + (1/3) × arc(Asc → MC)
   Cusp12 = Asc + (2/3) × arc(Asc → MC)
```

---

### 3. CAMPANUS

**Тип:** Пространственная (Space-Based)
**История:** 13 век, Йоанн де Кампано

**Принцип:** Делит первый вертикал (небесный меридиан) на равные части.

**Формулы:**

```
  Primary Vertical = 90° от горизонта
  
  MC = arctan( tan(RA) / cos(Obliquity) )
  
  Куспиды через небесный экватор:
    Cusp11 = 30° от MC по экватору
    Cusp12 = 60° от MC по экватору
    Cusp2  = 30° от ASC по экватору
    Cusp3  = 60° от ASC по экватору
```

**Примечание Munkasey:** Campanus даёт "нелепые куспиды" при неправильной реализации — нужна проверка квадрантов.

---

### 4. REGIOMONTANUS

**Тип:** Пространственная (Space-Based)
**История:** 15 век, Региомонтан

**Принцип:** Делит эклиптику через проекцию на небесный экватор.

**Формулы:**

```
  MC = arctan( tan(RA_Sun) / cos(Obliquity) )
  
  Для дома 11:
    declination_11 = arcsin( sin(Declination_MC) / 3 )
    RA_Cusp11 = arcsin( tan(declination_11) / tan(90° - Geographic_Latitude) )
```

---

### 5. ALCABITIUS

**Тип:** Пространственная (Space-Based)
**История:** 13 век, Аль-Кабиси

**Принцип:** Делит экваториальные квадранты на равные части.

**Формулы:**

```
  1. RA_Difference = RA_Asc - RA_MC
  2. Divide_by_3 = RA_Difference / 3
  
  Cusp11 = RA_MC + Divide_by_3
  Cusp12 = RA_MC + 2 × Divide_by_3
  
  Cusp2 = RA_Asc + Divide_by_3
  Cusp3 = RA_Asc + 2 × Divide_by_3
  
  Longitude_of_Cusp2:
    Если отрицательное → добавить 180°
```

---

### 6. PORPHYRY

**Тип:** Квадрантная (Quadrant)
**История:** Древняя Греция (~200 н.э.)

**Принцип:** Просто делит квадранты поровну.

**Формулы:**

```
  Cusp11 = MC + (Asc - MC) / 3
  Cusp12 = MC + 2 × (Asc - MC) / 3
  
  Cusp2 = Asc + (Desc - Asc) / 3
  Cusp3 = Asc + 2 × (Desc - Asc) / 3
```

---

### 7. WHOLE SIGN

**Тип:** Эклиптическая (Ecliptic)
**История:** Древняя Греция, эллинистическая астрология

**Принцип:** Дом 1 = знак восходящего градуса, остальные следуют по 30°.

**Формулы:**

```
  House 1 = Знак Ascendant (0°-30° этого знака)
  House 2 = Следующий знак (30°-60°)
  House 3 = Следующий знак (60°-90°)
  ...
  House 12 = 30° до знака Ascendant
```

---

### 8. EQUAL HOUSE (Equal from Ascendant)

**Тип:** Эклиптическая (Ecliptic)

**Принцип:** Все дома по 30°, начиная от Ascendant.

**Формулы:**

```
  Cusp1 = ASC_Longitude
  Cusp2 = ASC_Longitude + 30°
  Cusp3 = ASC_Longitude + 60°
  ...
  Cusp12 = ASC_Longitude + 330°
```

---

### 9. EQUAL from MC

**Тип:** Эклиптическая (Ecliptic)

**Принцип:** MC на куспиде 10, дома по 30° от MC.

**Формулы:**

```
  Cusp10 = MC_Longitude
  Cusp11 = MC_Longitude + 30°
  ...
  Cusp9 = MC_Longitude - 30°
```

---

## Ключевые астрологические точки

### ASCENDANT (ASC)

```
Формула вычисления Асцендента (из Munkasey's "An Astrological House Formulary"):

ASC = arctan( -cos(HourAngle) / 
              (sin(Latitude) × tan(Declination) + 
               cos(Latitude) × sin(HourAngle)) )

Где:
  HourAngle = GST - RA_culminating_planet (для ASC - это точка пересечения горизонта)
  Latitude = географическая широта места рождения
  Declination = склонение точки на эклиптике
```

### MIDHEAVEN (MC)

```
MC = arctan( tan(RA_Sun_at_MC) / cos(Obliquity_of_Ecliptic) )

Альтернативно через RA:
  MC_RA = RA_at_culmination (прямое восхождение в верхней кульминации)
```

---

## Реализация в коде

### Python (используя Swiss Ephemeris / pyswisseph)

```python
import math
from datetime import datetime
import swisseph as swe

def calculate_ascendant(jd, lat, lon):
    """Расчёт Асцендента по формуле Munkasey"""
    # Получаем эклиптическую долготу Солнца
    pos = swe.calc_ut(jd, swe.SUN)
    lon_sun = pos[0][0]
    
    # Склонение и правое восхождение
    obliquity = math.radians(23.4393)  # наклон эклиптики
    
    # Приближённый расчёт ASC
    asc = math.degrees(math.atan2(
        -math.cos(math.radians(lon_sun - lon)),
        (math.sin(math.radians(lat)) * math.tan(obliquity) +
         math.cos(math.radians(lat)) * math.sin(math.radians(lon_sun - lon)))
    ))
    
    if asc < 0:
        asc += 360
    
    return asc
```

---

## Классификация систем домов

| Система | Тип | Класс | Регион популярности |
|---------|-----|-------|---------------------|
| Placidus | Время | Современный | США, Европа |
| Koch | Время | Современный | Германия, Австрия |
| Whole Sign | Эклиптика | Древний | Греция, Индия (Jyotish) |
| Porphyry | Квадрант | Древний | Эллинистический |
| Campanus | Пространство | Средневековый | Италия |
| Regiomontanus | Пространство | Средневековый | Европа |
| Alcabitius | Пространство | Средневековый | Арабская традиция |
| Equal House | Эклиптика | Универсальный | Универсальный |
| Topocentric | Время | Современный | Южная Америка |

---

## Библиография

1. Munkasey, Michael P. "An Astrological House Formulary" — основной источник формул
2. Munkasey, Michael P. "House Keywords and More..." — Llewellyn Modern Astrology Library
3. Meeus, Jean. "Astronomical Algorithms" — астрономические расчёты
4. Ribero, Luis. "On the Heavenly Spheres" — история и математика систем домов

---

## Ссылки

- [Astro.com Forum — Munkasey Campanus formula discussion](https://www.astro.com/forarch/pdf/1470514486.pdf)
- [Scribd — An Astrological House Formulary](https://www.scribd.com/doc/6495552)
- [GitHub — CircularNatalHoroscopeJS (реализация формул Munkasey)](https://github.com/0xStarcat/CircularNatalHoroscopeJS)
- [The Astrology Podcast — House Division Calculations](https://theastrologypodcast.com/2021/07/31/house-division-calculations-in-astrology-explained/)
