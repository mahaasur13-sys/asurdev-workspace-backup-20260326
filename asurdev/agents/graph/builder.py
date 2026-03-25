"""
LangGraph Builder — State Machine Construction
asurdev Sentinel v3.2

Builds the LangGraph state machine that orchestrates all agents.

Graph Flow:
    market → [bull, bear, astro, cycle] (parallel)
    [bull, bear, astro, cycle] → dow
    dow → [gann | andrews | synthesize] (conditional based on disagreement)
    [gann, andrews] → meridian
    meridian → synthesize → END
"""

from langgraph.graph import StateGraph, END
from ..state import SentinelState
from .nodes import (
    node_market,
    node_bull,
    node_bear,
    node_astro,
    node_cycle,
    node_dow,
    node_andrews,
    node_gann,
    node_meridian,
    node_synthesize,
)
from .routing import route_based_on_disagreement


def build_graph() -> StateGraph:
    """
    Build LangGraph state machine.
    
    Returns:
        Compiled StateGraph ready for execution
    """
    builder = StateGraph(SentinelState)
    
    # Node registry
    node_registry = {
        "market": node_market,
        "bull": node_bull,
        "bear": node_bear,
        "astro": node_astro,
        "cycle": node_cycle,
        "dow": node_dow,
        "andrews": node_andrews,
        "gann": node_gann,
        "meridian": node_meridian,
        "synthesize": node_synthesize,
    }
    
    # Register all nodes
    for name, node_fn in node_registry.items():
        builder.add_node(name, node_fn)
    
    # Entry point
    builder.set_entry_point("market")
    
    # Phase 1: Market → parallel agents
    builder.add_edge("market", "bull")
    builder.add_edge("market", "bear")
    builder.add_edge("market", "astro")
    builder.add_edge("market", "cycle")
    
    # Wait for parallel agents
    builder.add_edge(["bull", "bear", "astro", "cycle"], "dow")
    
    # Phase 2: Conditional routing for resolution
    builder.add_conditional_edges(
        "dow",
        route_based_on_disagreement,
        {
            "gann": "gann",
            "andrews": "andrews",
            "synthesize": "synthesize"
        }
    )
    
    # Merge paths back to meridian
    builder.add_edge("gann", "meridian")
    builder.add_edge("andrews", "meridian")
    
    # Phase 3: Final synthesis
    builder.add_edge("meridian", "synthesize")
    builder.add_edge("synthesize", END)
    
    return builder
