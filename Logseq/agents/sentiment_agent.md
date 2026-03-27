---
type:: agent
id:: sentiment_agent
tags:: [agent, sentiment, fear-greed, social-media, funding-rates]
created:: 2026-03-27
weight:: 0.10
domain:: sentiment
source:: [[AstroFinSentinelV5/agents/_impl/sentiment_agent.py]]

## Назначение

SentimentAgent анализирует настроения рынка: Fear & Greed Index, социальные медиа (Twitter, Reddit), фандинговые ставки (для крипто), и выдаёт contrarian-сигналы.

## Обязанности

1. Fetch Fear & Greed Index
2. Анализ социальных медиа (Twitter, Reddit, StockTwits)
3. Детекция contrarian-сигналов
4. Отслеживание funding rates (crypto)

## Входные данные

- `symbol` — торговый символ (default: BTCUSDT)
- `current_price` — текущая цена
- `timeframe_requested` — временной горизонт

## Выход

```python
AgentResponse(
    agent_name="SentimentAgent",
    signal=SignalDirection.LONG/SHORT/NEUTRAL,
    confidence=0-100,
    reasoning="...",
    sources=["Fear & Greed API", "Twitter API"]
)
```

## Источники данных

| Источник | Тип | Статус |
|---------|-----|--------|
| Fear & Greed Index | Бесплатный | ✅ |
| Twitter/X API | Требует ключ | ⚠️ |
| Reddit API | Бесплатный | ⚠️ |
| Binance Funding Rate | Бесплатный | ✅ |

## Метрики

| Метрика | Вес в сигнале |
|---------|--------------|
| Fear & Greed | 40% |
| Funding Rate | 30% |
| Price Momentum | 30% |

## Астрологический оверлей

- Moon → настроение толпы (20%)
- Venus → социальная гармония

## Backward reference

- Родитель: [[agents_index]]
- Использует: [[ephemeris_calculations]]
- Сигнал входит в: [[synthesis_agent]]

## Реализация

```python
class SentimentAgent(BaseAgent[AgentResponse]):
    weight = 0.10  # 10%
    domain = "sentiment"
```

- Файл: `agents/_impl/sentiment_agent.py`
- Stub: `agents/sentiment_agent.py` (re-export from `_impl`)
