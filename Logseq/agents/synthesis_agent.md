---
type:: agent
id:: synthesis_agent
tags:: [agent, coordinator, synthesis, orchestrator, _impl, 100-pct]
aliases:: [SynthesisAgent, синтез-агент, координатор]
created:: 2026-03-27
updated:: 2026-03-27
weight:: 1.0
domain:: synthesis
related:: [[fundamental_agent]], [[macro_agent]], [[quant_agent]], [[technical_agent]], [[sentinel_v5_workflow]], [[volatility_engine]]

---

# Synthesis Agent

## Краткое описание

**Координатор финального синтеза.** Получает сигналы от ВСЕХ аналитических агентов, применяет гибридное взвешивание по категориям, разрешает конфликты и формирует финальный торговый сигнал с уровнями входа/стопа.

**Вес в гибридном сигнале:** 100% (координатор, не голосует напрямую)

## Расположение в коде

`agents/_impl/synthesis_agent.py` — каноническая версия
`agents/synthesis_agent.py` — stub (backward compatibility)

## Структура класса

```python
class SynthesisAgent(BaseAgent[AgentResponse]):

    async def run(state: dict) -> AgentResponse

    # Internal
    def _group_by_category(signals: list) -> Dict[str, list]
    def _detect_conflicts(categories) -> list
    def _synthesize(categories, conflicts, symbol) -> tuple
    def _vote(categories, eff_weights) -> tuple
    def _apply_guards(direction, confidence) -> tuple
    def _format_breakdown(categories) -> str
    def _collect_sources(signals) -> list
    def _calculate_levels(direction, price, risk_pct) -> dict
    def _get_signal_attr(sig, key, default=None)
```

## Конфигурация

Weights загружаются из `config/agent_weights.yaml`. Fallback — константы в коде.

```python
CATEGORY_WEIGHTS = {
    "astro":       0.22,
    "fundamental": 0.15,
    "macro":       0.15,
    "quant":       0.18,
    "options":     0.12,
    "sentiment":   0.09,
    "technical":   0.09,
}

AGENT_WEIGHTS = {
    "FundamentalAgent":   0.20,
    "QuantAgent":         0.20,
    "MacroAgent":         0.15,
    "OptionsFlowAgent":   0.15,
    "SentimentAgent":     0.10,
    "TechnicalAgent":     0.10,
    "BullResearcher":     0.05,
    "BearResearcher":     0.05,
}

# Guards
MAX_CONFIDENCE  = 92
MIN_CONFIDENCE  = 30
VOLATILITY_DROP = 15

# Conflict resolution
ASTRO_REDUCTION   = 0.30   # если Astro конфликтует с Fund+Quant
FUNDAMENTAL_BOOST = 0.18
QUANT_BOOST       = 0.12
```

## Алгоритм синтеза

```
┌─────────────────────────────────────────────────┐
│  1. GROUP  → категории (astro, fundamental...)  │
│  2. CONFLICT DETECT  → astro vs fund+quant?   │
│  3. WEIGHT ADJUST  → снижаем astro на 30%      │
│  4. VOTE  → LONG/SHORT/NEUTRAL по весам        │
│  5. GUARD  → EC-01 cap + V-06 volatility drop  │
│  6. LEVELS  → entry, stop, targets (R-07)      │
└─────────────────────────────────────────────────┘
```

## Конфликт: Astro vs Fundamental+Quant

```
Если Astro направление ≠ Neutral И ≠ направлению Fundamental/Quant:
  → Astro weight × (1 - 0.30) = 0.70 от текущего
  → Fundamental weight × (1 + 0.18)
  → Quant weight × (1 + 0.12)
```

## V-07: EXTREME Volatility

Если `regime == VolatilityRegime.EXTREME`:
```
direction = AVOID
confidence = max(30, confidence - 25)
reasoning = "V-07 [EXTREME VOLATILITY] — trade blocked"
```

## V-06: Volatility Confidence Drop

Из `VolatilityEngine`:
```
HIGH regime  → confidence -= 10
EXTREME regime → confidence -= 25
```

## EC-01: Hubris Cap

```
MAX_CONFIDENCE = 92
confidence = min(confidence, 92)
if confidence < MIN_CONFIDENCE (30) → нейтрализуем в NEUTRAL
```

