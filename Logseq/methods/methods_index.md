---
type:: moc
id:: methods_index
tags:: [moc, methods, algorithms, index]
created:: 2026-03-27
updated:: 2026-03-27
---

# Methods Index

> Сводная страница всех методов и алгоритмов AstroFin Sentinel V5.

## Core Methods

| Метод | Файл | Описание |
|-------|------|---------|
| [[volatility_engine]] | `core/volatility.py` | ATR-based dynamic position sizing |
| [[thompson_sampling]] | `core/thompson.py` | Bayesian agent selection |
| [[belief_tracker]] | `core/belief.py` | Agent accuracy tracking |
| [[ephemeris_calculations]] | `core/ephemeris.py` | Swiss Ephemeris wrapper |
| [[aspects_calculations]] | `core/aspects.py` | Angular planetary aspects |

## Knowledge System

| Метод | Файл | Описание |
|-------|------|---------|
| [[rag_retriever]] | `knowledge/rag_retriever.py` | FAISS vector search |
| [[belief_index]] | `knowledge/belief_index.py` | RAG index for agent beliefs |

## Data Systems

| Метод | Файл | Описание |
|-------|------|---------|
| [[history_db]] | `core/history_db.py` | Session persistence (SQLite) |
| [[checkpoint]] | `core/checkpoint.py` | State checkpointing |
| [[metrics_agent]] | `backtest/metrics_agent.py` | Backtest metrics |

## Trading Logic

| Метод | Файл | Описание |
|-------|------|---------|
| [[synthesis_agent]] | `agents/_impl/synthesis_agent.py` | Signal aggregation + conflict resolution |
| [[risk_agent]] | `agents/_impl/risk_agent.py` | Dynamic risk management |
| [[options_flow_agent]] | `agents/_impl/options_flow_agent.py` | Options chain analysis |

## Astro Methods

| Метод | Домен | Файл |
|-------|-------|------|
| [[electoral_agent]] | Muhurta / Vedic electional | `agents/_impl/electoral_agent.py` |
| [[bradley_agent]] | S&P Bradley Model | `agents/_impl/bradley_agent.py` |
| [[gann_agent]] | Gann angles + squares | `agents/_impl/gann_agent.py` |
| [[cycle_agent]] | Market cycles + astro | `agents/_impl/cycle_agent.py` |
| [[time_window_agent]] | Multi-TF windows | `agents/_impl/time_window_agent.py` |
| [[elliot_agent]] | Elliot Wave | `agents/_impl/elliot_agent.py` |

## Architecture Map

```
┌─────────────────────────────────────────────────────────┐
│              METHODS & ALGORITHMS                        │
├──────────────┬──────────────┬──────────────────────────┤
│ Agent System │ Data System  │ Signal Processing        │
├──────────────┼──────────────┼──────────────────────────┤
│              │              │                          │
│ BeliefTrack  │ HistoryDB    │ SynthesisAgent            │
│     │        │     │        │     │                    │
│ ThompsonSmpl │ Checkpoint   │ VolatilityEngine         │
│     │        │     │        │     │                    │
│ RiskAgent    │ MetricsAgent │ AspectsEngine            │
│              │              │                          │
└──────────────┴──────────────┴──────────────────────────┘
```

## Key Formulas

### Kelly Criterion
```
Kelly = (W × (R) − (1−W)) / R
  W = win rate
  R = avg_win / avg_loss
```

### Beta Distribution
```
α = successes + 1
β = failures + 1
mean = α / (α + β)
```

### ATR Regime
```
ATR% < 1.5%  → LOW
1.5–3%      → NORMAL
3–5%        → HIGH
≥ 5%        → EXTREME
```

### Confidence Interval (Wilson)
```
p̂ = α / (α + β)
z = 1.96 (95%)
CI = (p̂ + z²/2 − z√(p̂(1−p̂) + z²/4)) / (1 + z²)
```

## Integration

```
sentinel_v5.py (orchestrator)
    │
    ├── ThompsonSampler.select() ──→ BeliefTracker.get()
    │
    ├── VolatilityEngine.analyze() ──→ risk_pct, stop_distance
    │
    ├── run_*_agent() calls
    │       │
    │       ├── core/ephemeris → planetary positions
    │       │         │
    │       │         └── core/aspects → angular aspects
    │       │
    │       └── knowledge/rag_retriever → context
    │
    ├── BeliefTracker.update_from_session()
    │
    └── SynthesisAgent.run() → final signal
```

## Rule Engine

| Rule | Module | Description |
|------|--------|-------------|
| V-06 | volatility_engine | Confidence drop in HIGH vol |
| V-07 | volatility_engine | AVOID signal in EXTREME |
| EC-01 | synthesis_agent | Hubris cap (≤90%) |
| Conflict-01 | synthesis_agent | Astro vs Funda+Quant weighting |

## See Also

- [[agents_index]] — карта агентов
- [[concepts_index]] — концепции
- [[synthetic_signals_moc]] — альтернативная карта
