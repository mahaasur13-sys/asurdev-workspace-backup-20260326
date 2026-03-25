# asurdev Sentinel v3.2 — Архитектура

## Концепция

**asurdev Sentinel** — мультиагентная система принятия решений по принципу "Внутренний совет директоров". Не даёт готовых ответов, а разыгрывает совет из специализированных агентов, каждый из которых смотрит на задачу со своей стороны.

```
┌─────────────────────────────────────────────────────────────────┐
│                      C.L.E.A.R. BOARD                           │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│   MARKET     │    BULL     │    BEAR     │      ASTRO         │
│   ANALYST    │  RESEARCHER │  RESEARCHER │     COUNCIL         │
│   (25%)      │   (15%)     │   (15%)     │      (20%)         │
├──────────────┴──────────────┴──────────────┴────────────────────┤
│                      SYNTHESIZER                                 │
│              "Что решил совет директоров?"                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Структура v3.2

```
asurdevSentinel/
├── agents/
│   ├── __init__.py              ← ✅ Unified exports
│   ├── types.py                 ← ✅ Signal, AgentResponse, TradingSignal (SSoT)
│   ├── state.py                 ← SentinelState TypedDict
│   │
│   ├── memory/                  ← ✅ NEW: Persistent Memory Module
│   │   ├── __init__.py
│   │   ├── manager.py           ← MemoryManager, SessionMemory
│   │   ├── chroma.py            ← ChromaMemory (RAG storage)
│   │   ├── fuzzy.py             ← FuzzyMemory (adaptive weights)
│   │   └── integration.py       ← MemoryMiddleware, MemoryAwareAgentNode
│   │
│   ├── graph/                   ← ✅ NEW: LangGraph Module
│   │   ├── __init__.py
│   │   ├── nodes.py             ← All node_* functions
│   │   ├── routing.py          ← route_based_on_disagreement
│   │   └── builder.py           ← build_graph
│   │
│   ├── _impl/                   ← Agent implementations
│   │   ├── __init__.py
│   │   ├── base_agent.py        ← BaseAgent, AgentResponse
│   │   ├── market_analyst.py
│   │   ├── bull_researcher.py
│   │   ├── bear_researcher.py
│   │   ├── astro_council/
│   │   │   ├── agent.py         ← ✅ AstroCouncilAgent (primary)
│   │   │   ├── western.py
│   │   │   ├── vedic.py
│   │   │   └── financial.py
│   │   ├── cycle_agent.py
│   │   ├── gann_agent.py
│   │   ├── andrews_agent.py
│   │   ├── dow_agent.py
│   │   └── meridian_agent.py
│   │
│   ├── langgraph_orchestrator.py ← Main entry point
│   └── orchestrator.py           ← Legacy v2 orchestrator
│
├── _core/                        ← ⚠️ DEPRECATED (redirects to agents/)
│
└── astrology/                     ← Deterministic calculations
```

---

## Unified Types (v3.2)

**Single source of truth:** `agents/types.py`

```python
from agents.types import Signal, AgentResponse, TradingSignal

# Signal enum — 6 уровней + backwards compatibility
Signal.STRONG_BUY   # 100
Signal.BUY          # 70  
Signal.NEUTRAL      # 50
Signal.HOLD         # 50
Signal.SELL         # 30
Signal.STRONG_SELL  # 0

# AgentResponse — стандартный ответ любого агента
@dataclass
class AgentResponse:
    agent_name: str
    signal: str
    confidence: int  # 0-100
    summary: str
    details: Dict[str, Any]
    metadata: Dict[str, Any]
    errors: List[str]
    timestamp: str
```

---

## Memory Module

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     MemoryMiddleware                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐│
│  │ SessionMemory│  │ ChromaMemory │  │ FuzzyMemory         ││
│  │ (in-memory) │  │ (persistent) │  │ (adaptive weights) ││
│  └─────────────┘  └─────────────┘  └─────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Usage

```python
from agents.memory import MemoryMiddleware, MemoryManager

# Create middleware
mm = MemoryMiddleware(persist_dir="./data/chroma_db")

# Start session
mm.start_session(session_id="btc_001", symbol="BTC", action="hold")

# Get RAG context for agent
ctx = mm.get_context_for_agent("astro", "BTC")
print(ctx.memory_summary)

# Get adaptive weights
weights = mm.get_adaptive_weights("BTC", market_condition="BULLISH")
# {'market': 0.20, 'bull': 0.12, 'bear': 0.08, ...}
```

### ChromaDB Collections

| Collection | Purpose |
|------------|---------|
| `analyses` | Agent analysis records |
| `feedback` | User feedback |
| `outcomes` | Prediction outcomes for learning |
| `patterns` | Learned market patterns |

---

## Graph Module

### Flow

```
market → [bull, bear, astro, cycle] (parallel)
                ↓
            [dow] (conditional routing)
                ↓
    ┌─────────┴─────────┐
    ↓         ↓         ↓
  gann    andrews   synthesize
    └─────────┬─────────┘
              ↓
          meridian
              ↓
          synthesize → END
