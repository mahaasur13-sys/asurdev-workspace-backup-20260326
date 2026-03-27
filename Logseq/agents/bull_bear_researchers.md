---
type:: agent
id:: bull_researcher
tags:: [agent, bullish, patterns, volume, support-zones]
created:: 2026-03-27
weight:: 0.05
domain:: trading
source:: [[AstroFinSentinelV5/agents/_impl/bull_researcher.py]]

## Назначение

BullResearcher ищет бычий кейс для актива: паттерны, фундаментальные катализаторы, зоны поддержки, объёмы. Агент генерирует LONG или NEUTRAL сигнал с обоснованием.

## Обязанности (BullResearcher)

1. Детекция бычьих свечных паттернов
2. Анализ позитивных фундаментальных/новостных катализаторов
3. Идентификация зон поддержки и накопления
4. Астро-оверлей: Jupiter, Moon phases

## Метрики

| Метрика | Вес |
|---------|-----|
| Бычьи паттерны (высшие минимумы, пробои) | 30% |
| Объём (растущий/падающий) | 25% |
| Зоны поддержки (близость к цене) | 20% |
| Астрология (Jupiter, Moon waxing) | 25% |

## Логика сигнала

```
bullish_score >= 0.65 → LONG (confidence = score * 100 + 10, max 85)
bullish_score >= 0.45 → NEUTRAL (confidence = 50)
bullish_score < 0.45 → NEUTRAL (confidence = 35)
```

## Астро-оверлей BullResearcher

- Jupiter в бычьем знаке → +0.20 к скору
- Moon waxing (первая половина цикла, <50%) → +0.10

## Backward reference

- Родитель: [[agents_index]]
- Синоним: [[bear_researcher]]
- Использует: [[ephemeris_calculations]]

## Реализация

```python
class BullResearcherAgent(BaseAgent[AgentResponse]):
    weight = 0.05  # 5%
    domain = "trading"
```

---

## BearResearcher

id:: bear_researcher
tags:: [agent, bearish, patterns, volume, resistance-zones]
weight:: 0.05
domain:: trading
source:: [[AstroFinSentinelV5/agents/_impl/bear_researcher.py]]

### Назначение

BearResearcher ищет медвежий кейс: медвежьи паттерны, негативные катализаторы, зоны сопротивления, дистрибуция.

### Обязанности

1. Детекция медвежьих свечных паттернов
2. Анализ негативных фундаментальных/новостных катализаторов
3. Идентификация зон сопротивления и дистрибуции
4. Астро-оверлей: Saturn, Mars aspects

### Метрики

| Метрика | Вес |
|---------|-----|
| Медвежьи паттерны (низшие максимумы, пробои вниз) | 30% |
| Объём | 25% |
| Зоны сопротивления | 20% |
| Астрология (Saturn, Mars retrograde) | 25% |

### Астро-оверлей BearResearcher

- Saturn в медвежьем знаке (Taurus, Cancer, Capricorn) → +0.20
- Mars retrograde → +0.15

### Логика сигнала

```
bearish_score >= 0.65 → SHORT (confidence = score * 100 + 10, max 85)
bearish_score >= 0.45 → NEUTRAL (confidence = 50)
bearish_score < 0.45 → NEUTRAL (confidence = 35)
```
