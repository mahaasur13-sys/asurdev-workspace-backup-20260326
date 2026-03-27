---
type:: agent
id:: elliot_agent
tags:: [agent, elliott-wave, technical-analysis, fibonacci]
created:: 2026-03-27
weight:: 0.03
domain:: technical
source:: [[AstroFinSentinelV5/agents/_impl/elliot_agent.py]]

## Назначение

ElliotAgent — анализ волн Эллиотта.

## Обязанности

1. Identifies 5-wave impulse patterns
2. Подсчёт коррективных волн (ABC, zigzag, flat)
3. Детекция wave extensions и truncations
4. Предсказание wave targets с помощью Fibonacci ratios

## Волновая структура

### Импульс (5 волн)

```
Wave 1 → Wave 2 ↓ → Wave 3 ↑ → Wave 4 ↓ → Wave 5 ↑
         ( retraces 0.618×W1)
                              ( retraces 0.382×W1-W3)
```

### Коррекция (3 волны)

```
Wave A ↓ → Wave B ↑ → Wave C ↓
```

## Fibonacci ratios

| Откат | Значение |
|-------|---------|
| Wave 2 | 0.618 × Wave 1 |
| Wave 4 | 0.382 × Wave 1-W3 |
| Wave 3 | 1.618 × Wave 1 |
| Wave 5 | 0.618-1.618 × Wave 1-W3 |

## Концепции

- [[elliott_wave]]
- Fibonacci retracements
- Wave personality

## Backward reference

- Родитель: [[agents_index]]
- Использует: [[technical_agent]] framework

## Реализация

```python
class ElliotAgent(BaseAgent[AgentResponse]):
    weight = 0.03  # 3%
    domain = "technical"
```
