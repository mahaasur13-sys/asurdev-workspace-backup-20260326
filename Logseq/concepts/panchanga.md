---
type:: concept
id:: panchanga
tags:: [astrology, vedic, panchanga, tithi, nakshatra, yoga, karana, choghadiya]
aliases:: [панчанга, пять элементов, индийский календарь]
created:: 2026-03-29
updated:: 2026-03-29
related:: [[concepts/muhurta]], [[concepts/choghadiya]], [[concepts/muhurta_trading]], [[agents/electoral_agent]], [[methods/ephemeris_calculations]]

---

# Panchanga — Пять элементов индийского астрологического календаря

## Определение

**Panchanga** (санскр. पञ्चाङ्ग, «пять конечностей») — традиционный индийский астрологический календарь, содержащий **пять ключевых элементов** для определения астрологического качества любого момента времени.

| # | Элемент | Значение |
|---|---------|---------|
| 1 | **Tithi** | Лунный день (фаза Луны) |
| 2 | **Nakshatra** | Лунная стоянка (27 звёзд) |
| 3 | **Yoga** | Комбинация положения Солнца и Луны |
| 4 | **Karana** | Половина лунного дня |
| 5 | **Var** | День недели (7 дней) |

---

## Происхождение

| Текст | Период | Описание |
|-------|--------|---------|
| **Surya Siddhanta** | ~400 н.э. | Древнейший трактат по астрономии |
| **Brihat Samhita** | Varāhamihira, 6 в. | Энциклопедия с главами о Panchanga |

---

## 1. Tithи (Титхи) — Лунный день

**Формула:**
```
Tithи = floor((λ_Moon - λ_Sun) / 12°) % 30
```

| Категория | Tithи | Значение |
|-----------|-------|---------|
| **Nanda** (растительные) | 1, 6, 11 | Рост, начинания |
| **Bhadra** (демонические) | 3, 7, 9, 13 | Болезни, потери |
| **Jaya** (победа) | 4, 8, 12 | Успех |
| **Rikta** (пустые) | 5, 10, 15, 30 | Не начинать |

**Ключевые титхи:**

| Tithи | Название | Трейдинг |
|-------|---------|---------|
| 1 | Pratipat | Начинания |
| 7 | Saptami | Избегать |
| 9 | Navami | Избегать |
| 11 | Ekadashi | Решение проблем |
| 15 | Purnima | Эмоции |
| 30 | Amavasya | Новолуние — избегать |

---

## 2. Nakshatra (Накшатра) — Лунная стоянка

**Формула:**
```
Nakshatra = floor(λ_Moon / 13°20') % 27
```

**Благоприятные для торговли:**

| Nakshatra | Качество | Трейдинг |
|-----------|---------|---------|
| Rohini | Artha | Отлично |
| Pushya | Dharma | Отлично |
| Swati | Artha | Отлично |
| Hasta | Artha | Хорошо |
| Shravana | Dharma | Хорошо |
| Revati | Dharma | Хорошо |

**Избегать для торговли:**

| Nakshatra | Причина |
|-----------|---------|
| Mula | Корень разрушения |
| Ashlesha | Змеиные объятия |
| Jyeshtha | Старший — опасен |
| Ardra | Буря — хаос |

---

## 3. Yoga (Йога) — Комбинация планет

**Формула:**
```
Yoga = floor((λ_Sun + λ_Moon) / 13°20') % 27
```

| Yoga | Значение |
|------|---------|
| Shubha | Благоприятная |
| Siddhi | Успех |
| Vriddhi | Рост |
| Amrita | Бессмертие |
| Vaidhriti | Разрушение |

---

## 4. Karana (Карана) — Половина Tithи

11 уникальных каран, делящих титхи пополам. Ключевые — Gulika (все титхи, ограничение) и Naga (титхи 3, 8, 13).

---

## 5. Vara (Ва̄ра) — День недели

| День | Планета | Трейдинг |
|------|---------|---------|
| Sunday | Солнце | Эмоции |
| Monday | Луна | Интуиция |
| Tuesday | Марс | Риск |
| Wednesday | Меркурий | Анализ |
| Thursday | Юпитер | Инвестиции |
| Friday | Венера | Переговоры |
| Saturday | Сатурн | Медленно |

---

## Расчёт (Swiss Ephemeris)

```python
import swisseph as sw

def panchanga_now(lat=55.75, lon=37.62, jd=None):
    sun = sw.calc_ut(jd, sw.SUN)
    moon = sw.calc_ut(jd, sw.MOON)

    tithi = int((moon[0] - sun[0] + 360) % 360 / 12)
    nak = int(moon[0] / (13 + 20/60)) % 27
    yoga_idx = int((sun[0] + moon[0]) / (13 + 20/60)) % 27
    vara = int((jd + 1.5) % 7)

    return {
        "tithi": tithi + 1,
        "nakshatra": nak + 1,
        "yoga": yoga_idx + 1,
        "vara": ["Sunday","Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"][vara]
    }
```

---

## Источники

- Surya Siddhanta (~400 н.э.)
- Brihat Samhita — Varāhamihira
- V.K. Shridhar. Electional Astrology — Muhurta Chintamani (1987)
