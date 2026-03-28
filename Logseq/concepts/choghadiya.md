---
type:: concept
id:: choghadiya
tags:: [astrology, vedic, muhurta, choghadiya, timing, trading]
aliases:: [чогхадия, чаughадия, временные периоды дня]
created:: 2026-03-29
updated:: 2026-03-29
related:: [[concepts/muhurta]], [[concepts/panchanga]], [[concepts/muhurta_trading]], [[agents/electoral_agent]]

---

# Choghadiya — Временны́е периоды дня

## Определение

**Choghadiya** (चौघडिया, «четыре с половиной») — система деления дня и ночи на 8 равных периодов (Muhurta). Каждый период имеет астрологическое качество, определяющее благоприятность для различных деятельностей.

---

## Структура: 8 Choghadiya

### Дневные мухурты (от восхода Солнца)

| # | Choghadiya | Значение | Трейдинг |
|---|------------|---------|---------|
| 1 | **Amrit** | Бессмертие — ЛУЧШИЙ | OPEN LONG |
| 2 | **Shubh** | Благоприятный | Сделки |
| 3 | **Labh** | Прибыль | LONG |
| 4 | **Char** | Движение | Быстрые решения |
| 5 | **Samarth** | Сила | HOLD |
| 6 | **Vaidhriti** | Нет результата | Выход |
| 7 | **Rog** | Болезнь — ПЛОХОЙ | CLOSE |
| 8 | **Kaal** | Время смерти — ХУДШИЙ | CLOSE |

### Ночные мухурты (от заката)

| # | Choghadiya | Трейдинг |
|---|------------|---------|
| 1 | Udik | CLOSE |
| 2 | Rog | CLOSE |
| 3 | Kaal | CLOSE |
| 4 | Labh | LONG |
| 5 | Shubh | LONG |
| 6 | Amrit | OPEN |
| 7 | Char | Быстрые |
| 8 | Samarth | HOLD |

---

## Расчёт Choghadiya (Swiss Ephemeris)

```python
import swisseph as sw

DAY_NAMES = ["Amrit","Shubh","Labh","Char","Samarth","Vaidhriti","Rog","Kaal"]
NIGHT_NAMES = ["Udik","Rog","Kaal","Labh","Shubh","Amrit","Char","Samarth"]

def calc_choghadiya(jd, lat, lon):
    # Восход и закат
    rise = sw.rise_trans(jd-1, sw.SUN, lat, lon, flr=sw.FLG_SWIEPH)
    rise_jd = rise[1][0]
    set_jd = rise_jd + 0.5  # примерно

    day_len = (set_jd - rise_jd) / 8

    day_fraction = (jd % 1)
    rise_hours = (rise_jd % 1)
    current_hours = day_fraction

    if rise_hours <= current_hours < rise_hours + 12/24:
        # День
        muh = int((current_hours - rise_hours) * 8) % 8
        name = DAY_NAMES[muh]
        favorable = muh in [0, 1, 2]
    else:
        # Ночь
        set_hours = (set_jd % 1)
        muh = int((current_hours - set_hours) * 8) % 8
        name = NIGHT_NAMES[muh]
        favorable = muh in [3, 4, 5]

    return name, favorable
```

---

## Фильтрация для AstroFin Sentinel

```python
def choghadiya_filter(jd, lat=55.75, lon=37.62) -> str:
    name, favorable = calc_choghadiya(jd, lat, lon)
    if not favorable:
        return f"AVOID — {name}"
    if name in ["Amrit", "Labh"]:
        return f"OPEN LONG — {name}"
    if name == "Shubh":
        return f"PROCEED — {name}"
    return f"HOLD — {name}"
```

---

## Muhurta Trading (BSE/NSE)

```
Diwali Muhurta Session: 18:30-19:30 IST
Попадает в Shubh или Labh на Mumbai (19N, 73E)
Историческая прибыль: +0.5-2% за сессию
```

---

## Источники

- Brihat Samhita — Varāhamihira
- Muhurta Chintamani — V.K. Shridhar (1987)
- Surya Siddhanta

---

## Связи

- [[concepts/muhurta]]
- [[concepts/panchanga]]
- [[agents/electoral_agent]]

---

*Создано: 2026-03-29*
