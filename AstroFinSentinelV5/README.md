# AstroFin Sentinel v5

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

## RAG Knowledge System

Each agent accesses knowledge through `retrieve_knowledge(query, domain)`:

- `domain="astrology"` — Nakshatras, Choghadiya, Muhurta, Western dignities
- `domain="technical"` — Indicators, patterns, wave theory
- `domain="trading"` — Risk management, position sizing

Knowledge chunks live in `knowledge/chunks/`.

## Dependencies

```
langgraph>=0.0.55
langchain-core
langchain-openai
requests
```
