# AstroFin Sentinel V5 — Project Specification

**Version:** 5.0.0-production  
**Status:** ✅ PRODUCTION READY  
**Last Updated:** 2026-03-29

---

## Executive Summary

AstroFin Sentinel V5 is a **multi-agent trading system** combining:
- **14 specialized agents** (Fundamental, Quant, Macro, Technical, Astro, etc.)
- **Thompson Sampling** for agent selection
- **KARL self-improvement loop** (AMRE framework)
- **MAS Factory architecture** for dynamic agent orchestration

**Core Value:** Generates BUY/SELL/HOLD signals with confidence scores for crypto markets.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     ASTROFIN SENTINEL V5                        │
├─────────────────────────────────────────────────────────────────┤
│  User Query → Router → MASFactory → Synthesis → Signal Output │
│                         ↓                                        │
│  ┌─────────┐ ┌───────────┐ ┌─────────────┐ ┌──────────────┐ │
│  │Technical│ │   Astro   │ │   Macro     │ │  Fundamental │ │
│  │  Pool   │ │  Council  │ │   Flow      │ │    Flow      │ │
│  │(3 ags) │ │  (5 ags)  │ │  (4 agents) │ │  (3 agents)  │ │
│  └─────────┘ └───────────┘ └─────────────┘ └──────────────┘ │
│                         ↓                                        │
│           KARL AMRE Loop (Meta-Questioning, OAP)               │
│                         ↓                                        │
│                    FINAL SIGNAL                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Agent Registry

### Thompson Pools

| Pool | Agents | Selection |
|------|--------|-----------|
| **TECHNICAL** | MarketAnalyst, BullResearcher, BearResearcher | Top-K |
| **ASTRO** | BradleyAgent, GannAgent, CycleAgent, ElectoralAgent, TimeWindowAgent | Top-K |
| **ELECTORAL** | ElectoralAgent | Top-1 |

### Agent Weights

| Agent | Category | Base Weight |
|-------|----------|-------------|
| FundamentalAgent | fundamental | 20% |
| QuantAgent | quant | 20% |
| MacroAgent | macro | 15% |
| OptionsFlowAgent | options | 15% |
| SentimentAgent | sentiment | 10% |
| TechnicalAgent | technical | 10% |
| BullResearcher | sentiment | 5% |
| BearResearcher | sentiment | 5% |
| BradleyAgent | astro | 3% |
| GannAgent | astro | 3% |
| CycleAgent | astro | 5% |
| ElectoralAgent | astro | 3% |
| TimeWindowAgent | astro | 2% |

---

## KARL AMRE Framework

### Components

| Component | Purpose |
|----------|---------|
| **UncertaintyEngine** | Quantifies aleatoric + epistemic uncertainty |
| **GroundingEngine** | Validates signal-confidence consistency |
| **SelfQuestioningEngine** | Meta-questions for bias detection |
| **OAPOptimizer** | Position sizing + confidence calibration |
| **RewardCalibrator** | Maps confidence → probability |
| **ContinuousBacktest** | Regime-aware performance tracking |

### AMRE Flow

```
Signal → Uncertainty → Grounding → Self-Questioning → OAP → Decision Record
                              ↓
                    KARL Metrics (TTC, OOS Fail, Entropy)
```

---

## Data Flow

```
1. User Query (natural language)
   ↓
2. Router (classify: TECHNICAL, FUNDAMENTAL, NATURAL, etc.)
   ↓
3. Thompson Sampling (select agents per pool)
   ↓
4. MAS Factory (build topology, execute agents)
   ↓
5. Agent Execution (parallel async)
   ↓
6. AMRE Post-Processing
   ↓
7. Synthesis Agent (weighted vote + conflict resolution)
   ↓
8. Final Signal (BUY/SELL/HOLD/NEUTRAL/AVOID + confidence)
```

---

## Backtest Results (ATOM-014)

