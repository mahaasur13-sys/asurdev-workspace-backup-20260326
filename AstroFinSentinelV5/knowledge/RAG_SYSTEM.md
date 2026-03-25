# AstroFin Sentinel v5 — RAG Knowledge System

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                    RAG-First Multi-Agent System                      │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   User Query ──► Router Agent                                        │
│                      │                                                │
│         ┌────────────┼────────────┐                                  │
│         ▼            ▼            ▼                                    │
│    Technical    Astro       Electional    ← 3 специализированных      │
│      Team      Council        Agent          потока                   │
│         │            │            │                                  │
│         └────────────┼────────────┘                                  │
│                      ▼                                                │
│               Synthesis Agent                                         │
│                      │                                                │
│                      ▼                                                │
│              Final Recommendation                                     │
│                                                                       │
│   ┌─────────────────────────────────────────────────────────────┐     │
│   │              SHARED KNOWLEDGE BASE (RAG)                    │     │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐   │     │
│   │  │ Astrology/   │  │ Technical/  │  │ Market Data /   │   │     │
│   │  │ Vedic        │  │ Indicators   │  │ Trading Rules   │   │     │
│   │  └─────────────┘  └─────────────┘  └─────────────────┘   │     │
│   └─────────────────────────────────────────────────────────────┘     │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

## RAG Index Structure

```
knowledge/
├── chunks/                    # Source markdown files (Obsidian vault)
│   ├── astrology/
│   │   ├── nakshatras.md
│   │   ├── choghadiya.md
│   │   ├── muhurta.md
│   │   ├── western_dignities.md
│   │   └── election_rules.md
│   ├── technical/
│   │   ├── rsi_macd.md
│   │   ├── elliott_wave.md
│   │   └── gann_methods.md
│   └── trading/
│       ├── position_sizing.md
│       └── risk_management.md
├── indexes/                  # FAISS / ChromaDB indexes
│   ├── astrology.index
│   ├── technical.index
│   └── trading.index
└── rag_retriever.py         # Unified retrieval interface
```

## Agent Knowledge Access Pattern

Each agent:
1. Has its own `{agent_name}_instructions.md` (hardcoded in prompt)
2. Can retrieve knowledge via `retrieve_knowledge(query, domain=None)`
3. Must cite sources in responses

## Retrieval Flow

```
Agent Query
    │
    ▼
[Query Enhancement]  ← расширяет запрос через синонимы
    │
    ▼
[Vector Search]      ← FAISS в памяти или Chroma
    │
    ▼
[Re-ranking]         ← BM25 + semantic reranking
    │
    ▼
[Context Window]     ← топ-10 чанков → в контекст агента
    │
    ▼
Agent Response       ← всегда с цитированием
```

## Domains

| Domain | Agents | Index |
|--------|--------|-------|
| `astrology` | AstroCouncil, ElectionalAgent | `astrology.index` |
| `technical` | MarketAnalyst, WaveAgents | `technical.index` |
| `trading` | All agents | `trading.index` |
| `all` | Router, Synthesis | All indexes |
