"""
Technical Knowledge Base — Chroma Vector Store for Historical Cases.
Updated: 2026-03-24 — Adaptive RAG support

Each document contains:
- embedding: vector of technical features (RSI, MACD, pattern_type, timeframe, trend_slope)
- metadata: symbol, date, pattern, outcome, outcome_pct, holding_period_days
- text: human-readable case description
"""

import chromadb
from chromadb.config import Settings
import hashlib
import os
from typing import Optional
import numpy as np


# =============================================================================
# FEATURE VECTOR BUILDER
# =============================================================================

def build_feature_vector(technical_result: dict) -> list[float]:
    """
    Build a feature vector from technical analysis results.
    
    Vector dimensions (13 features):
    1. rsi_normalized (0.0-1.0 from 0-100)
    2. macd_histogram_sign (-1 to 1)
    3. macd_histogram_magnitude (0-1, normalized)
    4. ema_20_vs_50 (1 if ema20 > ema50 else 0)
    5. ema_50_vs_200 (1 if ema50 > ema200 else 0)
    6. price_momentum (normalized % change)
    7. pattern_bullish_score (0.0-1.0)
    8. pattern_bearish_score (0.0-1.0)
    9. pattern_confidence (0.0-1.0)
    10. timeframe_weight (0.2 for 1h, 0.4 for 4h, 0.6 for 1d, 0.8 for 1w)
    11. volume_confirmation (0.0-1.0)
    12. support_resistance_proximity (0.0-1.0)
    13. trend_strength (-1 to 1)
    
    Returns:
        list[float]: 13-dimensional feature vector
    """
    if not technical_result:
        return [0.5] * 13
    
    vec = []
    
    # 1. RSI normalized
    rsi = technical_result.get("rsi", 50)
    vec.append(rsi / 100.0)
    
    # 2-3. MACD histogram
    macd = technical_result.get("macd", {})
    histogram = macd.get("histogram", 0)
    vec.append(np.tanh(histogram))  # -1 to 1
    vec.append(min(abs(histogram) / 10.0, 1.0))  # magnitude 0-1
    
    # 4. EMA crossover
    ema20 = technical_result.get("ema_20", 0)
    ema50 = technical_result.get("ema_50", 0)
    ema200 = technical_result.get("ema_200", 0)
    vec.append(1.0 if ema20 > ema50 else 0.0)
    vec.append(1.0 if ema50 > ema200 else 0.0)
    
    # 6. Price momentum
    price_change = technical_result.get("price_change_pct", 0)
    vec.append(np.tanh(price_change / 10.0))  # normalize
    
    # 7-9. Pattern scores
    patterns = technical_result.get("detected_patterns", [])
    bullish = technical_result.get("bullish_score", 0.5)
    bearish = technical_result.get("bearish_score", 0.5)
    confidence = technical_result.get("confidence", 0.5)
    vec.append(bullish)
    vec.append(bearish)
    vec.append(confidence)
    
    # 10. Timeframe weight
    tf_map = {"1h": 0.2, "4h": 0.4, "1d": 0.6, "1w": 0.8, "1M": 1.0}
    tf = technical_result.get("timeframe", "4h")
    vec.append(tf_map.get(tf, 0.4))
    
    # 11-13. Default values (would be enhanced with real data)
    vec.extend([0.5, 0.5, 0.0])
    
    return vec


def build_text_description(technical_result: dict) -> str:
    """Build human-readable text from technical result for Chroma."""
    parts = []
    
    if technical_result.get("rsi"):
        rsi = technical_result["rsi"]
        rsi_state = "overbought" if rsi > 70 else "oversold" if rsi < 30 else "neutral"
        parts.append(f"RSI={rsi:.1f} ({rsi_state})")
    
    if technical_result.get("macd"):
        macd = technical_result["macd"]
        hist = macd.get("histogram", 0)
        direction = "bullish" if hist > 0 else "bearish"
        parts.append(f"MACD histogram={hist:.4f} ({direction})")
    
    if technical_result.get("detected_patterns"):
        patterns = [p.get("pattern_type", "unknown") for p in technical_result["detected_patterns"]]
        parts.append(f"Patterns: {', '.join(patterns)}")
    
    parts.append(f"Bullish score: {technical_result.get('bullish_score', 0.5):.2f}")
    parts.append(f"Bearish score: {technical_result.get('bearish_score', 0.5):.2f}")
    
    return "; ".join(parts) if parts else "No technical details"


