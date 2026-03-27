---
type:: concept
id:: market_cycles
tags:: [concept, technical-analysis, cycles, astro-cycles, wycleoff]
weight:: 5
created:: 2026-03-27
updated:: 2026-03-27
sources:: [W.D. Gann, Raymond A. Merriman, AstroFin Sentinel V5 cycle_agent.py]
---

# Market Cycles — Рыночные Циклы

## Определение

**Market Cycles** — повторяющиеся паттерны в поведении цены, обусловленные комбинацией человеческой психологии, экономических циклов и астрологических факторов.

> «Рынки движутся в волнах — не потому что они случайны, а потому что человеческая природа неизменна.» — Реймонд Мерриман

---

## Фазы рыночного цикла

### Wyckoff Market Cycle (4 фазы)

```
     Цена
      ▲
      │    ┌──────────┐         ┌──────────┐
      │    │MARKUP    │         │MARKUP    │
      │   ╱          ╲        ╱          ╲
      │  ╱            ╲      ╱            ╲
      │ ╱   ACCUMU-   ╲    ╱  DISTRIBU-  ╲
      │╱    LATION    ╲  ╱    -TION       ╲
      └──────────────────────────────────────▶ Время
       ▲              ▲▲▲            ▲
       │              │││            │
    Начало         Пик           Дно
    накопления     распр.        ликвидации
```

| Фаза | Название | Поведение | Действие |
|------|---------|-----------|---------|
| 1 | **Accumulation** (Накопление) | Цена в диапазоне, умные деньги покупают | Наблюдать, готовиться |
| 2 | **Markup** (Рост) | Прорыв вверх, тренд формируется | Покупать на откатах |
| 3 | **Distribution** (Распределение) | Цена в диапазоне вверху, умные деньги продают | Продавать / шортить |
| 4 | **Markdown** (Падение) | Тренд вниз, panic selling | Шортить, не ловить ножи |

### Stan Weinstein's Phase Analysis

| Фаза | RSI (30/70) | MA (200) | Объём | Сигнал |
|------|-------------|----------|-------|--------|
| **1 — Breaking out** | > 50 | Цена выше | Растущий | BUY |
| **2 — Advanced stage** | > 65 | Сильный uptrend | Нормальный | HOLD |
| **3 — Topping** | 30–70 | Цена ниже | Дивергенция | SELL |
| **4 — Base building** | < 30 | Консолидация | Низкий | WATCH |

---

## Циклы Времени

### Ключевые периоды

| Цикл | Период | Источник | Применение |
|------|--------|---------|-----------|
| **20 дней** | ~4 недели | Trading | Краткосрочные входы |
| **40 дней** | ~8 недель | Trading | Среднесрочные тренды |
| **80 дней** | ~16 недель | Trading | Коррекции |
| **1 год** | 365 дней | Солнечный | Сезонность |
| **Jupiter** | 11.86 лет | Астрологический | Долгосрочные тренды |
| **Saturn** | 29.46 лет | Астрологический | Экономические циклы |
| **Jupiter-Saturn** | 19.86 лет | Астрологический | Цикл Коньюнкции |
| **Uranus-Neptune** | 171.3 года | Астрологический | Поколенческие тренды |

### Цикл Юпитер-Сатурн (19.86 лет)

| Конфигурация | Значение | Последняя дата |
|-------------|---------|---------------|
| ☌ Conjunction | Начало нового цикла | 2000.5 (Водолей) |
| △ First Trine | early Bull | 2006–2007 |
| □ First Square | Mid-cycle correction | 2010 |
| ▽ Last Trine | Late Bull | 2018–2019 |
| □ Last Square | Pre-bear | 2020 |
| ☍ Opposition | Bear market | 2025–2026 (прогноз) |

---

## Автокорреляционный анализ

В `cycle_agent.py` используется **автокорреляция** для определения доминирующего цикла:

```python
def _find_dominant_cycle(self, data: list) -> dict:
    test_periods = [20, 30, 40, 60, 80]

    for period in test_periods:
        # Автокорреляция при лаге = period
        corr_sum = sum(
            (closes[i] - mean) * (closes[i - period] - mean)
            for i in range(period, len(closes))
        )
        corr = corr_sum / var

        if corr > best_corr:
            best_period = period
            best_corr = corr

    return {"period": best_period, "strength": min(abs(best_corr), 1.0)}
```

---

## Определение фазы цикла

