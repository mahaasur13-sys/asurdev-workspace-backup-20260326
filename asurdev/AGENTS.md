# asurdev Sentinel — Agents Memory

**Project:** asurdev Sentinel v3.1  
**Status:** ✅ Refactored — unified types, AstroCouncil properly integrated  
**Architecture:** Clean modular design with deterministic astrology

---

## Agent Board (Внутренний Совет Директоров)

| Agent | Type | Purpose | Implementation |
|-------|------|---------|-----------------|
| `MarketAnalyst` | Technical | Price action, RSI, trends | `agents._impl.market_analyst` |
| `BullResearcher` | Fundamental | Find bullish cases | `agents._impl.bull_researcher` |
| `BearResearcher` | Fundamental | Find bearish cases | `agents._impl.bear_researcher` |
| **`AstroCouncil`** | Astrology | Western + Vedic + Financial | `agents._impl.astro_council` ✅ |
| `CycleAgent` | Cycles | Timing Solution integration | `agents._impl.cycle_agent` |
| `Synthesizer` | Aggregation | C.L.E.A.R. verdict | `agents._impl.synthesizer` |

### AstroCouncil Sub-Agents (v3.1)

| Sub-Agent | Source | Output |
|-----------|--------|--------|
| `WesternAstrologer` | Lilly "Christian Astrology" | Essential Dignities, Aspects |
| `VedicAstrologerAgent` | Muhurta, Nakshatras | Choghadiya, Muhurta Score |
| `FinancialAstrologer` | Combined | Final Signal (Western + Vedic + Moon) |

---

## Unified Types (v3.1)

**Single source of truth:** `agents/types.py`

```python
from agents.types import Signal, AgentResponse, TradingSignal

# Signal enum
Signal.STRONG_BUY   # +100
Signal.BUY         # +70
Signal.NEUTRAL     # +50
Signal.SELL        # +30
Signal.STRONG_SELL # 0

# AgentResponse — all agents return this
response = AgentResponse(
    agent_name="Market",
    signal="BULLISH",
    confidence=75,
    summary="Price above MA20",
    details={...}
)

# TradingSignal — final output
signal = TradingSignal.from_agents("BTC", [responses], entry_price=67000)
```

---

## Architecture (v3.1)

```
┌─────────────────────────────────────────────────────────────────────┐
│                      asurdev SENTINEL v3.1                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │
│  │   MARKET    │    │    BULL    │    │    BEAR    │              │
│  │  ANALYST    │    │ RESEARCHER │    │ RESEARCHER │              │
│  │   (25%)     │    │   (15%)    │    │   (15%)    │              │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘              │
│         │                  │                  │                     │
│         └──────────────────┼──────────────────┘                     │
│                            ▼                                        │
│                   ┌─────────────────┐                              │
│                   │      CYCLE     │                              │
│                   │   (parallel)   │                              │
│                   └────────┬────────┘                              │
│                            │                                        │
│                            ▼                                        │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                   ASTRO COUNCIL (RAG-enabled)                │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │   │
│  │  │  WESTERN    │  │   VEDIC     │  │  FINANCIAL  │             │   │
│  │  │  (Lilly)    │  │ (Muhurta)   │  │ (Combined) │             │   │
│  │  │             │  │             │  │             │             │   │
│  │  │ • Dignities │  │ • Nakshatra │  │ Signal:     │             │   │
│  │  │ • Aspects    │  │ • Choghadiya│  │ STRONG_BUY │             │   │
│  │  │ • Accidental│  │ • Muhurta   │  │ BUY         │             │   │
│  │  │             │  │             │  │ NEUTRAL     │             │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                            │                                        │
│                            ▼                                        │
│                   ┌─────────────────┐                              │
│                   │   DOW + COND.   │                              │
│                   │  routing        │                              │
│                   └────────┬────────┘                              │
│                            │                                        │
│              ┌─────────────┼─────────────┐                        │
│              ▼             ▼             ▼                         │
│        ┌──────────┐  ┌──────────┐  ┌────────────┐                │
│        │   GANN   │  │ ANDREWS  │  │ DIRECT     │                │
│        │ (diff>30)│  │(15<diff≤30)│ │(diff≤15)  │                │
│        └────┬─────┘  └────┬─────┘  └─────┬──────┘                │
│             └─────────────┴─────────────┘                        │
│                            │                                        │
│                   ┌─────────────────┐                              │
│                   │    MERIDIAN     │                              │
│                   └────────┬────────┘                              │
│                            │                                        │
│                            ▼                                        │
│                   ┌─────────────────┐                              │
│                   │   SYNTHESIZER  │                              │
│                   │ C.L.E.A.R. ✓   │                              │
│                   └─────────────────┘                              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Deterministic Astrology (No "Intuition")

### Western (Lilly)

```
Essential Dignities Score = Exaltation(+5) + Fall(-4) + Triplicity(±3) + Term(±2)
Accidental Dignities = Joy(+5) + Stationary(+4) + Combust(-4) + Oriental(±2)
Aspects: Conjunction(8°), Sextile(6°), Square(8°), Trine(8°), Opposition(10°)
```

### Vedic (Muhurta)

```
Muhurta Score = Nakshatra(30%) + Sign(20%) + Day(20%) + Choghadiya(30%)

Nakshatras:
  BULLISH: Rohini(85), Swati(80), Mrigashira(75), Hasta(75)
  BEARISH: Mula(35), Ardra(40), Ashlesha(30)
  
