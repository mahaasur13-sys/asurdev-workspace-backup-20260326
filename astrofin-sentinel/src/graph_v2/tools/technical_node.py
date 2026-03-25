"""
Technical Node with Adaptive RAG Router.
Updated: 2026-03-24

Flow:
1. Calculate indicators + detect patterns → TechnicalResult
2. Adaptive Router decides: need_retrieval? → goto step 3
3. Retrieve similar cases from Chroma
4. Self-Critique: is_relevant?
   - If yes → goto bull/bear with adjusted confidence
   - If no → Corrective RAG (reformulate query, retry)
   - Max 2 retries, then proceed with original confidence
"""

from typing import Literal
from langchain_openai import ChatOpenAI
import os
import numpy as np

from src.graph_v2.state import AgentState, TechnicalResult, PatternMatch, RetrievalState
from src.graph_v2.tools.technical_kb import (
    build_feature_vector,
    build_text_description,
    retrieve_similar_cases,
    evaluate_retrieval_relevance,
    reformulate_query,
)


llm = ChatOpenAI(
    model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
    temperature=0.0
)


# =============================================================================
# TECHNICAL INDICATORS (Placeholder — replace with TA-Lib / pandas-ta)
# =============================================================================

def calculate_indicators(symbol: str, timeframe: str) -> dict:
    """
    Placeholder: Calculate technical indicators.
    Replace with real data from CoinGecko/CCXT + TA-Lib.
    
    Returns dict with: rsi, macd, ema_20, ema_50, ema_200, current_price, price_change_pct
    """
    # TODO: Integrate with real market data
    return {
        "rsi": 55.0,  # Placeholder
        "macd": {"macd": 0.0015, "signal": 0.0012, "histogram": 0.0003},
        "ema_20": 67450.0,
        "ema_50": 67200.0,
        "ema_200": 65000.0,
        "current_price": 67500.0,
        "price_change_pct": 1.5,
        "volume_24h": 25_000_000_000,
    }


def detect_patterns(indicators: dict, price_data: dict = None) -> list[PatternMatch]:
    """
    Detect chart patterns from indicators.
    Placeholder implementation.
    
    Returns list of PatternMatch objects.
    """
    patterns = []
    
    # Simple pattern detection (placeholder logic)
    rsi = indicators.get("rsi", 50)
    macd_hist = indicators.get("macd", {}).get("histogram", 0)
    
    # RSI-based pattern
    if rsi < 30:
        patterns.append(PatternMatch(
            pattern_type="oversold_reversal",
            direction="bullish",
            timeframe="4h",
            confidence=0.6,
            description=f"RSI at {rsi:.1f} indicates oversold conditions"
        ))
    elif rsi > 70:
        patterns.append(PatternMatch(
            pattern_type="overbought_reversal",
            direction="bearish",
            timeframe="4h",
            confidence=0.6,
            description=f"RSI at {rsi:.1f} indicates overbought conditions"
        ))
    
    # MACD divergence (simplified)
    if macd_hist > 0:
        patterns.append(PatternMatch(
            pattern_type="macd_bullish_cross",
            direction="bullish",
            timeframe="4h",
            confidence=0.55,
            description="MACD histogram positive, bullish momentum"
        ))
    
    return patterns


def calculate_scores(indicators: dict, patterns: list[PatternMatch]) -> tuple[float, float]:
    """
    Calculate bullish_score and bearish_score from 0.0 to 1.0.
    
    Returns (bullish_score, bearish_score)
    """
    bullish = 0.5
    bearish = 0.5
    
    # RSI component
    rsi = indicators.get("rsi", 50)
    if rsi < 30:
        bullish += 0.2
    elif rsi > 70:
        bearish += 0.2
    
    # MACD component
    macd_hist = indicators.get("macd", {}).get("histogram", 0)
    if macd_hist > 0:
        bullish += min(abs(macd_hist) * 10, 0.2)
    else:
        bearish += min(abs(macd_hist) * 10, 0.2)
    
    # Pattern component
    for pattern in patterns:
        if pattern.direction == "bullish":
            bullish += pattern.confidence * 0.1
        elif pattern.direction == "bearish":
            bearish += pattern.confidence * 0.1
    
    # Normalize to 0.0-1.0
    bullish = max(0.0, min(1.0, bullish))
    bearish = max(0.0, min(1.0, bearish))
    
    # Ensure they sum roughly to 1.0
    total = bullish + bearish
    if total > 0:
        scale = 1.0 / total
        bullish *= scale
        bearish *= scale
    
    return bullish, bearish