```

### Routing Logic

```python
def route_based_on_disagreement(state) -> "gann" | "andrews" | "synthesize":
    diff = abs(bull.confidence - bear.confidence)
    
    if diff > 30:   # High disagreement → Gann resolution
        return "gann"
    elif diff > 15:  # Moderate → Andrews
        return "andrews"
    else:            # Low → direct synthesis
        return "synthesize"
```

---

## Orchestrators

### MemoryEnabledOrchestrator (Recommended)

```python
from agents import MemoryEnabledOrchestrator

orchestrator = MemoryEnabledOrchestrator(
    persist_dir="./data/chroma_db",
    enable_rag=True,
    enable_adaptive_weights=True,
)

result = await orchestrator.analyze("BTC", action="hold")

# Record feedback
orchestrator.add_feedback(result, agent="astro", helpful=True, rating=5)

# Record outcome (later)
orchestrator.add_outcome("BTC", agent="astro", prediction="BULLISH", 
                         actual_direction="correct", confidence=75, price_change=2.5)
```

### LangGraphOrchestrator (Legacy)

```python
from agents import LangGraphOrchestrator

orchestrator = LangGraphOrchestrator(
    interrupt_before=["synthesize"]  # Human-in-the-loop
)

result = await orchestrator.analyze("BTC", action="hold")
```

---

## Агенты

| Agent | Weight | Implementation |
|-------|--------|----------------|
| `MarketAnalyst` | 20% | `agents._impl.market_analyst` |
| `BullResearcher` | 10% | `agents._impl.bull_researcher` |
| `BearResearcher` | 10% | `agents._impl.bear_researcher` |
| **`AstroCouncil`** | 15% | `agents._impl.astro_council.agent` |
| `CycleAgent` | 10% | `agents._impl.cycle_agent` |
| `DowTheoryAgent` | 10% | `agents._impl.dow_agent` |
| `AndrewsAgent` | 8% | `agents._impl.andrews_agent` |
| `GannAgent` | 7% | `agents._impl.gann_agent` |
| `MeridianAgent` | 10% | `agents._impl.meridian_agent` |

---

## AstroCouncil (v3.2)

**Главное изменение:** Теперь это primary astrology engine, интегрированный в LangGraph.

### Sub-Agents

```
AstroCouncilAgent
├── WesternAstrologer (Lilly)
│   ├── Essential Dignities
│   ├── Accidental Dignities  
│   └── Aspects & Receptions
│
├── VedicAstrologerAgent (Swiss Ephemeris)
│   ├── Nakshatras (27)
│   ├── Choghadiya (8 periods)
│   └── Muhurta Score
│
├── **MankashiAgent** (Vedic, text-based)
│   ├── Daily Muhurta forecasts
│   ├── Planetary yogas
│   ├── Planet strength analysis
│   └── Eclipse risk detection
│
└── FinancialAstrologer
    └── Combined Signal
```

### MankashiAgent (Migrated from AstroFin Sentinel)

Alternative Vedic implementation using text-based Mankashi forecasting:

```python
from agents._impl.astro_council.mankashi_agent import VedicAstrologerAgent

agent = VedicAstrologerAgent(birth_date="03.05.1967")
report = agent.analyze(symbol="BTC", side="buy")
# report.signal, report.confidence, report.muhura, etc.
```

**Features:**
- Daily Muhurta extraction
- Planetary yoga detection (Дхана Йога, Ханса Йога, etc.)
- Planet strength (exaltation/fall)
- Nakshatra influence mapping
- Eclipse risk warnings
- Moon phase detection

---

## Версии

| Версия | Дата | Изменения |
|--------|------|-----------|
| v1.0 | 2025 | Базовая архитектура |
| v2.0 | 2026-01 | Рефакторинг, Clean Architecture |
| v3.0 | 2026-03 | RAG, Astro Council, детерминизм |
| v3.1 | 2026-03-22 | Unified types, AstroCouncil integrated |
| **v3.2** | 2026-03-22 | **Memory/Graph modules, clean architecture** |

---

## Запуск

```bash
# Full analysis with memory
python -c "
from agents import MemoryEnabledOrchestrator
import asyncio

async def main():
    o = MemoryEnabledOrchestrator()
    r = await o.analyze('BTC', action='hold')
    print(f'Verdict: {r[\"final_verdict\"]}')

asyncio.run(main())
"

# Quick test
python -m agents.langgraph_orchestrator
```