Choghadiya:
  BEST: Amrit (100)
  GOOD: Labh(75), Char(75), Shubh(75)
  BAD: Kaal(20), Rog(20), Ari(20)
```

---

## RAG System

```python
from rag import ObsidianKnowledgeBase

# Connect to Obsidian Vault
kb = ObsidianKnowledgeBase(
    vault_path="/home/workspace/obsidian-sync",
    persist_dir="./data/rag_index"
)

# Query for context
context = kb.get_context("Nakshatra Shatabhisha trading")
# → Used by AstroCouncil to enrich analysis
```

---

## Usage

```python
from agents.langgraph_orchestrator import LangGraphOrchestrator

# Full analysis
orchestrator = LangGraphOrchestrator()
result = await orchestrator.analyze("BTC", action="hold")

# Check results
print(result.final_verdict)  # Signal.STRONG_BUY
print(result.confidence_avg)  # 78.5

# Individual agent responses
for key in ["market", "bull", "bear", "astro"]:
    resp = result.get(f"{key}_response")
    if resp:
        print(f"{key}: {resp.signal} ({resp.confidence}%)")
```

---

## Running

```bash
# 1. Build RAG index
python -m rag.obsidian_kb --vault /home/workspace/obsidian-sync --output ./data/rag_index

# 2. Run analysis
python -m agents.langgraph_orchestrator --symbol BTC --date 2026-03-22

# 3. Dashboard
streamlit run ui/dashboard.py
```

---

## Key Files (v3.1)

| File | Purpose |
|------|---------|
| `agents/types.py` | **NEW** — Unified Signal, AgentResponse, TradingSignal |
| `agents/signal.py` | Signal enum (kept for backwards compat) |
| `agents/langgraph_orchestrator.py` | Main orchestrator with AstroCouncil |
| `agents/state.py` | LangGraph state definition |
| `agents/_impl/astro_council/` | AstroCouncil sub-agents + RAG |
| `astrology/core.py` | Western Dignities (Lilly) |
| `astrology/vedic.py` | Vedic calculations |
| `rag/` | RAG system for Obsidian |
| `_core/agents.py` | Legacy wrapper (redirects to types.py) |

---

## Visualizations Module (v3.2)

Новый модуль визуализации для астрологических и финансовых данных.

### Структура

```
visualizations/
├── __init__.py           # exports: ZodiacWheel, GannLevels, AstroOverlay
├── zodiac_wheel.py       # Натальная карта (matplotlib)
├── gann_levels.py        # Gann уровни (plotly)
└── astro_overlay.py      # Астро-оверлей на свечные графики
```

### Быстрый старт

```python
from visualizations import ZodiacWheel, GannLevels, AstroOverlay

# 1. Зодиакальное колесо
wheel = ZodiacWheel(style='modern')  # modern | classic | astroprint
img_bytes = wheel.draw(
    positions={
        'Sun': {'sign': 0, 'degree': 15},   # Овен 15°
        'Moon': {'sign': 3, 'degree': 22},   # Рак 22°
    },
    houses={1: 0, 2: 25, 3: 45},  # Кухпи домов
    aspects=[
        {'planet1': 'Sun', 'planet2': 'Moon', 'type': 'Trine', 'orb': 7},
    ]
)

# 2. Gann уровни
gann = GannLevels()
levels = gann.calculate_levels(high=68000, low=62000, close=64500)
fig = gann.draw_prices(prices_df, levels)
fig.write_html('gann_chart.html')

# 3. Астро-оверлей
overlay = AstroOverlay()
events = [
    {'date': '2026-03-22', 'type': 'New Moon'},
    {'date': '2026-03-25', 'type': 'Square', 'planet1': 'Mars', 'planet2': 'Saturn'},
]
fig = overlay.add_to_figure(base_fig, events)
```

### React компоненты

```
ui_react/src/components/
├── ZodiacWheel.tsx    # SVG колесо (recharts + custom SVG)
└── GannChart.tsx      # Финансовый график с уровнями
```

```tsx
import { ZodiacWheel } from './components/ZodiacWheel';
import { GannChart } from './components/GannChart';

// Натальная карта
<ZodiacWheel
  positions={{
    Sun: { sign: 0, degree: 15 },
    Moon: { sign: 3, degree: 22 },
  }}
  houses={{ 1: 0, 2: 25 }}
  size={400}
  variant="modern"
/>

// Gann график
<GannChart
  data={ohlcvData}
  levels={gannLevels}
  astroMarkers={astroEvents}
  showVolume={true}
/>
```

---

## Changes from v3.0 → v3.1

1. **Unified types** — Single `agents/types.py` (Signal, AgentResponse, TradingSignal)
2. **AstroCouncil properly integrated** — LangGraph now uses `AstroCouncilAgent`
3. **Removed legacy duplication** — `_core/agents.py` is now a wrapper
4. **Clean imports** — All agents import from `agents.types`
5. **Better state management** — SentinelState includes lat/lon for astrology

---

## Location Coordinates (Сохранённые локации)

| Локация | Lat | Lon | Дата добавления |
|---------|-----|-----|-----------------|
| **Самара, Россия** | 53.183°N | 50.117°E | 2026-03-22 |

### Пример использования

```bash
python muhurta_search.py 2026-03-23 "Самара" 53.183 50.117
```