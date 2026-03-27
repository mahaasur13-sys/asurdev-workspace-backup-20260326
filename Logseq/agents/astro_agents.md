---
type:: agent
id:: astro_agents
tags:: [agent, astrology, muhurta, bradley, gann, cycles, time-windows]
created:: 2026-03-27
source:: [[AstroFinSentinelV5/agents/_impl/]]

## AstroCouncil

id:: astro_council_agent
weight:: (coordination only, no direct vote)
domain:: astro

AstroCouncil — координатор астрологического блока. Объединяет результаты всех astro-sub-агентов через `TradingSignal.from_agents()`.

**NOT a voting agent** — только координирует и агрегирует.

### Astro-суб-агенты

| Агент | Вес | Функция |
|-------|-----|---------|
| [[bradley_agent]] | 3% | Сезонность S&P + планетарные аспекты |
| [[electoral_agent]] | 3% | Muhurta timing |
| [[gann_agent]] | 3% | Углы Ганна, квадрат цены/времени |
| [[cycle_agent]] | 5% | Доминантные циклы |
| [[time_window_agent]] | 2% | Мульти-таймфрейм окна |

---

## BradleyAgent

id:: bradley_agent
weight:: 0.03
domain:: technical
source:: [[AstroFinSentinelV5/agents/_impl/bradley_agent.py]]

### Назначение

Модель Брэдли — сезонность S&P 500 на основе планетарных аспектов.

### Обязанности

1. Расчёт Bradley Seasonality Index
2. Идентификация высоковероятных точек разворота
3. Кросс-референс с планетарными аспектами

### Метод

```
Bradley Model = Σ(planetary_aspect_weights × historical_returns)
```

### Эфемериды

- swiss_ephemeris (sweph) → планетарные положения
- 7 планет: Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn

### Ограничения

- Наиболее точен для S&P 500
- Для крипто — адаптированная версия

---

## GannAgent

id:: gann_agent
weight:: 0.03
domain:: technical
source:: [[AstroFinSentinelV5/agents/_impl/gann_agent.py]]

### Назначение

Анализ по методам W.D. Gann.

### Обязанности

1. Расчёт углов Ганна (1×1, 1×2, 2×1)
2. Identifies support/resistance at angle intersections
3. Временные прогнозы (Gann date clusters)
4. Квадрат цены и времени

### Ключевые концепции

- [[gann_theory]]
- 1×1 angle = 45° = 1 unit price per 1 unit time
- Квадрат Ганна (Square of Nine)

---

## CycleAgent

id:: cycle_agent
weight:: 0.05
domain:: technical
source:: [[AstroFinSentinelV5/agents/_impl/cycle_agent.py]]

### Назначение

Анализ доминантных рыночных циклов.

### Обязанности

1. Детекция периодов циклов (20, 40, 80 дней)
2. Идентификация фазы (up/down/transition)
3. Предсказание точек разворота цикла
4. Выравнивание с астро-циклами (Jupiter 12yr, Saturn 29yr)

### Циклы

| Цикл | Тип | Применение |
|------|-----|-----------|
| 20 дней | Short-term | Свинг-трейдинг |
| 40 дней | Medium-term | Позиционная торговля |
| 80 дней | Long-term | Среднесрочные позиции |

### Астро-циклы

- Jupiter → 12-летний цикл
- Saturn → 29-летний цикл
- [[bradley_siderograph]]

---

## TimeWindowAgent

id:: time_window_agent
weight:: 0.02
domain:: astrology
source:: [[AstroFinSentinelV5/agents/_impl/time_window_agent.py]]

### Назначение

Определение лучших окон для входа.

### Обязанности

1. Сканирование нескольких таймфреймов на предмет confluence
2. Identifies optimal entry windows (4H, 1D, 1W)
3. Кросс-референс с астро-таймингом (Choghadiya, Muhurta)
4. Избегание низколиквидных периодов

### Таймфреймы

- 4H → intraday
- 1D → swing
- 1W → positional

### Confluence scoring

```
windows = [4H, 1D, 1W, Astro]
bullish = count of bullish windows
bearish = count of bearish windows
confluence_score = max(bullish, bearish) / len(windows)
```

---

## ElectoralAgent

id:: electoral_agent
weight:: 0.10
domain:: astrology
source:: [[AstroFinSentinelV5/agents/electoral_agent.py]]

### Назначение

Muhurta specialist — выбор оптимального времени для входа.

### Обязанности

1. Сканирование election windows (today/week/month)
2. Расчёт Muhurta scores
3. Избегание плохих периодов (Marana, Vyatipata, Rahukaal)
4. Рекомендация оптимальных окон входа

### Концепции

- [[muhurta_trading]]
- Nakshatra (лунные созвездия, 27)
- Choghadiya (мухурты дня, 8 блоков)

### Результат

```
ENTER → благоприятное окно
WAIT → нейтральное
AVOID → опасный период
```

### Использует

- `astrology.vedic.get_current_nakshatra()`
- `astrology.vedic.get_choghadiya()`

## Backward references

- Родитель: [[agents_index]]
- Координатор: [[astro_council_agent]]
- Концепции: [[muhurta_trading]], [[gann_theory]], [[bradley_siderograph]], [[elliott_wave]]
