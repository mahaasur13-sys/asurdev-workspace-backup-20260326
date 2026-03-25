# LangGraph State — AstroFin Sentinel
---
version: "1.0.0"
last_updated: "2026-03-24"
langgraph_version: "0.2.x"
---

```python
"""
AstroFin Sentinel — LangGraph State
===================================
Централизованное определение состояния для LangGraph графа.

State использует TypedDict для максимальной типобезопасности
с LangChain + Pydantic моделями для complex полей.
"""

from __future__ import annotations
from typing import Annotated, Literal, Optional
from datetime import datetime

from pydantic import BaseModel, Field


# ─── Enums ──────────────────────────────────────────────

class Confidence(BaseModel):
    """Confidence levels."""
    value: Literal["HIGH", "MEDIUM", "LOW"]


class Action(BaseModel):
    """Trading actions."""
    value: Literal["BUY", "SELL", "HOLD"]


# ─── Raw Data Models ────────────────────────────────────

class RawMarketData(BaseModel):
    """OHLCV + indicators от MarketDataProvider."""
    symbol: str
    timeframe: str
    price: float
    volume_24h: float
    change_24h: float
    high_24h: float
    low_24h: float
    rsi: float = 50.0
    macd_signal: str = "neutral"  # bullish | bearish | neutral
    trend: str = "neutral"        # uptrend | downtrend | neutral
    support: float
    resistance: float
    raw_ohlcv: list = Field(default_factory=list)


class RawAstroData(BaseModel):
    """Astronomical data от EphemerisNode."""
    timestamp_utc: str
    latitude: float
    longitude: float
    moon_sign: str
    moon_degree: float
    moon_phase: str
    nakshatra: str
    yoga: str
    tithi: str
    karana: str
    choghadiya_type: str
    choghadiya_window_start: str
    choghadiya_window_end: str
    is_auspicious: bool
    raw: dict = Field(default_factory=dict)


# ─── Agent Results ───────────────────────────────────────

class AgentResult(BaseModel):
    """Стандартный результат любого агента."""
    agent_id: str
    agent_role: str
    status: Literal["success", "error", "skipped"]
    findings: dict
    narrative: str = ""
    confidence: Confidence
    action_recommendation: Action = Field(default_factory=Action(value="HOLD"))
    metadata: dict = Field(default_factory=dict)
    knowledge_sources: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


# ─── LangGraph State ─────────────────────────────────────

class SentinelState(BaseModel):
    """
    Центральное состояние графа.
    Каждый агент читает нужные поля и записывает свой результат.
    """

    # ── Запрос ──────────────────────────────────────────
    symbol: str = "BTCUSDT"
    timeframe: str = "1h"
    action_type: Action = Field(default_factory=Action(value="HOLD"))
    location: dict = Field(default_factory={"lat": 25.20, "lon": 55.27})  # Dubai default
    analysis_timestamp_utc: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat() + "Z"
    )

    # ── Raw Data (заполняется нодами) ───────────────────
    market: Optional[RawMarketData] = None
    astro: Optional[RawAstroData] = None

    # ── Agent Results (заполняются агентами) ────────────
    market_analysis: Optional[AgentResult] = None
    bull_case: Optional[AgentResult] = None
    bear_case: Optional[AgentResult] = None
    astro_analysis: Optional[AgentResult] = None
    muhurta_analysis: Optional[AgentResult] = None
    synthesis: Optional[AgentResult] = None

    # ── Graph Metadata ──────────────────────────────────
    messages: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    class Config:
        use_enum_values = False


# ─── Node Names ──────────────────────────────────────────

NODES = {
    "fetch_market": "fetch_market_data",
    "fetch_astro": "fetch_astro_data",
    "market_analyst": "market_analyst_node",
    "bull_researcher": "bull_researcher_node",
    "bear_researcher": "bear_researcher_node",
    "astro_specialist": "astro_specialist_node",
    "muhurta_specialist": "muhurta_specialist_node",
    "synthesizer": "synthesizer_node",
}

# ─── Graph Flow ──────────────────────────────────────────

GRAPH_FLOW = """
                        ┌─→ [bull_researcher] ─┐
[market_analyst] ───────┼─→ [bear_researcher]  ─┼──→ [astro_specialist] ──→ [synthesizer]
                        └─→ [market_analyst] ───┘              ↑
                                                              │
                                               [ephemeris_node] ← ← ← ←
                                               [muhurta_specialist] ──→ ┘
"""
```
