---
type:: agent
id:: fundamental_agent
tags:: [agent, fundamental-analysis, _impl, weighted]
aliases:: [FundamentalAgent, фундаментальный-агент]
created:: 2026-03-27
updated:: 2026-03-27
weight:: 0.12
domain:: fundamental
related:: [[macro_agent]], [[quant_agent]], [[synthesis_agent]], [[sentiment_agent]]

---

# Fundamental Agent

## Краткое описание

Агент фундаментального анализа. Оценивает финансовые показатели компании/актива через DCF-модели, мультипликаторы (P/E, MVRV), качество прибыли и метрики роста.

**Вес в гибридном сигнале:** 12% (часть 20%-го фундаментального блока)

Астрологический бонус: ~30% (Jupiter, Venus)

## Расположение в коде

`agents/_impl/fundamental_agent.py` — каноническая версия
`agents/fundamental_agent.py` — stub (backward compatibility)

## Структура класса

```python
class FundamentalAgent(BaseAgent[AgentResponse]):
    weight: 0.12
    domain: "fundamental"

    async def analyze(state: dict) -> AgentResponse
    async def run(state: dict) -> AgentResponse

    # Internal
    async def _fetch_crypto_metadata(symbol: str) -> dict
    async def _fetch_onchain_data(symbol: str) -> dict
    def _analyze_valuation(metadata, onchain, price) -> dict
    def _analyze_earnings_quality(metadata, onchain) -> dict
    def _analyze_growth_metrics(onchain) -> dict
```

## Входные данные

| Источник | Данные | Метод |
|---------|--------|-------|
| CoinGecko API | name, market_cap_rank, volume_24h, ATH/ATL | `GET /coins/{id}` |
| CoinGecko API | 30-дневный price history → MVRV | `GET /coins/{id}/market_chart` |
| State | `symbol`, `current_price` | от оркестратора |

## Выходные данные

`AgentResponse` с полями:

```python
signal:     SignalDirection  # LONG / SHORT / NEUTRAL
confidence: int             # 0-100
reasoning:  str             # сводка по всем метрикам
metadata: {
    "valuation":  {"score", "summary"},   # MVRV analysis
    "earnings":  {"score", "summary"},   # market cap tier
    "growth":    {"score", "summary"},   # volatility-based
    "onchain":   {"mvrv_ratio", "ath_distance_pct", "volatility_30d"}
}
sources: ["fundamental/valuation.md", "fundamental/earnings.md"]
```

## Алгоритм анализа

### 1. Valuation (MVRV)

```
MVRV = current_price / average_price_30d

MVRV < 0.7  → score = 0.75 (deep value)      🟢
MVRV < 1.0  → score = 0.65 (below average)   🟢
MVRV < 2.0  → score = 0.55 (fair value)      🟡
MVRV < 3.5  → score = 0.40 (overvalued)      🟠
MVRV ≥ 3.5  → score = 0.25 (bubble zone)      🔴

ATH distance bonus: >70% от ATH → score × 1.1
Near ATH (<10%) → score × 0.9
```

### 2. Earnings Quality

```
market_cap_rank < 10  → score = 0.65 (Top-10, stable)
market_cap_rank < 50  → score = 0.60 (Large cap)
market_cap_rank < 100 → score = 0.55 (Mid cap)
market_cap_rank ≥ 100 → score = 0.45 (Small cap)

+ volatility adjustment (price_change_24h)
```

### 3. Growth Metrics

```
volatility_30d < 5%  → score = 0.60 (low, stable growth)
volatility_30d < 15% → score = 0.55 (normal)
volatility_30d < 30% → score = 0.45 (high)
volatility_30d ≥ 30% → score = 0.35 (extreme)
```

## Агрегирование

```
LONG votes > SHORT votes → direction = LONG
SHORT votes > LONG votes → direction = SHORT
равенство → NEUTRAL

confidence = sum(scores) / len(scores) × 100
```

## Взаимодействия

- **Использует:** `core.base_agent.BaseAgent`, `core.ephemeris` (через `@require_ephemeris`)
- **Вызывается:** `synthesis_agent` (категория `fundamental`)
- **Результат:** `AgentResponse` → `all_signals` → `SynthesisAgent._group_by_category()`

## Астрологический фактор

`@require_ephemeris` декоратор добавляет астрологический бонус (~30%) от Jupiter и Venus.

## Пример использования

```python
from agents._impl.fundamental_agent import run_fundamental_agent

state = {"symbol": "BTCUSDT", "current_price": 67000}
result = await run_fundamental_agent(state)
# result = {
#     "fundamental_signal": {
#         "agent_name": "FundamentalAgent",
#         "signal": "LONG",
#         "confidence": 65,
#         "reasoning": "MVRV 0.72 (deep value)...",
#         "metadata": {...}
#     }
# }
```

## Known issues

- CoinGecko free tier rate limits apply (10-50 req/min)
- MVRV approximation uses simple 30d average (not realized cap)
- Fallback to default values on API failure

## См. также

- [[quant_agent]] — количественный анализ
- [[macro_agent]] — макроэкономика
- [[synthesis_agent]] — финальный синтез
- [[sentinel_v5_workflow]] — торговый цикл