| Metric | Value |
|--------|-------|
| Total Decisions | 12 |
| WIN Rate | 58.3% |
| Avg Sharpe | 0.71 |
| Max Drawdown | 4.7% |
| Best Regime | HIGH (60% win rate) |

---

## API Reference

### Python SDK

```python
from orchestration.sentinel_v5 import run_sentinel_v5, run_sentinel_v5_karl

# Basic run
result = await run_sentinel_v5("Analyze BTC", "BTCUSDT", "SWING")

# KARL mode (with self-improvement)
result = await run_sentinel_v5_karl(
    "Analyze BTC", "BTCUSDT", "SWING",
    enable_self_question=True,
    enable_backtest=True
)

# Get signal
signal = result["final_recommendation"]["signal"]  # "BUY"
confidence = result["final_recommendation"]["confidence"]  # 78
```

### CLI

```bash
# Basic
python -m orchestration.sentinel_v5 "Analyze BTC" BTCUSDT SWING

# KARL mode
python -m orchestration.sentinel_v5 --karl "Analyze BTC"

# Diagnostics
python -m orchestration.karl_cli --diag

# Continuous backtest
python -m orchestration.karl_cli --continuous BTCUSDT
```

---

## Database Schema

### Sessions (core/history.db)

| Column | Type | Description |
|--------|------|-------------|
| session_id | TEXT | UUID |
| symbol | TEXT | Trading pair |
| timeframe | TEXT | INTRADAY/SWING/POSITIONAL |
| final_signal | TEXT | BUY/SELL/HOLD/NEUTRAL |
| final_confidence | INTEGER | 0-100 |

### Agent Beliefs (core/belief.db)

| Column | Type | Description |
|--------|------|-------------|
| agent_name | TEXT | Agent identifier |
| alpha | REAL | Beta distribution α |
| beta | REAL | Beta distribution β |

---

## Configuration

### Environment Variables

```bash
# Optional - for real data
OPENAI_API_KEY=sk-...
BINANCE_API_KEY=...
BINANCE_SECRET=...

# Optional - for enhanced data
COINGECKO_API_KEY=...
POLYGON_API_KEY=...
```

### Agent Weights (config/agent_weights.yaml)

```yaml
category_weights:
  astro: 0.22
  fundamental: 0.15
  macro: 0.15
  quant: 0.18
  options: 0.12
  sentiment: 0.09
  technical: 0.09
```

---

## Conflict Resolution

### Astro vs Fundamental+Quant

When Astro disagrees with both Fundamental and Quant:

```
astro_weight *= 0.70    # -30% penalty
fundamental_weight *= 1.18   # +18% boost
quant_weight *= 1.12    # +12% boost
```

---

## Volatility Guards (V-06, V-07)

| Regime | ATR% | Confidence Drop | Position Size |
|--------|------|------------------|----------------|
| LOW | <1.5% | 0 | 3.0% |
| NORMAL | 1.5-3% | 0 | 2.0% |
| HIGH | 3-5% | -10 | 1.0% |
| EXTREME | >5% | -25 | 0.5% |

---

## MAS Factory Topology

### Node Types

| Type | Purpose |
|------|---------|
| `AgentNode` | Executes single agent |
| `SequentialNode` | Chains agents A→B→C |
| `ParallelNode` | Runs agents concurrently |
| `SwitchNode` | Conditional routing |
| `MergeNode` | Combines outputs |
| `LoopNode` | Iteration with exit condition |
| `ProxyNode` | Async wrapper |

### Pre-built Topologies

| Name | Nodes | Use Case |
|------|-------|----------|
| `STANDARD` | 3 roles, 1 switch, 1 merge | Basic analysis |
| `FAST` | 1 role | Quick signals |
| `DEEP_ANALYSIS` | 5 roles, 2 switches, loops | Full research |
| `ASTRO_ONLY` | 1 Astro role | Pure astrology |
| `META_REASONING` | 2 roles + loop | Self-improvement |

