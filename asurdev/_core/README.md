# asurdev Sentinel Core v2.1 - Refactored

## Структура

```
_core/
├── types.py      # AgentResult, SignalType, TradingSignal
├── agents.py     # All analysis agents (250 lines)
├── api.py        # FastAPI endpoints
└── __init__.py   # Public API
```

## Агенты

| Агент | Функция | Сигнал |
|-------|---------|--------|
| `analyze_market` | RSI, MA, тренды | Технический |
| `analyze_dow` | Dow Theory | HH/HL паттерны |
| `analyze_andrews` | Median Line | Andrews Pitchfork |
| `analyze_smc` | Order Blocks, FVG | Институциональный |
| `analyze_gann` | Square of 9 | Ганн |
| `analyze_monte_carlo` | Симуляция | Вероятностный |
| `analyze_astrology` | Moon phases | Астрологический |
| `synthesize_signals` | Объединение | Финальный |

## Использование

```python
from _core import (
    analyze_market, analyze_dow, analyze_smc,
    analyze_gann, analyze_monte_carlo, synthesize_signals
)

# Данные
prices = [100, 102, 101, 105, 107, 106, 108, 110]

# Анализ
results = [
    analyze_market(prices, "BTC"),
    analyze_dow(prices, "BTC"),
    analyze_smc(prices, "BTC"),
]

# Финальный сигнал
final = synthesize_signals(results, "BTC")
print(final.signal, final.confidence, final.summary)
```

## API Endpoints

- `GET /` - Status
- `GET /agents` - List agents
- `POST /analyze` - Full analysis

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"symbol": "BTC", "price": 50000, "prices": [48000, 49000, 50000]}'
```
