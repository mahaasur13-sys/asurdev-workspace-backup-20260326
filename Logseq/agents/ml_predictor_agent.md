---
type:: agent
id:: ml_predictor_agent
tags:: [agent, ml, prediction, volatility-forecast]
created:: 2026-03-27
weight:: 0.10
domain:: quant
source:: [[AstroFinSentinelV5/agents/_impl/ml_predictor_agent.py]]

## Назначение

MLPredictorAgent — ML-предсказания волатильности и направления цены.

## Обязанности

1. Предсказание ценового направления с помощью ML-моделей
2. Прогнозирование режимов волатильности
3. Генерация доверительных интервалов
4. Оптимизация размера позиции на основе уверенности предсказания

## Входные данные

- `symbol` — торговый символ
- `timeframe_requested` — временной горизонт (SWING)
- `current_price` — текущая цена

## Метрики

| Метрика | Описание |
|---------|---------|
| Price direction | Направление (LONG/SHORT/NEUTRAL) |
| Volatility regime | LOW/NORMAL/HIGH/EXTREME |
| Confidence interval | 95% CI для целевой цены |
| Position size | Kelly-optimal размер |

## Backward reference

- Родитель: [[agents_index]]
- Часть: Quant-блок
- Использует: [[volatility_engine]]

## Реализация

```python
class MLPredictorAgent(BaseAgent[AgentResponse]):
    weight = 0.10  # 10%
    domain = "quant"
```
