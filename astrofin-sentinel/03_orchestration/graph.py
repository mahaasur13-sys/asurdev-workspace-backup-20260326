# LangGraph Orchestration — AstroFin Sentinel
---
version: "1.0.0"
last_updated: "2026-03-24"
langgraph_version: "0.2.x"
---

```python
"""
AstroFin Sentinel — LangGraph Orchestration
===========================================
Мультиагентный граф с параллельными ветками и RAG.

Graph Flow:
┌─────────────┐
│  fetch_data │ (market + astro, parallel)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│market_analyst│
└──────┬──────┘
       │
       ▼
   ┌───────┐
   │PARALLEL│──→ bull_researcher
   │        │──→ bear_researcher
   └────┬───┘
        │
        ▼
┌───────────────┐
│astro_specialist│
└───────┬───────┘
        │
        ▼
┌───────────────┐
│muhurta_specialist│
└───────┬───────┘
        │
        ▼
┌─────────────┐
│ synthesizer │ (FINAL)
└─────────────┘
"""

from __future__ import annotations
import os
from typing import Literal

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

from orchestration.state import SentinelState, NODES


# ─── LLM Config ───────────────────────────────────────────

LLM = ChatAnthropic(
    model="claude-sonnet-4-20250514",
    anthropic_api_key=os.environ["ANTHROPIC_API_KEY"],
)

# Fallback для OpenAI
OPENAI_LLM = ChatOpenAI(
    model="gpt-4o",
    api_key=os.environ.get("OPENAI_API_KEY", ""),
)


# ─── Node Functions ──────────────────────────────────────

def fetch_market_data(state: SentinelState) -> SentinelState:
    """Нода загрузки рыночных данных."""
    from data_providers.market_data_provider import MarketDataProvider

    provider = MarketDataProvider()
    state.market = provider.get_market_data(
        symbol=state.symbol,
        timeframe=state.timeframe,
    )
    return state


def fetch_astro_data(state: SentinelState) -> SentinelState:
    """Нода загрузки астрологических данных."""
    from data_providers.ephemeris_node import EphemerisNode

    node = EphemerisNode()
    loc = state.location

    state.astro = node.get_astro_data(
        timestamp_utc=state.analysis_timestamp_utc,
        latitude=loc.get("lat", 25.20),
        longitude=loc.get("lon", 55.27),
    )
    return state


def market_analyst_node(state: SentinelState) -> SentinelState:
    """Market Analyst — технический анализ."""
    prompt = f"""
    Ты — Market Analyst. Проведи технический анализ для {state.symbol} ({state.timeframe}).

    Текущие данные:
    - Price: ${state.market.price}
    - RSI (14): {state.market.rsi:.1f}
    - MACD: {state.market.macd_signal}
    - Trend: {state.market.trend}
    - Support: ${state.market.support}
    - Resistance: ${state.market.resistance}
    - 24h Volume: ${state.market.volume_24h:,.0f}
    - 24h Change: {state.market.change_24h:+.2f}%

    Определи направление и ключевые уровни.
    Верни JSON: direction, trend, rsi, macd_signal, support, resistance
    """
    # LLM call → AgentResult
    # ... (полный код в agents/market_analyst.py)
    return state


def bull_researcher_node(state: SentinelState) -> SentinelState:
    """Bull Researcher — бычий сценарий (параллельно с bear)."""
    # ... (полный код в agents/bull_researcher.py)
    return state


def bear_researcher_node(state: SentinelState) -> SentinelState:
    """Bear Researcher — медвежий сценарий (параллельно с bull)."""
    # ... (полный код в agents/bear_researcher.py)
    return state


def astro_specialist_node(state: SentinelState) -> SentinelState:
    """Astro Specialist — астрологический анализ."""
    astro = state.astro
    prompt = f"""
    Ты — Astro Specialist. Проанализируй астрологическую карту для трейдинга.

    Moon Sign: {astro.moon_sign}
    Moon Degree: {astro.moon_degree:.1f}°
    Moon Phase: {astro.moon_phase}
    Nakshatra: {astro.nakshatra}
    Yoga: {astro.yoga}
    Choghadiya: {astro.choghadiya_type} ({astro.choghadiya_window_start}–{astro.choghadiya_window_end})
    Auspicious: {astro.is_auspicious}

    Оцени влияние на финансовые решения.
    """
    # ... (RAG call + LLM → AgentResult)
    return state


def muhurta_specialist_node(state: SentinelState) -> SentinelState:
    """Muhurta Specialist — выбор времени."""
    # ... (полный код в agents/muhurta_specialist.py)
    return state


def synthesizer_node(state: SentinelState) -> SentinelState:
    """Synthesizer — финальная рекомендация."""
    # ... (полный код в agents/synthesizer.py)
    return state


# ─── Graph Definition ────────────────────────────────────

def build_graph() -> StateGraph:
    """
    Собирает LangGraph.
    
    Параллелизация:
    - market_analyst запускает bull + bear одновременно
    - После parallel → astro → muhurta → synthesizer
    """

    builder = StateGraph(SentinelState)

    # ── Nodes ─────────────────────────────────────────────
    builder.add_node("fetch_market", fetch_market_data)
    builder.add_node("fetch_astro", fetch_astro_data)
    builder.add_node("market_analyst", market_analyst_node)
    builder.add_node("bull_researcher", bull_researcher_node)
    builder.add_node("bear_researcher", bear_researcher_node)
    builder.add_node("astro_specialist", astro_specialist_node)
    builder.add_node("muhurta_specialist", muhurta_specialist_node)
    builder.add_node("synthesizer", synthesizer_node)

    # ── Entry ─────────────────────────────────────────────
    builder.set_entry_point("fetch_market")

    # ── Data fetch (parallel) ──────────────────────────────
    builder.add_edge("fetch_market", "fetch_astro")
    builder.add_edge("fetch_astro", "market_analyst")

    # ── Parallel branch ────────────────────────────────────
    builder.add_node("parallel_agents", lambda s: s)  # pseudo-node для fan-out

    builder.add_edge("market_analyst", "parallel_agents")

    # Fan-out: bull + bear параллельно
    builder.add_node("bull_researcher", bull_researcher_node)
    builder.add_node("bear_researcher", bear_researcher_node)

    # После parallel agents → astro specialist
    builder.add_edge("bull_researcher", "astro_specialist")
    builder.add_edge("bear_researcher", "astro_specialist")

    # ── Astro + Muhurta chain ─────────────────────────────
    builder.add_edge("astro_specialist", "muhurta_specialist")
    builder.add_edge("muhurta_specialist", "synthesizer")
    builder.add_edge("synthesizer", END)

    return builder.compile()


# ─── Run ──────────────────────────────────────────────────

if __name__ == "__main__":
    graph = build_graph()

    initial_state = SentinelState(
        symbol="BTCUSDT",
        timeframe="1h",
        location={"lat": 25.20, "lon": 55.27},  # Dubai
    )

    result = graph.invoke(initial_state)

    print("=== FINAL RESULT ===")
    print(f"Action: {result.synthesis.action_recommendation}")
    print(f"Confidence: {result.synthesis.confidence}")
    print(result.synthesis.narrative)
```
