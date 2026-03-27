---
type:: agent
id:: technical_agent
tags:: [agent, technical-analysis, rsi, macd, bollinger, _impl]
aliases:: [TechnicalAgent, технический-агент]
created:: 2026-03-27
updated:: 2026-03-27
weight:: 0.10
domain:: technical
related:: [[synthesis_agent]], [[quant_agent]], [[market_analyst]]

---

# Technical Agent

## Краткое описание

Агент технического анализа. Вычисляет RSI(14), MACD(12,26,9), Bollinger Bands, Volume Profile. Используется как **фильтр** в гибридном сигнале.

**Вес в гибридном сигнале:** 10%

**Гибридный скоринг:** 85% технический + 15% астрологический бонус

Астрологический бонус: ~15% (Mars, Moon)

## Расположение в коде

`agents/_impl/technical_agent.py` — каноническая версия
`agents/technical_agent.py` — stub (backward compatibility)

## Структура класса

```python
class TechnicalAgent(BaseAgent):
    async def run(state: Dict) -> AgentResponse

    def _call_ephemeris(dt) -> Dict
    async def _fetch_ohlcv(symbol, interval, limit) -> list
    def _calculate_indicators(data, price) -> Dict
    def _ema(values, period) -> float
    def _calculate_technical_score(indicators, eph) -> float
    def _get_astro_influence(eph) -> str
    def _build_reasoning(ind, score) -> str
```

## Входные данные

| Источник | Данные | Метод |
|---------|--------|-------|
| Binance API | OHLCV (50 свечей, 1D) | `GET /api/v3/klines` |
| Swiss Ephemeris | Позиции Mars, Moon, Venus | `core.ephemeris` |
| State | `symbol`, `current_price`, `datetime` | от оркестратора |

## Индикаторы

### RSI(14)

```
RSI < 30  → score += 20  # oversold = bullish 🟢
RSI < 40  → score += 10  # 🟢
RSI > 70  → score -= 20  # overbought = bearish 🔴
RSI > 60  → score -= 10  # 🔴
```

### MACD (12, 26, 9)

```
EMA(12) - EMA(26) = MACD line
Signal = EMA(MACD, 9)

MACD histogram > 0 → score += 15  # 🟢
MACD histogram < 0 → score -= 15  # 🔴
```

### Bollinger Bands (20, 2)

```
BB position = (price - lower) / (upper - lower)

position < 0.2 → score += 15  # near lower band = oversold 🟢
position < 0.4 → score += 5   # 🟢
position > 0.8 → score += 15  # near upper band = overbought warning 🟠
position > 0.6 → score -= 5   # 🟠
```

### Volume Profile

```
recent_vol = avg(vol[-5:])
older_vol  = avg(vol[-20:-5])

recent > older × 1.3 → "increasing (bullish)" → score += 5
recent < older × 0.7 → "decreasing (bearish)" → score -= 5
```

## Гибридный скоринг

```
score = 50.0
+ RSI component
+ MACD component
+ Bollinger component
+ Volume component

astro_bonus = (astro_score - 50) × 0.30

final_score = max(0, min(100, score + astro_bonus))
```

## Выходные данные

```python
AgentResponse(
    agent_name="Technical",
    signal=SignalDirection,  # STRONG_BUY / BUY / NEUTRAL / SELL / STRONG_SELL
    confidence=int,
    reasoning="RSI(14)=X (label), MACD=bullish, BB: middle, Vol: stable, Tech score=X/100",
    sources=["Binance API", "Technical analysis"],
    metadata={
        "technical_score": float,
        "rsi": float,
        "macd": {"histogram": float, "signal": float},
        "bollinger": {"upper", "lower", "middle", "position"},
        "volume_trend": str,
        "astro_influence": "Yoga: {yoga}, score: {score}",
        "source": "binance + astrological_bonus"
    }
)
```

## Астрологический компонент

```python
# Mars-Moon aspects
mars_moon = |mars - moon| % 360
mars_moon < 30 or > 330 → score += 10  # trine = momentum 🟢
85 < mars_moon < 95     → score -= 10  # square = volatility 🔴

# Venus-Moon aspects
ven_moon < 30 or > 330 → score += 5   # trine = stability 🟢
```

## Сигнал и уверенность

| Score | Сигнал |
|-------|--------|
| ≥ 80 | STRONG_BUY |
| 65–79 | BUY |
| 50–64 | NEUTRAL |
| 35–49 | SELL |
| < 35 | STRONG_SELL |

```
confidence = min(88, int(score))
```

## Взаимодействия

- **Использует:** `core.base_agent.BaseAgent`, `core.ephemeris`, `requests`
- **Вызывается:** `synthesis_agent` (категория `technical`)
- **Данные:** Binance OHLCV 1D interval

## Пример использования

```python
from agents._impl.technical_agent import run_technical_agent

state = {"symbol": "BTCUSDT", "current_price": 67000}
result = await run_technical_agent(state)
# result = {"technical_signal": {...}}
```

## Known issues

- Swiss Ephemeris license required for full `@require_ephemeris` functionality
- Binance free tier rate limits apply
- Fixed 1D interval (no multi-timeframe in single run)

## TODO

- [ ] Multi-timeframe analysis (1H, 4H, 1W)
- [ ] Support custom intervals from state
- [ ] Add VWAP, Ichimoku, ADX indicators

## См. также

- [[quant_agent]] — количественный анализ
- [[market_analyst]] — анализ рыночной структуры
- [[synthesis_agent]] — финальный синтез
- [[ephemeris_calculations]] — расчёт эфемерид