---

## File Structure

```
AstroFinSentinelV5/
├── orchestration/
│   ├── sentinel_v5.py      # Main orchestrator
│   ├── sentinel_v5_mas.py  # MAS Factory mode
│   ├── router.py           # Query classification
│   └── karl_cli.py         # Rich CLI UI
├── agents/
│   ├── _impl/              # Active agent implementations
│   │   ├── fundamental_agent.py
│   │   ├── quant_agent.py
│   │   ├── macro_agent.py
│   │   ├── technical_agent.py
│   │   ├── astro_council/
│   │   └── ...
│   ├── karl_synthesis.py   # KARL integration
│   └── base_agent.py       # Agent interface
├── core/
│   ├── ephemeris.py        # Swiss Ephemeris
│   ├── aspects.py         # Planetary aspects
│   ├── volatility.py       # Volatility regime
│   ├── history_db.py      # SQLite persistence
│   ├── belief.py          # Thompson Beta(α,β)
│   └── thompson.py        # Thompson Sampling
├── amre/                  # KARL AMRE Framework
│   ├── uncertainty.py
│   ├── grounding.py
│   ├── reward.py
│   ├── oap_optimizer.py
│   ├── self_question.py
│   ├── hierarchical_policy.py
│   ├── audit.py           # DecisionRecord
│   ├── backtest_loop.py
│   ├── replay_buffer.py
│   ├── karl_integration.py
│   └── meta_questioning.py
├── mas_factory/            # MAS Factory (ATOM-R-028)
│   ├── topology.py        # Role, SwitchNode, Topology
│   ├── architect.py       # Topology builder
│   ├── registry.py        # Agent definitions
│   ├── adapters.py        # Context adapters
│   ├── engine.py          # Production engine
│   └── visualizer.py     # Mermaid output
├── db/                    # PostgreSQL layer
│   ├── session.py
│   ├── models.py
│   ├── repositories.py
│   └── karl_replay.py
├── backtest/
│   ├── atom_014_stress_test.py
│   ├── metrics_agent.py
│   └── metrics_history.db
└── knowledge/
    └── DB_ARCHITECTURE_PROMPT.md
```

---

## Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Win Rate | >55% | 58.3% ✅ |
| Sharpe Ratio | >1.0 | 0.71 ⚠️ |
| Avg Confidence | >65% | 70% ✅ |
| Signal Coverage | >90% | 100% ✅ |
| API Latency (p95) | <2s | ~0.5s ✅ |
| Backtest Runs | >100 | 12 ⚠️ |

---

## Known Limitations

1. **Sharpe Ratio** — Below target (0.71 vs 1.0). Consider:
   - Tighter stop-losses
   - Better regime filtering
   - More aggressive Astro signals in HIGH volatility

2. **Backtest Count** — Only 12 runs. Need:
   - 100+ runs for statistical significance
   - Multi-symbol testing (BTC, ETH, SOL)

3. **Data Sources** — Free tier only:
   - Binance (OHLCV) ✅
   - CoinGecko (metadata) ✅
   - Yahoo Finance (VIX, DXY) ✅
   - Polygon.io (options flow) ❌ (paid)

---

## Next Steps (Post-R-034)

1. **Real Trading Integration**
   - Binance spot execution
   - Paper trading mode
   - Position tracking

2. **Enhanced Data**
   - Options flow (Polygon.io)
   - Social sentiment (Twitter/X API)
   - On-chain metrics (Glassnode)

3. **Portfolio Management**
   - Multi-symbol allocation
   - Rebalancing rules
   - Risk limits

4. **Mobile Dashboard**
   - Telegram alerts
   - Status page
   - Trade history

---

## License

Proprietary — All rights reserved  
Author: mahaasur13-sys

---

**Generated:** 2026-03-29  
**Version:** 5.0.0-production
