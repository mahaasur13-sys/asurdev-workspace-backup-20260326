# AstroFin Sentinel v5 — Project Memory

**Status:** ✅ Hybrid Multi-Factor Platform (2026-03-25)
**Architecture:** RAG-First + LangGraph + Multi-Agent + Hybrid Signal
**Pattern:** Internal Board of Directors (Совет Директоров)

---

## 2026 Hybrid Signal Architecture

```
╔══════════════════════════════════════════════════════════════════════════╗
║            ASTROFIN SENTINEL v5 — HYBRID SIGNAL ARCHITECTURE         ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                       ║
║   User Query ──► Router ──► Parallel Agent Council ──► Synthesis        ║
║                                    │                    │             ║
║         ┌──────────┬──────────────┬┴──────┬───────────┐  │             ║
║         ▼          ▼              ▼       ▼           ▼             ║
║    ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌────────┐ ┌──────────┐      ║
║    │FUNDAMENT│ │  MACRO   │ │ QUANT   │ │OPTIONS │ │SENTIMENT │      ║
║    │ 20%    │ │   15%    │ │  20%    │ │  15%   │ │   10%    │      ║
║    └─────────┘ └──────────┘ └─────────┘ └────────┘ └──────────┘      ║
║                           │                    │                        ║
║                           ▼                    ▼                        ║
║                    ┌──────────────────────────────┐                   ║
║                    │     SYNTHESIS AGENT (100%)    │                   ║
║                    │     AstroCouncil = Coordinator │                   ║
║                    └──────────────────────────────┘                   ║
║                                                                       ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

## Agent Board — Final Weights

| Агент | Вес | Ответственность |
|-------|-----|----------------|
| **FundamentalAgent** | **20%** | Фундаментальный анализ (P/E, MVRV, revenue growth, valuation) |
| **QuantAgent** | **20%** | ML-модели, бэктестирование, предсказание волатильности |
| **MacroAgent** | **15%** | Макроэкономика (VIX, DXY, Fed rates, геополитика) |
| **OptionsFlowAgent** | **15%** | Анализ опционного потока, unusual activity, gamma exposure |
| **SentimentAgent** | **10%** | Анализ новостей, Reddit, X, StockTwits |
| **TechnicalAgent** | **10%** | Технический анализ (RSI, MACD, Bollinger) — как фильтр |
| **BullResearcher** | **5%** | Бычий нарратив + сильные астрологические факторы |
| **BearResearcher** | **5%** | Медвежий нарратив + рисковые факторы |
| **ElectoralAgent** | *(astro)* | Muhurta timing — координация через AstroCouncil |
| **AstroCouncil** | *(координатор)* | Координация всех суб-агентов, финальный синтез |
| **ИТОГО** | **100%** | |

> **Примечание:** AstroCouncil — координатор, получает данные от Astro-суб-агентов (BradleyAgent, ElectoralAgent, TimeWindowAgent) и объединяет их в блок Astro. Всегда возвращает структурированный `AgentResponse`.

---

## Conflict Resolution

**Никогда не игнорировать ни один источник.**

| Конфликт | Правило |
|----------|---------|
| Astro ↔ Fundamental+Quant | Astro вес −30%, Fundamental +18%, Quant +12% |

Если астрология противоречит фундаменталу и quant — снижаем вес астрологии.

---

## Астрологический фактор в каждом агенте

Каждый агент использует `@require_ephemeris` декоратор и включает 15-30% астрологический бонус:

| Агент | Astro Weight |
|-------|-------------|
| FundamentalAgent | ~30% (Jupiter, Venus) |
| MacroAgent | ~20% (Saturn, Jupiter) |
| QuantAgent | ~20% (ephemeris-based) |
| OptionsFlowAgent | ~20% (Mercury, Venus, Jupiter) |
| SentimentAgent | ~20% (Moon, Venus) |
| TechnicalAgent | ~15% (Mars, Moon) |

---

## Agent Implementation Files

```
agents/
├── base_agent.py              ← BaseAgent (RAG-first, AgentResponse)
├── synthesis_agent.py          ← AstroCouncil (100% coordinator)
├── fundamental_agent.py        ← 20%
├── macro_agent.py             ← 15%
├── quant_agent.py             ← 20% (_impl/quant_agent.py)
├── options_flow_agent.py      ← 15%
├── sentiment_agent.py          ← 10%
├── technical_agent.py          ← 10%
├── bull_researcher.py         ← 5% (_impl/)
├── bear_researcher.py         ← 5% (_impl/)
├── astro_council_agent.py      ← Astro coordinator
├── electoral_agent.py          ← Muhurta
└── _impl/                     ← Other agents
    ├── bull_researcher.py
    ├── bear_researcher.py
    ├── cycle_agent.py
    ├── risk_agent.py
    ├── gann_agent.py
    ├── elliot_agent.py
    ├── bradley_agent.py
    ├── sentiment_agent.py
    ├── time_window_agent.py
    ├── fundamental_agent.py    ← (backup)
    ├── insider_agent.py
    ├── macro_agent.py          ← (backup)
    ├── quant_agent.py
    ├── options_flow_agent.py   ← (backup)
    └── ml_predictor_agent.py
```

---

## Data Sources

| Source | Purpose | API |
|--------|---------|-----|
| CoinGecko | Crypto metadata, prices | Free |
| Binance | OHLCV data | Free |
| Swiss Ephemeris | Planetary positions | License (sweph) |
| SEC EDGAR | 13F filings | Free |
| Fear & Greed Index | Sentiment | Free (alternative.me) |
| Yahoo Finance | VIX, DXY, Gold | Free |
| Polygon.io | Options flow (future) | Paid |
| Unusual Whales | Options flow (future) | Paid |

---

## Usage

```bash
cd /home/workspace/AstroFinSentinelV5
python -m orchestration.sentinel_v5 "Analyze BTC" BTCUSDT SWING
```

---

## TODO

- [x] Implement all agents with proper weights
- [x] Update SynthesisAgent with 2026 hybrid weights
- [x] Add FundamentalAgent, MacroAgent, QuantAgent, OptionsFlowAgent
- [x] Add SentimentAgent, TechnicalAgent, Bull/Bear Researchers
- [x] Add conflict resolution (Astro vs Fundamental+Quant)
- [ ] Connect real data APIs (Polygon, Unusual Whales, SEC EDGAR)
- [ ] Add Telegram bot for alerts
- [ ] Build RAG index (FAISS/Chroma)
- [ ] Add visualizations