# =============================================================================
# TECHNICAL NODE
# =============================================================================

def technical_analysis_node(state: AgentState) -> AgentState:
    """
    Technical Analysis Node with Adaptive RAG Router.
    
    Flow:
    1. Calculate indicators + detect patterns
    2. Build feature vector
    3. ADAPTIVE ROUTER: need_retrieval?
       - YES → retrieve_similar_cases → self_critique
         - If relevant → proceed with adjusted confidence
         - If not → corrective_rag (max 2 iterations)
       - NO → proceed directly to bull/bear
    
    Output state updates:
    - technical_result: TechnicalResult with scores + patterns
    - retrieval_state: RetrievalState with RAG pipeline results
    """
    symbol = state.get("symbol", "BTC")
    timeframe = state.get("timeframe", "4h")
    
    # =========================================================================
    # STEP 1: Calculate Technical Indicators
    # =========================================================================
    indicators = calculate_indicators(symbol, timeframe)
    patterns = detect_patterns(indicators)
    bullish_score, bearish_score = calculate_scores(indicators, patterns)
    
    # =========================================================================
    # STEP 2: Build Technical Result
    # =========================================================================
    feature_vector = build_feature_vector({
        "rsi": indicators.get("rsi"),
        "macd": indicators.get("macd"),
        "ema_20": indicators.get("ema_20"),
        "ema_50": indicators.get("ema_50"),
        "ema_200": indicators.get("ema_200"),
        "price_change_pct": indicators.get("price_change_pct"),
        "detected_patterns": [p.model_dump() for p in patterns],
        "bullish_score": bullish_score,
        "bearish_score": bearish_score,
        "confidence": 0.6,  # Initial confidence before RAG
        "timeframe": timeframe,
        "symbol": symbol,
    })
    
    technical_result = TechnicalResult(
        current_price=indicators.get("current_price"),
        price_change_pct=indicators.get("price_change_pct"),
        rsi=indicators.get("rsi"),
        macd=indicators.get("macd"),
        ema_20=indicators.get("ema_20"),
        ema_50=indicators.get("ema_50"),
        ema_200=indicators.get("ema_200"),
        detected_patterns=patterns,
        bullish_score=bullish_score,
        bearish_score=bearish_score,
        confidence=0.6,  # Will be adjusted by RAG
        feature_vector=feature_vector,
        timeframe=timeframe,
        symbol=symbol,
        summary=build_text_description({
            "rsi": indicators.get("rsi"),
            "macd": indicators.get("macd"),
            "detected_patterns": [p.model_dump() for p in patterns],
            "bullish_score": bullish_score,
            "bearish_score": bearish_score,
            "price_change_pct": indicators.get("price_change_pct"),
        })
    )
    
    # =========================================================================
    # STEP 3: ADAPTIVE ROUTER — Need Retrieval?
    # =========================================================================
    # Decision logic: Retrieve if pattern confidence is medium (< 0.7)
    # or if scores are ambiguous (both near 0.5)
    
    need_retrieval = (
        technical_result.confidence < 0.7 or
        abs(technical_result.bullish_score - technical_result.bearish_score) < 0.2
    )
    
    retrieval_state = RetrievalState(
        retrieved_cases=[],
        corrective_rag_iterations=0,
        max_corrective_rag=2,
    )
    
    if not need_retrieval:
        # Direct route: go to bull/bear with current confidence
        retrieval_state.is_relevant = True
        retrieval_state.final_confidence = technical_result.confidence
        return {
            "technical_result": technical_result,
            "retrieval_state": retrieval_state,
            "messages": state.get("messages", []) + [
                {"role": "system", "content": f"Technical: {symbol} {timeframe}, no retrieval needed"}
            ]
        }
    
    # =========================================================================
    # STEP 4: Retrieve Similar Cases
    # =========================================================================
    try:
        retrieved_cases = retrieve_similar_cases(
            feature_vector=feature_vector,
            n_results=5,
            symbol_filter=symbol
        )
        retrieval_state.retrieved_cases = retrieved_cases
    except Exception as e:
        # Chroma might be empty or unavailable
        retrieved_cases = []
        retrieval_state.retrieved_cases = []
    
    # =========================================================================
    # STEP 5: Self-Critique
    # =========================================================================
    critique_result = evaluate_retrieval_relevance(
        technical_result=technical_result.model_dump(),
        retrieved_cases=retrieved_cases,
        llm=llm
    )
    
    retrieval_state.self_critique_score = critique_result["self_critique_score"]
    retrieval_state.self_critique_reasoning = critique_result["self_critique_reasoning"]
    
    # =========================================================================
    # STEP 6: Check Relevance or Corrective RAG
    # =========================================================================
    if critique_result["is_relevant"]:
        # Good retrieval — use adjusted confidence
        retrieval_state.is_relevant = True
        retrieval_state.final_confidence = critique_result["adjusted_confidence"]
        technical_result.confidence = critique_result["adjusted_confidence"]
    else:
        # Poor retrieval — try Corrective RAG (max 2 iterations)
        original_query = f"{symbol} {timeframe} technical analysis"
        
        while retrieval_state.corrective_rag_iterations < retrieval_state.max_corrective_rag:
            retrieval_state.corrective_rag_iterations += 1
            
            # Reformulate query
            reformulated = reformulate_query(
                original_query=original_query,
                technical_result=technical_result.model_dump(),
                failed_retrieval_reason=critique_result["self_critique_reasoning"],
                llm=llm
            )
            
            # Retry retrieval
            try:
                new_cases = retrieve_similar_cases(
                    feature_vector=feature_vector,
                    n_results=5,
                    symbol_filter=symbol
                )
                retrieval_state.retrieved_cases = new_cases
            except:
                new_cases = []
            
            # Re-evaluate
            new_critique = evaluate_retrieval_relevance(
                technical_result=technical_result.model_dump(),
                retrieved_cases=new_cases,
                llm=llm
            )
            
            if new_critique["is_relevant"]:
                retrieval_state.self_critique_score = new_critique["self_critique_score"]
                retrieval_state.self_critique_reasoning = new_critique["self_critique_reasoning"]
                retrieval_state.is_relevant = True
                retrieval_state.final_confidence = new_critique["adjusted_confidence"]
                technical_result.confidence = new_critique["adjusted_confidence"]
                break
            else:
                # Continue loop for another retry
                critique_result = new_critique
        
        # If still no relevant cases after max retries, proceed with penalty
        if not retrieval_state.is_relevant:
            retrieval_state.final_confidence = technical_result.confidence * 0.7
            technical_result.confidence *= 0.7
    
    # =========================================================================
    # STEP 7: Return updated state
    # =========================================================================
    return {
        "technical_result": technical_result,
        "retrieval_state": retrieval_state,
        "messages": state.get("messages", []) + [
            {"role": "system", "content": (
                f"Technical: {symbol} {timeframe}, "
                f"bullish={technical_result.bullish_score:.2f}, "
                f"bearish={technical_result.bearish_score:.2f}, "
                f"confidence={technical_result.confidence:.2f}, "
                f"retrieval={'YES' if need_retrieval else 'NO'}, "
                f"cases={len(retrieval_state.retrieved_cases)}"
            )}
        ]
    }


# =============================================================================
# ROUTER — Adaptive RAG decision
# =============================================================================

def adaptive_router_node(state: AgentState) -> Literal["direct", "retrieve_similar_cases"]:
    """
    Router node: decides whether to go direct to bull/bear
    or through the RAG pipeline.
    
    Routes:
    - "direct": Skip RAG, go straight to bull/bear specialists
    - "retrieve_similar_cases": Enter Adaptive RAG pipeline
    """
    technical_result = state.get("technical_result")
    
    if not technical_result:
        return "direct"
    
    # Decision: Retrieve if:
    # 1. Pattern confidence is medium
    # 2. Bull/Bear scores are ambiguous
    need_retrieval = (
        technical_result.confidence < 0.7 or
        abs(technical_result.bullish_score - technical_result.bearish_score) < 0.2
    )
    
    if need_retrieval:
        return "retrieve_similar_cases"
    else:
        return "direct"
