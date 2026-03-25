# Knowledge Base Changelog
---
version: "1.0.0"
last_updated: "2026-03-24"
maintained_by: asurdev
---

## Changelog

### 2026-03-24 — Initial Commit

#### Added
- `01_agents/market_analyst.md` — Technical analysis agent spec
- `01_agents/bull_researcher.md` — Bullish scenario agent spec  
- `01_agents/bear_researcher.md` — Bearish scenario agent spec
- `01_agents/astro_specialist.md` — Vedic astrology agent spec
- `01_agents/muhurta_specialist.md` — Timing specialist agent spec
- `01_agents/synthesizer.md` — Final synthesis agent spec

#### Architecture Notes
- Agents: market_analyst → [bull_researcher, bear_researcher] (parallel) → astro_specialist → synthesizer
- RAG: keyword + semantic hybrid search with agent_role / topic filters
- Weights: Technical 70%, Astro 30%
- Confidence: HIGH when tech+astro sync + |score| > 0.5

#### Next Steps
- [ ] Add planet_aspects.md to 02_knowledge
- [ ] Add nakshatra_trading.md to 02_knowledge
- [ ] Add choghadiya_table.md to 02_knowledge
- [ ] Implement LangGraph orchestration in 03_orchestration/
- [ ] Add vector DB integration (Chroma/FAISS)
