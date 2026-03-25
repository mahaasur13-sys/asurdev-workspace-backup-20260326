"""
Sentinel State — Multi-Agent AstroFin System.
Updated: 2026-03-24 — Adaptive RAG Router + Technical Node
"""

from typing import TypedDict, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


# =============================================================================
# TECHNICAL RESULT — Technical analysis output
# =============================================================================

class PatternMatch(BaseModel):
    """Detected chart pattern."""
    pattern_type: str  # "head_shoulders", "double_bottom", "triangle", etc.
    direction: str  # "bullish", "bearish", "neutral"
    timeframe: str
    confidence: float  # 0.0-1.0
    description: str


class TechnicalResult(BaseModel):
    """Technical analysis output from Technical Node."""
    # Price action
    current_price: Optional[float] = None
    price_change_pct: Optional[float] = None
    
    # Indicators
    rsi: Optional[float] = None  # 0-100
    macd: Optional[dict] = None  # {"macd": float, "signal": float, "histogram": float}
    ema_20: Optional[float] = None
    ema_50: Optional[float] = None
    ema_200: Optional[float] = None
    
    # Patterns
    detected_patterns: list[PatternMatch] = Field(default_factory=list)
    
    # Scores (0.0-1.0)
    bullish_score: float = 0.5
    bearish_score: float = 0.5
    
    # Confidence (0.0-1.0) — how confident is the technical analysis?
    confidence: float = 0.5
    
    # Feature vector for Chroma similarity search
    feature_vector: Optional[list[float]] = None
    
    # Raw data used
    timeframe: str = "4h"
    symbol: str = "BTC"
    
    # Human-readable summary
    summary: str = ""


# =============================================================================
# RETRIEVAL STATE — RAG pipeline
# =============================================================================

class RetrievedCase(BaseModel):
    """A similar historical case from Chroma."""
    case_id: str
    similarity_score: float  # 0.0-1.0, higher = more similar
    pattern_type: str
    symbol: str
    date: str
    outcome: str  # "price_rose_X%", "price_fell_X%", "consolidated"
    outcome_pct: Optional[float] = None
    holding_period_days: int
    text_description: str
    metadata: dict


class RetrievalState(BaseModel):
    """State for RAG retrieval pipeline."""
    retrieved_cases: list[RetrievedCase] = Field(default_factory=list)
    self_critique_score: Optional[float] = None  # 0.0-1.0
    self_critique_reasoning: str = ""
    is_rag_relevant: bool = False  # True if cases are relevant enough
    corrective_rag_iterations: int = 0
    max_corrective_rag: int = 2  # Max 2 retries
    final_confidence: Optional[float] = None  # Adjusted confidence after RAG
    retrieval_strategy: Optional[str] = None  # "standard" | "pattern_focused" | "regime_aware"
    adaptive_query: Optional[str] = None  # The query built by adaptive query builder


# =============================================================================
# MAIN AGENT STATE
# =============================================================================

class AgentState(TypedDict):
    """Main state passed through the multi-agent graph."""
    
    # Request
    symbol: str
    timeframe: str
    user_question: str
    
    # Astro (fetched early, used for stable caching)
    jd_ut: Optional[float]
    astro_data: Optional[dict]
    
    # Market Data
    market_data: Optional[dict]
    
    # Technical Analysis (NEW — replaces simple technical_indicators)
    technical_result: Optional[TechnicalResult]
    
    # Adaptive RAG Pipeline (NEW)
    retrieval_state: Optional[RetrievalState]
    
    # Flat RAG pipeline fields (mirrored from retrieval_state for graph visibility)
    retrieved_cases: list = []
    adjusted_confidence: Optional[float] = None
    retrieval_relevance: Optional[float] = None
    correction_count: int = 0
    
    # Retrieval history for adaptive router (tracks past RAG attempts)
    retrieval_history: list[dict]
    
    # Knowledge (from retrieve_knowledge tool)
    knowledge_context: Optional[dict]
    
    # Agent Opinions
    market_analyst_opinion: Optional[dict]
    bull_researcher_opinion: Optional[dict]
    bear_researcher_opinion: Optional[dict]
    muhurta_specialist_opinion: Optional[dict]
    synthesizer_opinion: Optional[dict]
    
    # Final
    final_vote: Optional[dict]
    
    # Graph internals
    messages: list
    errors: list
    
    # Routing
    next: Optional[str]


# =============================================================================
# TEAM STATE (for fan-out)
# =============================================================================

class TeamState(TypedDict):
    """Simplified state for fan-out to specialists."""
    symbol: str
    timeframe: str
    user_question: str
    jd_ut: Optional[float]
    market_data: Optional[dict]
    technical_result: Optional[TechnicalResult]
    retrieval_state: Optional[RetrievalState]
    astro_data: Optional[dict]
    knowledge_context: Optional[dict]
