# AstroFin Sentinel v4.4

**Гибридная AI-платформа для финансового анализа с астрологией и multi-agent оркестрацией.**

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentOrchestra Layer                       │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐ │
│  │ Conductor  │ │   Planner   │ │   MCP Manager          │ │
│  │  Agent     │ │   Agent     │ │   (Tool Orchestration) │ │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    AstroCouncil Agent                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              16 Sub-Agents (Parallel)                │   │
│  │  Western │ Vedic │ Financial │ Technical │ Quant    │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│                    SharedMemoryBank (RAG)                    │
│  Ephemeris │ Technical │ Astro │ Trading │ Election        │
├─────────────────────────────────────────────────────────────┤
│                    Infrastructure                           │
│  NeMo Guardrails │ NanoClaw Sandbox │ Redis │ StructLog    │
└─────────────────────────────────────────────────────────────┘
```

## 🤖 Агенты (16)

### Core Agents
| Agent | Вес | Описание |
|-------|------|----------|
| `FundamentalAgent` | 18% | Фундаментальный анализ (DG, NVT, SOPR) |
| `MacroAgent` | 13% | Макроэкономика (VIX, DXY, Fed Rate) |
| `QuantAgent` | 12% | ML + бэктестирование |
| `PredictorAgent` | 12% | ML-прогнозирование |
| `OptionsFlowAgent` | 10% | Gamma Exposure, Unusual Activity |
| `SentimentAgent` | 10% | Fear/Greed, Market Sentiment |
| `TechnicalAgent` | 10% | RSI, MACD, Bollinger (с RAG) |

### Astro Agents
| Agent | Вес | Описание |
|-------|------|----------|
| `ElectivePredictorAgent` | 5% | Элективная астрология |
| `WesternElectionalAgent` | 5% | Western electional windows |
| `MuhurtaAgent` | 3% | Vedic Muhurta timing |
| `TransitAgent` | 3% | Planetary transits |
| `NatalAgent` | 3% | Natal chart analysis |
| `AspectAgent` | 3% | Western aspects |
| `FinancialAstroAgent` | 3% | Financial astrology |
| `HealthAstroAgent` | 2% | Health astrology |
| `RelocationAgent` | 2% | Relocation astrology |
| `HoraryAgent` | 2% | Horary astrology |
| `EventTimingAgent` | 2% | Event timing |

### Research Agents
| Agent | Вес | Описание |
|-------|------|----------|
| `BullResearcher` | 5% | Бычий кейс |
| `BearResearcher` | 5% | Медвежий кейс |
| `RiskAgent` | 5% | Оценка риска |

## 🛡️ Безопасность

### NeMo Guardrails
```python
# Фильтрация вредоносного кода
- Input rails: SQL injection, XSS, path traversal
- Output rails: PII detection, harmful content
- Topic rails: Financial advice validation
```

### NanoClaw Sandbox
```python
# Изоляция агентов в MicroVM
- IsolationLevel.MICROVM для критических агентов
- ResourceLimits: CPU 2.0, Memory 2g, Disk 8g
- Network policy: egress-only
- Seccomp profile: strict
```

## 📊 RAG Knowledge Base

### Domains
- `technical/` - RSI, MACD, Bollinger Bands, Support/Resistance
- `astro/` - Vedic & Western astrology
- `trading/` - Trading strategies
- `election/` - Electional astrology
- `mikrotik/` - Network configuration

### Usage
```python
from backend.src.rag_knowledge import get_rag_kb

rag = await get_rag_kb()
chunks = await rag.retrieve(
    query="RSI overbought signal",
    domain="technical",
    top_k=5
)
```

## 🚀 Запуск

### Python API
```python
from backend.agents import AstroCouncilAgent
import asyncio

async def main():
    agent = AstroCouncilAgent()
    result = await agent.analyze({
        "symbol": "BTCUSDT",
        "current_price": 65000,
        "timeframe": "SWING"
    })
    print(f"Signal: {result.signal.value}")
    print(f"Confidence: {result.confidence}")

asyncio.run(main())
```

### CLI
```bash
cd /home/workspace/astrofin
PYTHONPATH=. python3 backend/main.py
```

### Tests
```bash
PYTHONPATH=. pytest backend/tests/ -v
```

## 📁 Структура проекта

```
astrofin/
├── backend/
│   ├── agents/
│   │   ├── base_agent.py           # Base classes
│   │   ├── astro_council/          # Main orchestrator
│   │   ├── technical/               # Technical analysis
│   │   ├── fundamental/            # Fundamental analysis
│   │   ├── macro/                  # Macro economics
│   │   ├── quant/                  # Quantitative analysis
│   │   ├── options_flow/           # Options flow
│   │   ├── sentiment/              # Sentiment analysis
│   │   ├── western_electional/     # Western election
│   │   ├── astro/                 # Various astro agents
│   │   └── orchestra/              # Orchestration
│   ├── src/
│   │   ├── rag_knowledge.py        # RAG knowledge base
│   │   ├── aiq_compat.py          # AgentIQ compatibility
│   │   ├── swiss_ephemeris.py     # Planetary calculations
│   │   └── guardrails.py          # NeMo Guardrails
│   ├── shared_memory/
│   │   └── bank.py                # Memory bank
│   └── utils/
│       ├── polygon_client.py      # Polygon.io API
│       └── cache_manager.py       # Redis caching
├── knowledge/
│   ├── technical/                  # Technical analysis docs
│   ├── astro/                     # Astrology docs
│   ├── election/                  # Election docs
│   └── mikrotik/                  # Network docs
└── tests/
    └── test_*.py                  # Pytest tests
```

## 🔧 Технологии

| Категория | Технологии |
|-----------|------------|
| **Orchestration** | AgentIQ, Dynamo Runtime, MCP |
| **Astro Computing** | Swiss Ephemeris (swisseph) |
| **Data** | NumPy, Pandas, SciPy |
| **ML** | scikit-learn |
| **Caching** | Redis (async) |
| **API Clients** | Polygon.io, httpx, aiohttp |
| **Safety** | NeMo Guardrails, NanoClaw Sandbox |
| **Logging** | StructLog |
| **Testing** | Pytest, pytest-asyncio |
| **Validation** | Pydantic |

## 📈 Статистика

- **Агенты**: 16 (Core + Astro + Research)
- **Тесты**: 32 passing
- **RAG Sources**: 4 domains
- **Technologies**: 15+ integrations

## ⚙️ Environment Variables

```bash
# API Keys
POLYGON_API_KEY=your_polygon_key
COINGECKO_API_KEY=your_coingecko_key
FRED_API_KEY=your_fred_key

# Redis
REDIS_URL=redis://localhost:6379/0

# Swiss Ephemeris
EPHEMERIS_PATH=/home/workspace/astrofin/backend/ephe
```

## 📝 Лицензия

MIT License
