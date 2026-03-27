---
type:: agent
id:: insider_agent
tags:: [agent, insider, 13f-filings, institutional]
created:: 2026-03-27
weight:: 0.08
domain:: fundamental
source:: [[AstroFinSentinelV5/agents/_impl/insider_agent.py]]

## Назначение

InsiderAgent — анализ инсайдерских сделок и 13F-файлингов.

## Обязанности

1. Track insider buying/selling (Form 4)
2. Анализ изменений институциональных позиций (13F)
3. Детекция unusual insider activity
4. Кросс-референс с ценовым действием

## Метрики

| Метрика | Вес |
|---------|-----|
| Insider trades | 50% ( Form 4) |
| 13F filings changes | 30% |
| Unusual activity detection | 20% |

## Источники данных

| Источник | Тип | Статус |
|---------|-----|--------|
| SEC EDGAR Form 4 | Бесплатный | ✅ |
| SEC EDGAR 13F | Бесплатный | ✅ |
| Insider tracking API | Платный | ⚠️ |

## Backward reference

- Родитель: [[agents_index]]
- Часть: Fundamental+Macro блок (8%)

## Реализация

```python
class InsiderAgent(BaseAgent[AgentResponse]):
    weight = 0.08  # 8%
    domain = "fundamental"
```
