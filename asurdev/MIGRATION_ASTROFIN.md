# AstroFin Sentinel Migration to AsurDev

**Date:** 2026-03-23  
**Source:** `astrofin-sentinel/` (standalone)  
**Target:** `asurdev/` (unified monorepo)  
**Status:** Completed

---

## Migration Summary

AstroFin Sentinel v2.0 merged into AsurDev Sentinel v3.2, combining:
- **AstroFin:** Mankashi Vedic astrology, JSON RAG, simple architecture
- **AsurDev:** Multi-agent LangGraph, ChromaDB RAG, Western + Vedic AstroCouncil

---

## What Was Migrated

### 1. Agents

| Source | Destination | Description |
|--------|-------------|-------------|
| `astrofin-sentinel/agents/astrologer.py` | `asurdev/agents/_impl/astro_council/mankashi_agent.py` | Vedic Astrologer (Mankashi system) |

### 2. Tools

| Source | Destination | Description |
|--------|-------------|-------------|
| `astrofin-sentinel/tools/astrology.py` | `asurdev/tools/mankashi.py` | Mankashi astrology forecasting |

### 3. Memory

| Source | Destination | Description |
|--------|-------------|-------------|
| `astrofin-sentinel/graph/memory.py` | `asurdev/agents/memory/json_store.py` | JSON-based RAG (simple, no ChromaDB) |

### 4. Prompts

| Source | Destination |
|--------|-------------|
| `astrofin-sentinel/prompts/astrologer.txt` | `asurdev/prompts/astrologer.txt` |
| `astrofin-sentinel/prompts/technical_analyst.txt` | `asurdev/prompts/technical_analyst.txt` |
| `astrofin-sentinel/prompts/fundamental_analyst.txt` | `asurdev/prompts/fundamental_analyst.txt` |
| `astrofin-sentinel/prompts/synthesizer.txt` | `asurdev/prompts/synthesizer.txt` |

---

## What's Different

### AstroCouncil Integration

**Before (AstroFin Sentinel):**
- Standalone `VedicAstrologerAgent` using Mankashi forecast script
- Simple JSON RAG memory
- 3 agents: Technical, Fundamental, Astrologer

**After (AsurDev):**
- `AstroCouncil` coordinates multiple sub-agents:
  - `WesternAstrologer` (Lilly system)
  - `VedicAstrologerAgent` (Swiss Ephemeris + Panchanga)
  - `FinancialAstrologer` (combined signal)
  - `MuhurtaSpecialist` (timing analysis)
- **NEW:** `MankashiAgent` as alternative Vedic implementation
- ChromaDB RAG + Fuzzy weights
- 9 agents total

### Memory Architecture

| Feature | AstroFin | AsurDev |
|---------|----------|---------|
| Storage | JSON files | ChromaDB vectors |
| Search | Keyword matching | Semantic embeddings |
| Adaptive weights | No | Yes (Fuzzy) |
| Fallback | — | JSONStore available |

---

## Usage

### Using Mankashi Astrologer

```python
from agents._impl.astro_council.mankashi_agent import VedicAstrologerAgent

agent = VedicAstrologerAgent(
    birth_date="03.05.1967",
    birth_time="07:15"
)

report = agent.analyze(symbol="BTC", side="buy")
print(f"Signal: {report.signal}")
print(f"Confidence: {report.confidence}")
print(f"Muhurta: {report.muhura['overall']}")
```

### Using JSON RAG Memory

```python
from agents.memory import RAGMemory, get_memory

memory = get_memory()

# Store analysis
entry_id = await memory.store_analysis(state)

# Retrieve
results = await memory.retrieve_relevant("BTC bullish", symbol="BTC")
```

---

## Archived

Original `astrofin-sentinel/` moved to:
```
asurdev/external/astrofin-sentinel/
```

Contains all original files preserving history.

---

## Next Steps

1. **Consolidate prompts** — merge `mankashi_agent.py` prompt with existing AstroCouncil prompts
2. **Test integration** — run `python -c "from agents._impl.astro_council.mankashi_agent import *; print('OK')"`
3. **Deprecate AstroFin** — mark original repo as legacy
4. **Update SPEC.md** — consolidate with ARCHITECTURE.md

---

## Version History

| Date | Change |
|------|--------|
| 2026-03-23 | Initial migration (v2.0 → v3.2) |
