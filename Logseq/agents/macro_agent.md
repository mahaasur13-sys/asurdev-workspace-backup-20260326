---
type:: agent
id:: macro_agent
tags:: [agent, macro, geopolitical, _impl, weighted]
aliases:: [MacroAgent, макро-агент]
created:: 2026-03-27
updated:: 2026-03-27
weight:: 0.08
domain:: macro
related:: [[fundamental_agent]], [[quant_agent]], [[synthesis_agent]]

---

# Macro Agent

## Краткое описание

Агент макроэкономического анализа. Мониторит индикаторы риск-аппетита: VIX, DXY, золото, Fear & Greed Index, ставку ФРС.

**Вес в гибридном сигнале:** 8% (часть 15%-го макро-блока)

Астрологический бонус: ~20% (Saturn, Jupiter)

## Расположение в коде

`agents/_impl/macro_agent.py` — каноническая версия
`agents/macro_agent.py` — stub (backward compatibility)

## Структура класса

```python
class MacroAgent(BaseAgent[AgentResponse]):
    weight: 0.08
    domain: "macro"

    async def analyze(state: dict) -> AgentResponse
    async def run(state: dict) -> AgentResponse

    # Fetchers
    async def _fetch_vix() -> float
    async def _fetch_dxy() -> float
    async def _fetch_gold() -> float
    async def _fetch_fear_greed() -> str
    async def _fetch_fed_rate() -> float

    # Analyzers
    def _analyze_vix(vix: float) -> tuple[SignalDirection, float, str]
    def _analyze_dxy(dxy: float) -> tuple[SignalDirection, float, str]
    def _analyze_gold(gold: float, btc_price: float) -> tuple
    def _analyze_fear_greed(fg: str) -> tuple
    def _analyze_fed_rate(rate: float) -> tuple
```

## Входные данные

| Источник | Данные | Статус |
|---------|--------|--------|
| CBOE / Proxy | VIX | ⚠️ Placeholder (использует BTC volatility) |
| Yahoo Finance | DXY (Dollar Index) | ⚠️ Placeholder (104.0) |
| Yahoo Finance | Gold price | ⚠️ Placeholder (2300) |
| Alternative API | Fear & Greed Index | ⚠️ Placeholder ("Neutral") |
| Public data | Fed Rate | ✅ Approximate (5.25%) |
| State | `current_price` | от оркестратора |

## Индикаторы и сигналы

### VIX

| Значение | Сигнал | Score | Описание |
|---------|--------|-------|---------|
| VIX < 15 | LONG | 0.70 | Low volatility = risk-on |
| 15 ≤ VIX < 25 | NEUTRAL | 0.55 | Normal market |
| 25 ≤ VIX < 35 | SHORT | 0.60 | Elevated VIX = caution |
| VIX ≥ 35 | AVOID | 0.75 | High fear |

### DXY (US Dollar Index)

| Значение | Сигнал | Score | Описание |
|---------|--------|-------|---------|
| DXY < 100 | LONG | 0.60 | Weak USD = bullish crypto |
| 100 ≤ DXY < 106 | NEUTRAL | 0.50 | Neutral |
| DXY ≥ 106 | SHORT | 0.60 | Strong USD = headwind |

### Gold / BTC

| Соотношение | Сигнал | Score | Описание |
|-------------|--------|-------|---------|
| Gold/BTC < 0.05 | LONG | 0.60 | Risk-on environment |
| Gold/BTC > 0.10 | NEUTRAL | 0.50 | Gold as inflation hedge |
| иначе | NEUTRAL | 0.50 | Neutral |

### Fear & Greed Index

| Значение | Сигнал | Score |
|---------|--------|-------|
| Extreme Fear | LONG | 0.70 |
| Fear | LONG | 0.60 |
| Neutral | NEUTRAL | 0.50 |
| Greed | SHORT | 0.60 |
| Extreme Greed | AVOID | 0.70 |

### Fed Rate

| Ставка | Сигнал | Score |
|--------|--------|-------|
| Rate > 5.0% | SHORT | 0.65 |
| 3.0% < Rate ≤ 5.0% | NEUTRAL | 0.50 |
| Rate ≤ 3.0% | LONG | 0.60 |

## Агрегирование

```
LONG votes > SHORT votes → LONG
SHORT votes > LONG votes → SHORT
равенство → NEUTRAL

confidence = sum(scores) / len(scores) × 100
```

## Выходные данные

```python
AgentResponse(
    agent_name="MacroAgent",
    signal=SignalDirection,  # LONG / SHORT / NEUTRAL / AVOID
    confidence=int,
    reasoning="VIX: {summary} | DXY: {summary} | Gold: {summary} | F&G: {fg} | Fed: {rate}%",
    sources=["macro/vix.md", "macro/fed_rates.md", "macro/dxy.md"],
    metadata={
        "vix": float,
        "dxy": float,
        "gold": float,
        "fear_greed": str,
        "fed_rate": float,
        "signals": {
            "vix": str, "dxy": str, "gold": str,
            "fear_greed": str, "fed_rate": str
        }
    }
)
```

## Взаимодействия

- **Использует:** `core.base_agent.BaseAgent`, `@require_ephemeris`
- **Вызывается:** `synthesis_agent` (категория `macro`)
- **Конфликты:** VIX > 35 → AVOID перекрывает другие LONG-сигналы

## Астрологический фактор

`@require_ephemeris` → Saturn (структура/риск) + Jupiter (экспансия) дают ±20% к базовому скору.

## Пример использования

```python
from agents._impl.macro_agent import run_macro_agent

state = {"current_price": 67000}
result = await run_macro_agent(state)
# result = {"macro_signal": {...}}
```

## Known issues

⚠️ Все данные (VIX, DXY, Gold, Fear&Greed) — placeholder-значения через CoinGecko free API. Для продакшена нужны реальные API: CBOE VIX, Yahoo Finance, alternative.me Fear&Greed.

## См. также

- [[fundamental_agent]] — фундаментальный анализ
- [[quant_agent]] — количественный анализ
- [[synthesis_agent]] — финальный синтез
- [[volatility_engine]] — расчёт волатильности