## Fallback

Если `< MIN_AGENTS_FALLBACK (2)` агентов дали сигналы:
```
signal = NEUTRAL
confidence = 30
reasoning = "Fallback: only X signals (min: 2)"
```

## Категории агентов

| Категория | Агенты |
|-----------|---------|
| `astro` | AstroCouncil, ElectoralAgent, BradleyAgent, TimeWindowAgent, GannAgent, ElliotAgent, CycleAgent |
| `fundamental` | FundamentalAgent, InsiderAgent |
| `macro` | MacroAgent |
| `quant` | QuantAgent, MLPredictorAgent |
| `options` | OptionsFlowAgent |
| `sentiment` | BullResearcher, BearResearcher, SentimentAgent |
| `technical` | TechnicalAgent, MarketAnalyst |

## Расчёт уровней (R-07)

```python
rr_ratio  = 2.5
stop_dist  = risk_pct × 1.5
tp_dist    = risk_pct × 2.5

LONG:  entry = price ± risk_pct×0.5
       stop  = price × (1 - stop_dist)
       T1    = price × (1 + tp_dist × 1)
       T2    = price × (1 + tp_dist × 2)
       T3    = price × (1 + tp_dist × 3)
       position = risk_pct / 2
```

## Выходные данные

```python
AgentResponse(
    agent_name="SynthesisAgent",
    signal=SignalDirection,  # LONG / SHORT / NEUTRAL / AVOID
    confidence=int,
    reasoning="<vote summary + guards>",
    sources=[...],
    metadata={
        "symbol": str,
        "timeframe": str,
        "current_price": float,
        "breakdown": str,           # форматированная таблица
        "conflicts": list,
        "agent_weights": dict,
        "thompson_selections": dict,
        "entry_zone": (float, float),
        "stop_loss": float,
        "targets": [float, float, float],
        "position_size": float,
        "risk_pct_used": float,
        "volatility_risk": {
            "regime": str,
            "atr_pct": float,
            "risk_pct": float,
            "position_size": float,
            "stop_distance_pct": float,
            "confidence_drop": int,
            "kelly_raw": float,
            "kelly_adjusted": float,
        }
    }
)
```

## Breakdown-формат

```
[ASTRO       ] LONG ▲       [████████░░]  72.0% w=0.22 (ElectoralAgent, BradleyAgent)
[FUNDAMENTAL ] LONG ▲       [████████░░]  68.0% w=0.15 (FundamentalAgent)
[MACRO       ] NEUTRAL     [░░░░░░░░░░]   0.0% w=0.15 (no signals)
[QUANT       ] LONG ▲       [███████░░░]  65.0% w=0.18 (QuantAgent)
[OPTIONS     ] NEUTRAL     [░░░░░░░░░░]   0.0% w=0.12 (no signals)
[SENTIMENT   ] SHORT ▼     [██████░░░░]  58.0% w=0.09 (BearResearcher)
[TECHNICAL   ] LONG ▲       [████████░░]  70.0% w=0.09 (Technical)
```

## Взаимодействия

- **Использует:** `core.base_agent`, `core.volatility`, `config/agent_weights.yaml`
- **Вызывается:** `orchestration/sentinel_v5.py` (финальный этап)
- **Результат:** финальный `AgentResponse` → пользователю

## Known issues

- All data sources (VIX, DXY, Gold, Fear&Greed) are placeholders
- Thompson Sampling selections stored in `thompson_selections`
- Config validation raises `ValueError` if weights don't sum to 1.0

## Пример использования

```python
from agents._impl.synthesis_agent import run_synthesis_agent

state = {
    "all_signals": [fundamental_resp, quant_resp, macro_resp],
    "thompson_selections": {"technical": ["MarketAnalyst"], "astro": [...], "electoral": ["ElectoralAgent"]},
    "symbol": "BTCUSDT",
    "current_price": 67000,
    "timeframe_requested": "SWING"
}
result = await run_synthesis_agent(state)
# result = {"synthesis_signal": {...}}
```

## Cm. также

- [[sentinel_v5_workflow]] — торговый цикл
- [[volatility_engine]] — движок риска
- [[thompson_sampling]] — Thompson Sampling
- [[synthetic_signals_moc]] — карта агентов
