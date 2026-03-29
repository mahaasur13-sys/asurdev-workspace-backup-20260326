<div align="center">

# 🧠 AstroFin Sentinel V5

**Multi-Agent Trading System with KARL Self-Improvement**

![Version](https://img.shields.io/badge/version-5.0.0--production-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![License](https://img.shields.io/badge/license-proprietary-red)

*AstroFin Sentinel V5* — это продвинутая мультиагентная торговая система, объединяющая фундаментальный, технический, макроэкономический и астрологический анализ для генерации торговых сигналов по криптовалютам.

</div>

---

## 🎯 Возможности

| Возможность | Описание |
|-------------|----------|
| **14 специализированных агентов** | Fundamental, Quant, Macro, Technical, Astro, Sentiment и др. |
| **Thompson Sampling** | Динамический выбор агентов на основе Bayesian belief tracking |
| **KARL AMRE Framework** | Self-improvement loop с uncertainty quantification |
| **MAS Factory** | Динамическая оркестрация агентов через topology |
| **Meta-Questioning** | Self-reflection для bias detection |
| **Astro-Timing** |Muhurta/Panchanga для optimal entry windows |
| **Volatility Guards** | Динамическая адаптация риск-менеджмента |

---

## 🚀 Быстрый старт

```bash
# Установка зависимостей
pip install -r requirements.txt

# Базовая проверка
python -m orchestration.sentinel_v5 "Analyze BTC" BTCUSDT SWING

# С KARL (self-improvement)
python -m orchestration.sentinel_v5 --karl "Analyze BTC"

# Непрерывный backtest
python -m orchestration.karl_cli --continuous BTCUSDT

# Диагностика системы
python -m orchestration.karl_cli --diag
```

---

## 📊 Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                     USER QUERY                                │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                      ROUTER                                   │
│         (классификация: TECHNICAL/FUNDAMENTAL/etc)           │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│               THOMPSON SAMPLING                              │
│    ( Bayesian agent selection: выбираем top-K агентов )       │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│                    MAS FACTORY                               │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│   │Technical │  │  Astro   │  │  Macro    │  │Fundament │  │
│   │  Pool    │  │ Council  │  │   Flow    │  │   Flow   │  │
│   │(3 ags)  │  │ (5 ags)  │  │(4 agents)│  │(3 agents)│  │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│        └──────────────┼──────────────┼──────────────┘        │
└───────────────────────┼─────────────┼────────────────────────┘
                        ↓             ↓
┌─────────────────────────────────────────────────────────────┐
│              KARL AMRE LOOP                                 │
│  Uncertainty → Grounding → Meta-Questioning → OAP          │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│              SYNTHESIS AGENT                                │
│     (Weighted vote + Conflict Resolution + Volatility)      │
└───────────────────────┬─────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────────┐
│                   FINAL SIGNAL                               │
│     🟢 BUY (78)  |  🔴 SELL (65)  |  ⚪ NEUTRAL (50)       │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Структура проекта

```
AstroFinSentinelV5/
├── orchestration/           # Оркестрация
│   ├── sentinel_v5.py       # Основной runner
│   ├── sentinel_v5_mas.py    # MAS Factory mode
│   ├── router.py             # Классификация запросов
│   └── karl_cli.py           # Rich CLI UI
├── agents/                   # Агенты
│   ├── _impl/               # Реализации агентов
│   │   ├── fundamental_agent.py
│   │   ├── quant_agent.py
│   │   ├── macro_agent.py
│   │   ├── technical_agent.py
│   │   ├── sentiment_agent.py
│   │   ├── options_flow_agent.py
│   │   ├── astro_council/
│   │   └── ...
│   ├── karl_synthesis.py    # KARL integration
│   └── base_agent.py         # Базовый класс
├── core/                     # Ядро
│   ├── ephemeris.py         # Swiss Ephemeris
│   ├── aspects.py           # Планетарные аспекты
│   ├── volatility.py         # Волатильность
│   ├── history_db.py         # SQLite persistence
│   ├── belief.py            # Thompson Beta(α,β)
│   └── thompson.py          # Thompson Sampling
├── amre/                     # KARL AMRE Framework
│   ├── uncertainty.py        # Неопределённость
│   ├── grounding.py          # Валидация
│   ├── self_question.py      # Meta-questions
│   ├── oap_optimizer.py      # Position sizing
│   ├── reward.py            # Reward functions
│   ├── audit.py            # DecisionRecord
│   └── backtest_loop.py     # Continuous backtest
├── mas_factory/              # MAS Factory (ATOM-R-028)
│   ├── topology.py         # Role, SwitchNode, Topology
│   ├── architect.py        # Topology builder
│   ├── registry.py         # Agent definitions
│   ├── adapters.py         # Context adapters
│   ├── engine.py           # Production engine
│   └── visualizer.py      # Mermaid output
├── db/                       # PostgreSQL layer
│   ├── session.py
│   ├── models.py
│   └── repositories.py
├── backtest/                 # Бэктестинг
│   └── atom_014_stress_test.py
└── knowledge/                 # RAG knowledge base
    └── DB_ARCHITECTURE_PROMPT.md
```

---

## ⚙️ Конфигурация

### Переменные окружения (.env)

```bash
# Опционально — для enhanced данных
OPENAI_API_KEY=sk-...

# Swiss Ephemeris
SWE_EPHE_PATH=/usr/share/ephe

# Базы данных
DATABASE_URL=postgresql://user:pass@localhost/astrofin
```

### Веса агентов (config/agent_weights.yaml)

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

## 📈 Результаты бэктестинга

| Метрика | Цель | Текущий результат |
|---------|------|-------------------|
| Win Rate | >55% | ✅ 58.3% |
| Sharpe Ratio | >1.0 | ⚠️ 0.71 |
| Max Drawdown | <10% | ✅ 4.7% |
| Avg Confidence | >65% | ✅ 70% |

---

## 🔧 Использование

### Python API

```python
import asyncio
from orchestration.sentinel_v5 import run_sentinel_v5, run_sentinel_v5_karl

async def main():
    # Basic run
    result = await run_sentinel_v5(
        user_query="Analyze BTC for swing trade",
        symbol="BTCUSDT",
        timeframe="SWING"
    )
    
    signal = result["final_recommendation"]["signal"]
    confidence = result["final_recommendation"]["confidence"]
    print(f"SIGNAL: {signal} (confidence: {confidence})")
    
    # KARL mode (with self-improvement)
    result = await run_sentinel_v5_karl(
        user_query="Analyze BTC",
        symbol="BTCUSDT",
        timeframe="SWING",
        enable_self_question=True,
        enable_backtest=True
    )

asyncio.run(main())
```

### CLI

```bash
# Анализ BTC
python -m orchestration.sentinel_v5 "Analyze BTC" BTCUSDT SWING

# KARL режим
python -m orchestration.sentinel_v5 --karl "Analyze BTC"

# Непрерывный бэктест
python -m orchestration.karl_cli --continuous BTCUSDT

# Диагностика
python -m orchestration.karl_cli --diag
```

### MAS Factory режим

```python
from mas_factory.engine import ProductionMASEngine
from mas_factory.architect import MASFactoryArchitect

engine = ProductionMASEngine()
result = await engine.run_sync("Analyze BTC", "BTCUSDT", "SWING")
```

---

## 🧪 Тестирование

```bash
# Все тесты
cd AstroFinSentinelV5
python -m pytest tests/ -v

# Стресс-тест ATOM-014
python backtest/atom_014_stress_test.py

# MAS Factory тесты
python mas_factory/atom_032_e2e_test.py

# Production тесты
python mas_factory/atom_033_production_test.py
```

---

## 📋 Changelog

### v5.0.0-production (2026-03-29)

- ✅ **ATOM-R-033**: Production MAS Factory engine
- ✅ **ATOM-R-032**: E2E tests (7/7 passed)
- ✅ **ATOM-R-031**: Bug fixes for MAS Factory
- ✅ **ATOM-R-028**: Full MAS Factory architecture
- ✅ **ATOM-021**: Meta-questioning optimization
- ✅ **ATOM-020**: PostgreSQL integration + KARL replay
- ✅ **ATOM-019**: KARL trajectories in DB
- ✅ **ATOM-018**: PostgreSQL schema + Alembic migrations
- ✅ **ATOM-017**: Industrial CLI with Rich UI
- ✅ **ATOM-016**: Fixed duplicate runner imports
- ✅ **ATOM-015**: KARL CLI dashboard
- ✅ **ATOM-014**: Stress tests (12 decisions, 58.3% win rate)
- ✅ **ATOM-013**: KARL integration in synthesis
- ✅ **ATOM-012**: AMRE metrics (uncertainty, grounding, OAP)
- ✅ **ATOM-011**: Replay buffer + backtest loop

---

## ⚠️ Отказ от ответственности

**ЭТО НЕ ФИНАНСОВЫЙ КОНСУЛЬТАНТ.**

Система предназначена только для образовательных целей. Автор не несёт ответственности за любые убытки, понесённые в результате использования этой системы.

---

## 📄 License

Proprietary — All rights reserved

*Author: mahaasur13-sys*  
*GitHub: https://github.com/mahaasur13-sys/asurdev-workspace*
