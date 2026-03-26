# AstroFin Sentinel V5

**RAG-First Multi-Agent Trading Intelligence System**

Система принятия торговых решений, построенная по принципу «Внутренний Совет Директоров» — множество специализированных агентов голосуют, Synthesis Agent выводит финальную рекомендацию.

## Architecture

```
User Query → Router → [Parallel Specialist Flows] → Synthesis → Final Report
               │
    ┌────────────┼────────────┐
    ▼            ▼            ▼
Technical    Astro       Electional
  Team      Council        Agent
    │            │            │
    ▼            ▼            ▼
Confluence  Confluence  Best Windows
    └────────────┼────────────┘
                 ▼
          Synthesis Agent
                 │
                 ▼
         Final Recommendation
```

## Quick Start

```bash
cd /home/workspace/AstroFinSentinelV5
pip install -r requirements.txt
python -m orchestration.sentinel_v5 "Analyze BTC for swing trade" BTCUSDT SWING
```

## Project Structure

```
AstroFinSentinelV5/
├── agents/                    # Agent implementations
│   ├── base_agent.py          # BaseAgent, AgentResponse, SignalDirection
│   ├── synthesis_agent.py     # SynthesisAgent (coordinator)
│   ├── astro_council_agent.py # AstroCouncil coordinator
│   ├── electoral_agent.py     # Muhurta / entry timing
│   ├── fundamental_agent.py   # Fundamental analysis (20%)
│   ├── macro_agent.py         # Macro economics (15%)
│   ├── quant_agent.py         # ML / backtest / volatility (20%)
│   ├── options_flow_agent.py  # Options flow (15%)
│   ├── sentiment_agent.py     # News / social sentiment (10%)
│   ├── technical_agent.py     # RSI, MACD, Bollinger (10%)
│   ├── market_analyst.py      # Market structure
│   ├── bull_researcher.py     # Bullish narrative (5%)
│   ├── bear_researcher.py     # Bearish narrative (5%)
│   └── directional_agents.py  # Direction helpers
├── core/                      # Core engine modules
│   ├── ephemeris.py           # Swiss Ephemeris wrapper (PlanetPosition, NatalChart)
│   ├── aspects.py             # Aspects engine (conjunction, square, trine, etc.)
│   ├── history_db.py          # SQLite session persistence
│   ├── volatility.py          # Volatility regime engine (dynamic risk)
│   └── checkpoint.py          # State checkpointing
├── backtest/
│   ├── engine.py              # Backtest engine
│   ├── metrics_agent.py       # Metrics DB (BacktestRun, MetricsSummary)
│   └── test_metrics_agent.py  # Tests (10/10 passing)
├── orchestration/
│   ├── sentinel_v5.py         # CLI entry point
│   └── router.py              # Query router
├── knowledge/
│   └── rag_retriever.py       # RAG retrieval (Nakshatras, Choghadiya, etc.)
├── astrology/
│   └── vedic.py               # Vedic astrology utilities
├── langgraph_schema.py         # LangGraph orchestration graph
├── config/
│   └── agent_weights.yaml      # Agent weight configuration
└── tests/
    └── test_orchestrator.py    # Orchestrator tests
```

## Agent Board

| Agent | Weight | Domain |
|-------|--------|--------|
| MarketAnalyst | 25% | Technical (RSI, MACD, Bollinger) |
| AstroCouncil | 20% | Western + Vedic + Financial astrology |
| BullResearcher | 15% | Bullish fundamental case |
| BearResearcher | 15% | Bearish fundamental case |
| ElectoralAgent | 10% | Muhurta / entry timing |
| CycleAgent | 5% | Market cycles |
| RiskAgent | 5% | Position sizing |

## Core Modules

### `core/ephemeris.py`
Позиции планет, дома, натальная карта. Использует Swiss Ephemeris (pyswisseph) с fallback на упрощённый расчёт.

```python
from core.ephemeris import get_planetary_positions, PlanetPosition

positions = get_planetary_positions(datetime(2026, 3, 26))
print(positions["jupiter"].longitude)  # → degrees
```

### `core/aspects.py`
Расчёт аспектов между планетами (соединение, секстиль, квадрат, трин, оппозиция). Работает с выходом `core/ephemeris.py`.

```python
from core.ephemeris import get_planetary_positions
from core.aspects import calculate_aspects

positions = get_planetary_positions(datetime(2026, 3, 26))
report = calculate_aspects(positions)
for a in report.aspects:
    print(a.signature, f"({a.orb}°)")
```

### `core/history_db.py`
SQLite-персистенция сессий.

```python
from core.history_db import save_session, list_sessions, session_stats

sessions = list_sessions(symbol='BTCUSDT', limit=10)
stats = session_stats(symbol='BTCUSDT', days=30)
```

### `core/volatility.py`
Динамический риск на основе ATR и режима волатильности (LOW / NORMAL / HIGH / EXTREME).

## RAG Knowledge System

Each agent accesses knowledge through `retrieve_knowledge(query, domain)`:

- `domain="astrology"` — Nakshatras, Choghadiya, Muhurta, Western dignities
- `domain="technical"` — Indicators, patterns, wave theory
- `domain="trading"` — Risk management, position sizing

## Dependencies

```
langgraph>=0.0.55
langchain-core
langchain-openai
requests
swissEphemeris (sweph)
```
