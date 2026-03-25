"""
LangGraph Module — State Machine Architecture
asurdev Sentinel v3.2
============================================

Builds and manages the LangGraph state machine that orchestrates
all agents.

Submodules:
- nodes.py: All agent node functions (node_market, node_astro, etc.)
- routing.py: Conditional routing logic
- builder.py: Graph construction

Usage:
    from agents.graph import build_graph, node_market
    
    graph = build_graph()
    app = graph.compile()
"""

from .nodes import (
    AgentNode,
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
from .builder import build_graph

__all__ = [
    # Nodes
    "AgentNode",
    "node_market",
    "node_bull",
    "node_bear",
    "node_astro",
    "node_cycle",
    "node_dow",
    "node_andrews",
    "node_gann",
    "node_meridian",
    "node_synthesize",
    # Routing
    "route_based_on_disagreement",
    # Builder
    "build_graph",
]
