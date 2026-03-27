---
type:: concept
id:: bradley_siderograph
tags:: [concept, astrology, seasonality, s&p-500, financial-astronomy]
weight:: 3
created:: 2026-03-27
updated:: 2026-03-27
sources:: [Bradley Model (Edwin G. Sweeney, 1930s–1940s), Bradley Siderograph™ (annual publication), equityclock.com]
---

# Bradley Siderograph — Модель Сезонности S&P 500

## Определение

**Bradley Model (Bradley Siderograph™)** — математическая модель, предсказывающая движения фондового рынка на основе взаимного расположения планет. Создана **Эдвином Брэдли (Edwin J. Bradley)** в 1930-х годах.

> «Bradley Model работает на предпосылке, что гравитационные поля планет оказывают измеримое влияние на коллективную психологию рынка.»

---

## Как работает модель

### Основной механизм

1. **12 планет** (включая Солнце и Луну) → 12 знаков зодиака
2. **66 пар планет** → **300+ аспектов** (точные + орбисы)
3. Каждый аспект → **Siderograph Index** (сумма: благоприятные +, неблагоприятные −)
4. **Итоговый индекс** предсказывает направление рынка

### Формула индекса (упрощённо)

```
Bradley Index = Σ (вес_аспекта × сигнал_аспекта)

где:
  сигнал_аспекта = +1 (благоприятный) | -1 (неблагоприятный) | 0 (нейтральный)
  вес_аспекта = f(тип_аспекта, орбис)
```

### Ключевые аспекты

| Аспект | Градус | Сигнал | Орбис |
|--------|--------|--------|-------|
| ☌ Conjunction | 0° | − | ±8° |
| ⚹ Sextile | 60° | + | ±6° |
| □ Square | 90° | − | ±8° |
| △ Trine | 120° | + | ±8° |
| ☍ Opposition | 180° | − | ±10° |

> **Важно:** В Bradley Model традиционные аспекты **инвертированы** — соединение (0°) считается напряжённым, а не гармоничным.

---

## Доверительный интервал

| Значение индекса | Сигнал |
|-----------------|--------|
| **+100 и выше** | Сильный бычий |
| **+50...+100** | Умеренный бычий |
| **−50...+50** | Нейтральный |
| **−50...−100** | Умеренный меджий |
| **−100 и ниже** | Сильный медвежий |

---

## Как применяется в AstroFin Sentinel

### BradleyAgent (agents/_impl/bradley_agent.py)

```python
class BradleyAgent(BaseAgent[AgentResponse]):
    """
    BradleyAgent — модель Брэдли (сезонность S&P 500).
    Weight: 3%
    """

    async def analyze(self, state: dict) -> AgentResponse:
        # Bradley seasonality
        seasonality = self._calculate_seasonality(price_data)
        planetary_aspects = await self._check_planetary_aspects(state)

        bradley_score = (
            seasonality["score"] * 0.50 +
            planetary_aspects["score"] * 0.50
        )

        if bradley_score >= 0.60:
            signal = SignalDirection.LONG
        elif bradley_score <= 0.35:
            signal = SignalDirection.SHORT
        else:
            signal = SignalDirection.NEUTRAL
```

### Два компонента

1. **Seasonality Score** (50%) — сезонность по историческим данным дня года
2. **Planetary Aspects Score** (50%) — текущие аспекты Юпитер-Сатурн, Юпитер-Уран, Сатурн-Уран

### Planetary Aspects в коде

```python
# Юпитер-Сатурн (главный цикл ~20 лет)
js_angle = abs(jupiter.longitude - saturn.longitude) % 360

# Юпитер-Уран (революционный цикл ~14 лет)
ju_angle = abs(jupiter.longitude - uranus.longitude) % 360

# Сатурн-Уран (поколенческий цикл)
su_angle = abs(saturn.longitude - uranus.longitude) % 360

# Орбис: ±8°
for aspect_deg in [0, 60, 90, 120, 180]:
    if abs(angle - aspect_deg) < 8:
        aspects_found.append(f"J-S {aspect_deg}°")
```

---

## Изображения

![Bradley Siderograph S&P 500 Seasonality (1950–2014)](https://i0.wp.com/leadingtrader.com/images/sp500-seasonality.png?resize=650,414)
*Рис.1 — Сезонность S&P 500 по Bradley Model: pre-election годы vs общий паттерн*

![Bradley Siderograph 2015–2025](https://miro.medium.com/v2/resize:fit:1400/1*fR6LiK3O6GdqdS8RXJtxrA.png)
*Рис.2 — Bradley Siderograph 2015–2025: влияние начинает расти с 25 октября и кульминирует к 30 ноября*

![Bradley + Long-term Rate of Change](https://i.ytimg.com/vi/rARdsOUZoHM/maxresdefault.jpg)
*Рис.3 — 10-летний S&P 500 с Bradley Siderograph: пик август 2017 (жёлтый спотлайт)*

---

## Ограничения модели

| Проблема | Описание |
|---------|---------|
| **S&P 500 only** | Модель разработана для фондового рынка США; для крипты адаптирована частично |
| **Вес 3%** | Ограниченный вклад в итоговый сигнал (система взвешенная) |
| **Ephemeris required** | Работает только при наличии Swiss Ephemeris |
| **Historical bias** | Данные до 1950 года менее надёжны |

---

## Дополнительные источники

| Источник | Примечание |
|---------|-----------|
| [equityclock.com](https://www.equityclock.com) | Ежегодные Bradley Siderograph чарты |
| [Bradley Model PDF](https://www.sectorrotation.org) | Оригинальная методология |
| [leadingtrader.com](https://www.leadingtrader.com) | Сезонность S&P 500 |

---

## Связанные концепции

- [[muhurta_trading]] — выбор момента для входа
- [[market_cycles]] — рыночные циклы
- [[gann_theory]] — углы Ганна
- [[ephemeris_calculations]] — расчёт эфемерид

---

## Теги

#concept #astrology #seasonality #bradley #siderograph #sp500 #financial-astronomy #planetary-aspects