```python
def _get_cycle_phase(self, data: list, dominant_cycle: dict) -> dict:
    period = dominant_cycle["period"]
    recent = closes[-period:]
    mid_point = (max(recent) + min(recent)) / 2

    if newest > oldest:  # uptrend
        if newest > mid_point:
            phase_name = "late_stage"  # сила 0.7
        else:
            phase_name = "early_stage"  # сила 0.6
    else:  # downtrend
        if newest < mid_point:
            phase_name = "late_stage"
        else:
            phase_name = "early_stage"

    return {"name": phase_name, "direction": direction, "strength": strength}
```

### Фазы в AstroFin Sentinel

| Phase Name | Direction | Strength | Сигнал |
|------------|-----------|----------|--------|
| `early_stage` | up | 0.6 | LONG |
| `late_stage` | up | 0.7 | LONG |
| `early_stage` | down | 0.6 | SHORT |
| `late_stage` | down | 0.7 | SHORT |

---

## Предсказание поворотных точек

```python
def _predict_turning_point(self, data, dominant_cycle, cycle_phase):
    period = dominant_cycle["period"]

    if cycle_phase["direction"] == "up":
        next_direction = "down"
        eta_days = period // 4  # ~четверть цикла до разворота
    else:
        next_direction = "up"
        eta_days = period // 4

    return {
        "direction": next_direction,
        "eta_days": eta_days,
        "confidence": cycle_phase["strength"] * 0.8
    }
```

---

## Астрологическая привязка

### Jupiter-Saturn Alignment

```python
async def _check_astro_cycles(self, state: dict) -> dict:
    jupiter = calculate_planet("jupiter", jd)
    saturn = calculate_planet("saturn", jd)

    angle = abs(jupiter.longitude - saturn.longitude) % 360

    if 115 <= angle <= 125:  # Trine (120°)
        score = 0.70  # Бычий
    elif 175 <= angle <= 185:  # Opposition (180°)
        score = 0.55  # Нейтральный
    else:
        score = 0.45  # Медвежий

    return {"score": score, "summary": f"Jupiter-Saturn angle: {angle:.0f}°"}
```

| Угол J-S | Интерпретация | Score |
|----------|--------------|-------|
| **Trine (120°)** | Бычий — гармоничный аспект | 0.70 |
| **Opposition (180°)** | Нейтральный — напряжение, но возможен подъём | 0.55 |
| **Square (90°)** | Медвежий — напряжение | 0.40 |
| **Conjunction (0°)** | Медвежий — начало нового цикла | 0.35 |

---

## Интеграция в CycleAgent

```python
# Cycle alignment score = 60% технический + 40% астрологический
cycle_score = (
    cycle_phase["strength"] * 0.6 +
    astro_cycles["score"] * 0.4
)

if cycle_phase["direction"] == "up" and cycle_score > 0.55:
    signal = SignalDirection.LONG
elif cycle_phase["direction"] == "down" and cycle_score > 0.55:
    signal = SignalDirection.SHORT
else:
    signal = SignalDirection.NEUTRAL
```

---

## Изображения

![Market Cycle 4 фазы Wyckoff](https://cdn.arongroups.co/uploads/2025/10/market-cycles-2-1024x711.jpg)
*Рис.1 — Четыре фазы рыночного цикла Wyckoff: Accumulation → Markup → Distribution → Markdown*

![Accumulation to Markup](https://www.financial-spread-betting.com/wp-content/uploads/2019/06/accumulation-markup.jpg)
*Рис.2 — Полный цикл: накопление, рост, распределение, ликвидация, повторное накопление*

---

## Дополнительные источники

| Источник | Тема |
|---------|------|
| R.A. Merriman — «The Major Planning Course» | Солнечные циклы |
| W.D. Gann — «The Basis of My Forecasting Method» | Циклы времени |
| Richard Wyckoff — «Stock Market Technique» | 4 фазы |
| Stan Weinstein — «Secrets for Profiting in Bull and Bear Markets» | Прорывы |

---

## Связанные концепции

- [[bradley_siderograph]] — сезонность S&P 500
- [[gann_theory]] — углы и квадраты Ганна
- [[muhurta_trading]] — астрологический тайминг входа
- [[andrews-pitchfork]] — медианная линия

---

## Теги

#concept #cycles #market-cycles #wyckoff #accumulation #distribution #trading #technical-analysis #astro-cycles #jupiter #saturn
