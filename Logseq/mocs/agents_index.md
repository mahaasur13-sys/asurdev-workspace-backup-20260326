---
type:: moc
id:: agents_index
tags:: [moc, agents, board-of-directors, astrofin]
created:: 2026-03-26
updated:: 2026-03-27

## AstroFin Sentinel V5 — Agent Board (Совет Директоров)

**Architecture:** RAG-First + LangGraph + Multi-Agent + Hybrid Signal  
**Pattern:** Internal Board of Directors (Совет Директоров)  
**ROMA Version:** v7.5 (2026-03-27)

---

## Major Agents (84%)

| Агент | Вес | Домен | Файл |
|-------|-----|-------|------|
| [[fundamental_agent]] | 20% | fundamental | `agents/_impl/fundamental_agent.py` |
| [[quant_agent]] | 20% | quant | `agents/_impl/quant_agent.py` |
| [[macro_agent]] | 15% | macro | `agents/_impl/macro_agent.py` |
| [[options_flow_agent]] | 15% | options | `agents/_impl/options_flow_agent.py` |
| [[sentiment_agent]] | 10% | sentiment | `agents/_impl/sentiment_agent.py` |
| [[electoral_agent]] | 10% | astrology | `agents/electoral_agent.py` |

---

## Technical Agents (10%)

| Агент | Вес | Домен | Файл |
|-------|-----|-------|------|
| [[technical_agent]] | 10% | technical | `agents/technical_agent.py` |
| [[bull_bear_researchers|BullResearcher]] | 5% | trading | `agents/_impl/bull_researcher.py` |
| [[bull_bear_researchers|BearResearcher]] | 5% | trading | `agents/_impl/bear_researcher.py` |

---

## Astro Agents (16%)

| Агент | Вес | Домен | Файл | Концепция |
|-------|-----|-------|------|---------|
| [[astro_agents|BradleyAgent]] | 3% | technical | `agents/_impl/bradley_agent.py` | [[bradley_siderograph]] |
| [[astro_agents|GannAgent]] | 3% | technical | `agents/_impl/gann_agent.py` | [[gann_theory]] |
| [[astro_agents|CycleAgent]] | 5% | technical | `agents/_impl/cycle_agent.py` | [[market_cycles]] |
| [[astro_agents|TimeWindowAgent]] | 2% | astrology | `agents/_impl/time_window_agent.py` | [[muhurta_trading]] |
| [[astro_agents|ElectoralAgent]] | 10% | astrology | `agents/electoral_agent.py` | [[muhurta_trading]] |
| [[astro_agents|AstroCouncil]] | — | coordinator | `agents/astro_council_agent.py` | — |

---

## Minor Agents

| Агент | Вес | Домен | Файл |
|-------|-----|-------|------|
| [[ml_predictor_agent]] | 10% | quant | `agents/_impl/ml_predictor_agent.py` |
| [[insider_agent]] | 8% | fundamental | `agents/_impl/insider_agent.py` |
| [[risk_agent]] | 5% | trading | `agents/_impl/risk_agent.py` |
| [[elliot_agent]] | 3% | technical | `agents/_impl/elliot_agent.py` |

---

## Coordinator

| Агент | Роль |
|-------|------|
| [[synthesis_agent]] | Финальный синтез всех сигналов (100%) |
| [[market_analyst]] | Анализ рыночной структуры |

---

## Architecture Diagram

```
User Query ──► Router ──► Technical Flow ──►
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
              MarketAnalyst BullResearcher BearResearcher
                                │
                    ◄───────────────────────────►
                                │
                    ◄──────── Astro Council ─────►
                    │
         ┌──────────┼──────────┬──────────┐
         ▼          ▼          ▼          ▼
   BradleyAgent GannAgent CycleAgent ElectoralAgent
         │          │          │          │
         └──────────┴──────────┴──────────┘
                                │
                    ◄───────────────────────────►
                                │
                    ◄───── Synthesis Agent ──────►
                                │
                            FINAL SIGNAL
```

---

## Key Principles

1. **Взвешивание:** 100% распределено между агентами
2. **AstroCouncil** — координатор, не голосует напрямую
3. **Conflict Resolution:** Astro против Fundamental+Quant → Astro −30%
4. **Thompson Sampling:** динамический отбор агентов на основе Bayesian beliefs
5. **EC-01 (Hubris Cap):** ограничение уверенности переобученных агентов (⚠️ not implemented)

---

## Related MOCs

- [[methods_index]] — методы (volatility, Thompson, ephemeris)
- [[concepts_index]] — концепции (Bradley, Gann, Elliott, Muhurta)
