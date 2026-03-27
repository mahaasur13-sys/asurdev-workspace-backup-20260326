---
type:: agent
id:: quant_agent
tags:: [agent, quantitative, backtesting, ml, _impl, weighted]
aliases:: [QuantAgent, квант-агент, количественный-агент]
created:: 2026-03-27
updated:: 2026-03-27
weight:: 0.10
domain:: quant
related:: [[synthesis_agent]], [[technical_agent]], [[volatility_engine]]

---

# Quant Agent

## Краткое описание

Агент количественного анализа и бэктестирования. Выполняет momentum-анализ, mean reversion, детекцию волатильности и корреляционный анализ.

**Вес в гибридном сигнале:** 10% (часть 20%-го quant-блока)

Астрологический бонус: ~20% (ephemeris-based)

## Расположение в коде

`agents/_impl/quant_agent.py` — каноническая версия
`agents/quant_agent.py` — stub (backward compatibility)

## Структура класса

```python
class QuantAgent(BaseAgent[AgentResponse]):
    weight: 0.10
    domain: "quant"

    async def analyze(state: dict) -> AgentResponse
    async def run(state: dict) -> AgentResponse

    async def _fetch_price_history(symbol, timeframe) -> list
    def _momentum_analysis(data: list) -> dict
    def _mean_reversion_analysis(data, price) -> dict
    def _volatility_regime(data: list) -> dict
    def _correlation_check(symbol: str) -> str
```

## Входные данные

| Источник | Данные |
|---------|--------|
| Binance API | OHLCV данные (100 свечей) |
| State | `symbol`, `timeframe_requested`, `current_price` |

**Интервалы:** `1H`, `4H`, `1D`, `1W`, `SWING` → `1h`, `4h`, `1d`, `1w`

## Выходные данные

```python
AgentResponse(
    agent_name="QuantAgent",
    signal=SignalDirection,  # LONG / SHORT / NEUTRAL
    confidence=int,
    reasoning="Momentum: {summary}. MeanRev: {signal} ({z}σ). ...",
    sources=["quant/momentum.md", "quant/mean_reversion.md"],
    metadata={
        "momentum": {"score", "summary", "mom_20"},
        "mean_reversion": {"signal", "z_score", "score"},
        "volatility_regime": {"regime", "vol_pct", "score"},
        "correlation": str
    }
)
```

## Алгоритмы

### 1. Momentum Analysis

```
mom_20 = (close[-1] - close[-20]) / close[-20]   # % change over 20 candles
mom_10 = (close[-1] - close[-10]) / close[-10]

mom_score = 0.5 + mom_20 × 2   # normalize to 0-1

mom_score > 0.70 → "Strong momentum +X%"
mom_score > 0.55 → "Weak momentum +X%"
mom_score > 0.45 → "Neutral momentum X%"
mom_score > 0.30 → "Weak bearish X%"
else             → "Strong bearish X%"
```

### 2. Mean Reversion (Z-Score)

```
mean = SMA(closes[-20:])
std  = StdDev(closes[-20:])
z    = (price - mean) / std

z < -2  → signal="oversold", score=0.70  🟢
-2 ≤ z < -1 → signal="bullish", score=0.60 🟢
 1 ≤ z < 2  → signal="bearish", score=0.60 🟠
 z ≥ 2      → signal="overbought", score=0.70 🔴
|z| < 1     → signal="neutral", score=0.50 🟡
```

### 3. Volatility Regime Detection

```
vol_10 = σ(returns[-10:]) × √365   # annualized
vol_30 = σ(returns[-30:]) × √365   # annualized

vol_10 > vol_30 × 1.5 → regime="high_vol_expanding", score=0.40 🔴
vol_10 < vol_30 × 0.7 → regime="low_vol_contr", score=0.60 🟢
иначе                 → regime="normal", score=0.50 🟡
```

### 4. Correlation Check

```
BTC/USD correlation with SPX: moderate positive  # placeholder
# TODO: real SPX, gold, DXY correlations
```

## Агрегирование

```
Momentum score > 0.55 → LONG vote, score = momentum_score
Momentum score < 0.45 → SHORT vote, score = 1 - momentum_score

MeanRev oversold → LONG vote, score=0.65
MeanRev overbought → SHORT vote, score=0.65

LONG votes > SHORT votes → LONG
SHORT votes > LONG votes → SHORT
```

## Взаимодействия

- **Использует:** `core.base_agent.BaseAgent`, `@require_ephemeris`, `numpy`
- **Вызывается:** `synthesis_agent` (категория `quant`)
- **Данные:** Binance OHLCV → OHLCV через `requests`

## Астрологический фактор

`@require_ephemeris` декоратор → ~20% бонус на основе ephemeris.

## Пример использования

```python
from agents._impl.quant_agent import run_quant_agent

state = {
    "symbol": "BTCUSDT",
    "timeframe_requested": "SWING",
    "current_price": 67000
}
result = await run_quant_agent(state)
# result = {"quant_signal": {...}}
```

## Known issues

- Correlation check — placeholder (no real SPX/DXY/Gold correlation)
- Binance rate limits on free tier
- Mean reversion z-score uses 20-bar window (not adaptive)

## TODO

- [ ] Real correlation with SPX, gold, DXY (Yahoo Finance)
- [ ] Adaptive window for mean reversion
- [ ] Add Bollinger Band width analysis
- [ ] Add ATR-based volatility (not just stddev)

## См. также

- [[volatility_engine]] — движок волатильности
- [[technical_agent]] — технический анализ
- [[synthesis_agent]] — финальный синтез
- [[backtest_metrics]] — бэктестирование