# =============================================================================
# CHROMA COLLECTION
# =============================================================================

_chroma_client = None
_collection = None


def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", "/tmp/astrofin_chroma")
        _chroma_client = chromadb.PersistentClient(
            path=persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
    return _chroma_client


def get_technical_collection():
    """Get or create the technical cases collection."""
    global _collection
    if _collection is None:
        client = get_chroma_client()
        _collection = client.get_or_create_collection(
            name="technical_cases",
            metadata={"description": "Historical technical patterns and outcomes"}
        )
    return _collection


# =============================================================================
# RETRIEVAL
# =============================================================================

def retrieve_similar_cases(
    feature_vector: list[float],
    n_results: int = 5,
    symbol_filter: Optional[str] = None
) -> list[dict]:
    """
    Retrieve similar historical cases from Chroma.
    
    Args:
        feature_vector: 13-dim feature vector from build_feature_vector()
        n_results: Number of similar cases to return
        symbol_filter: Optional symbol to filter by
    
    Returns:
        list of RetrievedCase-like dicts with similarity scores
    """
    collection = get_technical_collection()
    
    # Query Chroma
    results = collection.query(
        query_embeddings=[feature_vector],
        n_results=n_results,
        include=["metadatas", "documents", "distances"]
    )
    
    cases = []
    if results and results.get("ids"):
        ids = results["ids"][0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        documents = results.get("documents", [[]])[0]
        
        for i, case_id in enumerate(ids):
            # Convert distance to similarity (Chroma uses L2, 0 = identical)
            similarity = 1.0 / (1.0 + distances[i])
            
            case = {
                "case_id": case_id,
                "similarity_score": round(similarity, 4),
                "pattern_type": metadatas[i].get("pattern_type", "unknown"),
                "symbol": metadatas[i].get("symbol", ""),
                "date": metadatas[i].get("date", ""),
                "outcome": metadatas[i].get("outcome", ""),
                "outcome_pct": metadatas[i].get("outcome_pct"),
                "holding_period_days": metadatas[i].get("holding_period_days", 7),
                "text_description": documents[i] if i < len(documents) else "",
                "metadata": metadatas[i]
            }
            cases.append(case)
    
    return cases


def add_technical_case(
    feature_vector: list[float],
    pattern_type: str,
    symbol: str,
    date: str,
    outcome: str,
    outcome_pct: Optional[float],
    holding_period_days: int,
    text_description: str,
    additional_metadata: Optional[dict] = None
) -> str:
    """
    Add a historical technical case to the knowledge base.
    
    Args:
        feature_vector: 13-dim feature vector
        pattern_type: Type of pattern (head_shoulders, double_bottom, etc.)
        symbol: Trading symbol (BTC, ETH, etc.)
        date: Date string (YYYY-MM-DD)
        outcome: "price_rose_X%" or "price_fell_X%"
        outcome_pct: Numeric percentage
        holding_period_days: Days the position was held
        text_description: Human-readable description
        additional_metadata: Extra metadata fields
    
    Returns:
        case_id of inserted document
    """
    collection = get_technical_collection()
    
    # Generate deterministic ID
    hash_input = f"{symbol}:{date}:{pattern_type}:{outcome}"
    case_id = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    metadata = {
        "pattern_type": pattern_type,
        "symbol": symbol,
        "date": date,
        "outcome": outcome,
        "outcome_pct": outcome_pct,
        "holding_period_days": holding_period_days,
        **(additional_metadata or {})
    }
    
    collection.add(
        ids=[case_id],
        embeddings=[feature_vector],
        metadatas=[metadata],
        documents=[text_description]
    )
    
    return case_id
# =============================================================================
# SELF-CRITIQUE — LLM-based relevance evaluation (Ollama)
# =============================================================================

def evaluate_retrieval_relevance(
    technical_result: dict,
    retrieved_cases: list[dict],
    llm=None,
) -> dict:
    """
    Self-critique: Evaluate if retrieved cases are relevant to current situation.
    Uses Ollama (from src.llm.ollama_client) instead of LangChain OpenAI.

    Returns:
        dict with:
        - is_relevant: bool
        - self_critique_score: float 0.0-1.0
        - self_critique_reasoning: str
        - adjusted_confidence: float
    """
    from src.llm.ollama_client import get_default_llm

    if llm is None:
        llm = get_default_llm()

    if not retrieved_cases:
        return {
            "is_relevant": False,
            "self_critique_score": 0.0,
            "self_critique_reasoning": "No similar cases found in knowledge base.",
            "adjusted_confidence": technical_result.get("confidence", 0.5) * 0.8,
        }

    cases_text = "\n".join([
        f"- {c.get('pattern_type', 'unknown')} on {c.get('symbol', '')} ({c.get('date', '')}): "
        f"{c.get('outcome', '')} (similarity={c.get('similarity_score', 0):.3f})"
        for c in retrieved_cases[:3]
    ])

    prompt = f"""You are evaluating whether historical cases are relevant to a current trading situation.

CURRENT TECHNICAL ANALYSIS:
{build_text_description(technical_result)}

RETRIEVED SIMILAR CASES:
{cases_text}

Evaluate:
1. Are these cases similar enough to inform the current analysis?
2. How much should we adjust confidence based on historical precedent?
3. Are outcomes consistently bullish/bearish or mixed?

Respond in format:
RELEVANCE_SCORE: 0.0-1.0
REASONING: 2-3 sentences
ADJUSTED_CONFIDENCE: 0.0-1.0
"""

    result = llm.invoke(prompt)
    content = result.content if hasattr(result, "content") else str(result)

    score, reasoning, adjusted = 0.5, "", technical_result.get("confidence", 0.5)

    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("RELEVANCE_SCORE:"):
            try:
                score = float(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        elif line.startswith("REASONING:"):
            reasoning = line.split(":", 1)[1].strip()
        elif line.startswith("ADJUSTED_CONFIDENCE:"):
            try:
                adjusted = float(line.split(":", 1)[1].strip())
            except ValueError:
                pass

    is_relevant = score >= 0.4

    return {
        "is_relevant": is_relevant,
        "self_critique_score": score,
        "self_critique_reasoning": reasoning,
        "adjusted_confidence": adjusted if is_relevant else technical_result.get("confidence", 0.5) * 0.7,
    }


# =============================================================================
# CORRECTIVE RAG — Reformulate query and retry (Ollama)
# =============================================================================

def reformulate_query(
    original_query: str,
    technical_result: dict,
    failed_retrieval_reason: str,
    llm=None,
) -> str:
    """
    Reformulate query when initial retrieval failed or was irrelevant.
    Uses Ollama (from src.llm.ollama_client) instead of LangChain OpenAI.
    """
    from src.llm.ollama_client import get_default_llm

    if llm is None:
        llm = get_default_llm()

    prompt = f"""Reformulate this trading query to find more relevant historical cases.

ORIGINAL QUERY: {original_query}

CURRENT TECHNICAL CONTEXT:
{build_text_description(technical_result)}

WHY PREVIOUS RETRIEVAL FAILED:
{failed_retrieval_reason}

Suggest a more specific query that:
1. Adds relevant context about the current market regime (trending, ranging, volatile)
2. Specifies the exact pattern type if detected
3. Uses more precise technical terminology

Return only the reformulated query, nothing else.
"""

    result = llm.invoke(prompt)
    content = result.content if hasattr(result, "content") else str(result)

    for line in content.split("\n"):
        line = line.strip()
        if line and not line.startswith("```") and len(line) > 10:
            return line

    return original_query




# =============================================================================
# ADAPTIVE ROUTER — Decide whether to use RAG or skip to specialists
# =============================================================================

# Rare patterns that ALWAYS trigger RAG (high conviction, need historical confirmation)
RARE_PATTERNS = frozenset({
    "three_indians",           # Три индейца / Three Indians
    "head_and_shoulders",     # Голова и плечи
    "inverse_head_and_shoulders",  # Перевёрнутая голова и плечи
    "double_top",              # Двойная вершина
    "double_bottom",           # Двойное дно
    "triple_top",              # Тройная вершина
    "triple_bottom",           # Тройное дно
    "cup_and_handle",          # Чашка с ручкой
    "ascending_triangle",      # Восходящий треугольник
    "descending_triangle",     # Нисходящий треугольник
    "symmetrical_triangle",    # Симметричный треугольник
    "bull_flag",               # Бычий флаг
    "bear_flag",               # Медвежий флаг
    "pennant",                 # Вымпел
    "wedge_reversal",          # Клин разворот
    "dead_cross",              # Мёртвый крест (MA death cross)
    "golden_cross",            # Золотой крест (MA golden cross)
    "macd_divergence",         # MACD дивергенция
    "rsi_divergence",          # RSI дивергенция
    "volume_climax",           # Объёмный climax
})

# Low-confidence threshold — skip RAG, rely on specialists
LOW_CONFIDENCE_THRESHOLD = 0.35

# High-confidence threshold — skip RAG, use technical directly
HIGH_CONFIDENCE_THRESHOLD = 0.82


def should_skip_rag(technical_result: dict, retrieval_history: list[dict] = None) -> tuple[bool, str]:
    """
    Decide whether to skip RAG retrieval and go directly to specialists.
    
    Args:
        technical_result: Current technical analysis result
        retrieval_history: List of past retrieval attempts with their outcomes
                          Each dict: {"query": str, "relevance_score": float, "adjusted_confidence": float}
    
    Returns:
        tuple[bool, str]: (skip_rag: bool, reason: str)
    
    Decision Logic:
        1. High confidence (>= 0.82) → SKIP RAG (technical is sufficient)
        2. Low confidence (<= 0.35) → SKIP RAG (RAG unlikely to help)
        3. Rare pattern detected → USE RAG (historical confirmation needed)
        4. Past RAG was impactful (adjusted confidence delta > 0.1) → USE RAG
        5. No clear signal → SKIP RAG (trust specialists)
    """
    confidence = technical_result.get("confidence", 0.5)
    detected_patterns = technical_result.get("detected_patterns", [])
    
    # Criterion 1: High confidence — skip RAG
    if confidence >= HIGH_CONFIDENCE_THRESHOLD:
        return True, f"High technical confidence ({confidence:.2f} >= {HIGH_CONFIDENCE_THRESHOLD})"
    
    # Criterion 2: Low confidence — skip RAG (diminishing returns)
    if confidence <= LOW_CONFIDENCE_THRESHOLD:
        return True, f"Low technical confidence ({confidence:.2f} <= {LOW_CONFIDENCE_THRESHOLD}) — specialists will handle"
    
    # Criterion 3: Rare pattern detected — MUST use RAG
    for pattern in detected_patterns:
        pattern_type = pattern.get("pattern_type", "").lower()
        if pattern_type in RARE_PATTERNS:
            return False, f"Rare pattern detected: {pattern_type} — require historical confirmation"
    
    # Criterion 4: Past RAG was impactful — use RAG again
    if retrieval_history:
        for attempt in retrieval_history[-3:]:  # Check last 3 attempts
            relevance = attempt.get("relevance_score", 0)
            adjusted = attempt.get("adjusted_confidence", confidence)
            delta = abs(adjusted - confidence)
            
            # If RAG meaningfully adjusted confidence
            if delta > 0.1 and relevance >= 0.5:
                return False, f"Past RAG impactful (delta={delta:.3f}, relevance={relevance:.2f}) — retry"
    
    # Default: Skip RAG, let specialists handle
    return True, f"No strong RAG signal — confidence={confidence:.2f}, patterns={len(detected_patterns)}"


def get_rag_strategy(technical_result: dict) -> str:
    """
    Determine which RAG strategy to use if RAG is triggered.
    
    Returns:
        str: "standard" | "pattern_focused" | "regime_aware"
    """
    confidence = technical_result.get("confidence", 0.5)
    detected_patterns = technical_result.get("detected_patterns", [])
    rsi = technical_result.get("rsi", 50)
    
    if confidence < 0.5 and not detected_patterns:
        return "standard"
    if detected_patterns:
        return "pattern_focused"
    if rsi < 35 or rsi > 65:
        return "regime_aware"
    return "standard"


def build_adaptive_query(technical_result: dict, strategy: str) -> str:
    """
    Build optimized query based on strategy and technical context.
    """
    symbol = technical_result.get("symbol", "UNKNOWN")
    timeframe = technical_result.get("timeframe", "4h")
    confidence = technical_result.get("confidence", 0.5)
    detected_patterns = technical_result.get("detected_patterns", [])
    rsi = technical_result.get("rsi", 50)
    
    base_query = f"{symbol} {timeframe}"
    
    if strategy == "pattern_focused" and detected_patterns:
        pattern_names = [p.get("pattern_type", "") for p in detected_patterns]
        pattern_str = ", ".join(pattern_names)
        direction = detected_patterns[0].get("direction", "neutral")
        return f"{base_query} {pattern_str} {direction} pattern historical outcomes"
    
    elif strategy == "regime_aware":
        regime = "oversold" if rsi < 35 else "overbought" if rsi > 65 else "neutral"
        return f"{base_query} {regime} RSI market regime historical performance"
    
    else:  # standard
        return f"{base_query} technical analysis historical accuracy"
