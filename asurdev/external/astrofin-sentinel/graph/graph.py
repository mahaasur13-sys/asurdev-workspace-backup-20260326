"""
LangGraph definition for AstroFin Sentinel

This module creates and exports the main analysis graph
with proper routing and parallel execution.
"""

import asyncio
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import AnalysisState, QueryType
from .nodes import (
    supervisor_node,
    technical_node,
    fundamental_node,
    astrologer_node,
    quality_gate_node,
    synthesizer_node,
    memory_node,
    run_agents_parallel
)


def create_analysis_graph() -> StateGraph:
    """
    Create the main AstroFin Sentinel analysis graph.
    
    Graph Structure:
    
        [Supervisor] 
            │
            ▼
    ┌─────────────────────────────────────┐
    │     PARALLEL AGENTS (async)         │
    │  ┌─────────┐ ┌─────────┐ ┌────────┐ │
    │  │Technical│ │Fundament│ │ Astro  │ │
    │  │ Analyst │ │  Anal.  │ │ loger  │ │
    │  └────┬────┘ └────┬────┘ └───┬────┘ │
    └───────┼──────────┼──────────┼───────┘
            └──────────┴──────────┘
                      │
                      ▼
            [Quality Gate]
                  │
          ┌───────┴───────┐
          ▼               ▼
      [PASS]           [FAIL]
          │               │
          ▼               ▼
    [Synthesizer]    [End/Error]
          │
          ▼
      [Memory]
          │
          ▼
        [END]
    
    Returns:
        Compiled StateGraph ready for execution
    """
    
    # Create the graph
    graph = StateGraph(AnalysisState)
    
    # === NODES ===
    
    # 1. Supervisor (entry point)
    graph.add_node("supervisor", supervisor_node)
    
    # 2. Parallel agents - we use a custom compound node
    graph.add_node("parallel_agents", parallel_agents_node)
    
    # 3. Quality gate
    graph.add_node("quality_gate", quality_gate_node)
    
    # 4. Synthesizer
    graph.add_node("synthesizer", synthesizer_node)
    
    # 5. Memory (optional, can be skipped for quick analysis)
    graph.add_node("memory", memory_node)
    
    # === EDGES ===
    
    # Start from supervisor
    graph.set_entry_point("supervisor")
    
    # Supervisor routes to parallel agents
    graph.add_edge("supervisor", "parallel_agents")
    
    # Parallel agents feed into quality gate
    graph.add_edge("parallel_agents", "quality_gate")
    
    # Quality gate has conditional routing
    graph.add_conditional_edges(
        "quality_gate",
        route_after_quality,
        {
            "synthesizer": "synthesizer",
            "end": END
        }
    )
    
    # After synthesis, optionally store in memory
    graph.add_edge("synthesizer", "memory")
    
    # Memory always ends
    graph.add_edge("memory", END)
    
    return graph


async def parallel_agents_node(state: AnalysisState) -> AnalysisState:
    """
    Compound node that runs agents in parallel.
    
    This node determines which agents to run based on query_type
    and executes them concurrently using asyncio.
    """
    # Determine which agents to run
    agents_to_run = []
    
    # Technical is included in FULL_ANALYSIS, TECHNICAL_ONLY, QUICK_SCAN, and TECHNICAL_FUNDAMENTAL
    if state.query_type in [QueryType.FULL_ANALYSIS, QueryType.TECHNICAL_ONLY, QueryType.QUICK_SCAN, QueryType.TECHNICAL_FUNDAMENTAL]:
        if "technical" not in state.skip_agents:
            agents_to_run.append("technical")
    
    if state.query_type in [QueryType.FULL_ANALYSIS, QueryType.TECHNICAL_FUNDAMENTAL]:
        if "fundamental" not in state.skip_agents:
            agents_to_run.append("fundamental")
    
    if state.query_type == QueryType.FULL_ANALYSIS:
        if "astrologer" not in state.skip_agents:
            agents_to_run.append("astrologer")
    
    # Run agents in parallel
    updated_state = await run_agents_parallel(state, agents_to_run)
    
    return updated_state


def route_after_quality(state: AnalysisState) -> Literal["synthesizer", "end"]:
    """
    Route after quality gate based on whether quality passed.
    """
    if state.quality_passed:
        return "synthesizer"
    return "end"


# ============================================================================
# Graph compilation with checkpointer
# ============================================================================

def create_compiled_graph():
    """
    Create a compiled graph with memory checkpointing.
    
    This allows the graph to pause and resume, and maintains
    state between turns in a conversation.
    """
    graph = create_analysis_graph()
    
    # Use in-memory checkpointing
    checkpointer = MemorySaver()
    
    return graph.compile(checkpointer=checkpointer)


# ============================================================================
# Convenience functions
# ============================================================================

async def run_analysis(
    symbol: str,
    side: str = "buy",
    interval: str = "1h",
    birth_date: str = None,
    birth_time: str = None,
    weights: dict = None,
    session_id: str = None,
    skip_agents: list = None
) -> AnalysisState:
    """
    Run a complete analysis using the LangGraph.
    
    Args:
        symbol: Trading pair (e.g., "BTC/USDT")
        side: "buy" or "sell"
        interval: Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
        birth_date: Birth date for astrology (DD.MM.YYYY)
        birth_time: Birth time for astrology (HH:MM)
        weights: Custom weights for synthesis
        session_id: Session ID for memory context
        skip_agents: List of agents to skip (e.g., ["astrologer"])
        
    Returns:
        AnalysisState with complete analysis
    """
    import uuid
    
    # Create initial state
    state = AnalysisState(
        symbol=symbol,
        side=side,
        interval=interval,
        birth_date=birth_date,
        birth_time=birth_time,
        weights=weights or {
            "technical": 0.30,
            "fundamental": 0.30,
            "astrological": 0.40
        },
        session_id=session_id or str(uuid.uuid4())[:8],
        skip_agents=skip_agents or []
    )
    
    # Run the graph using ainvoke (returns final state)
    compiled = create_compiled_graph()
    
    config = {"configurable": {"thread_id": state.session_id}}
    
    # Use ainvoke for cleaner result handling
    result = await compiled.ainvoke(state, config=config)
    
    # ainvoke returns dict, convert back to AnalysisState
    if isinstance(result, dict):
        result = AnalysisState(**result)
    
    return result


# ============================================================================
# Sync wrapper for convenience
# ============================================================================

def run_analysis_sync(
    symbol: str,
    side: str = "buy",
    interval: str = "1h",
    birth_date: str = None,
    birth_time: str = None,
    weights: dict = None,
    session_id: str = None,
    skip_agents: list = None
) -> AnalysisState:
    """
    Synchronous wrapper for run_analysis.
    
    Use this for CLI or when you don't need async.
    """
    return asyncio.run(run_analysis(
        symbol=symbol,
        side=side,
        interval=interval,
        birth_date=birth_date,
        birth_time=birth_time,
        weights=weights,
        session_id=session_id,
        skip_agents=skip_agents
    ))
