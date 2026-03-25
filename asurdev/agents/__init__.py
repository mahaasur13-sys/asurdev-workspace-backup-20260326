"""
asurdev Sentinel — Agents Package v3.2
========================================

Unified exports for all agent types.

Usage:
    from agents import Signal, AgentResponse, LangGraphOrchestrator
    from agents.memory import MemoryMiddleware
    from agents.graph import build_graph
"""

# =============================================================================
# UNIFIED TYPES (Single Source of Truth)
# =============================================================================

from .types import Signal, AgentResponse, TradingSignal

# =============================================================================
# LLM FACTORY
# =============================================================================

from .llm_factory import (
    get_llm_config,
    create_llm_client,
    ANALYST_PROMPT,
    ASTROLOGER_PROMPT,
    SYNTHESIZER_PROMPT,
    RISK_MANAGER_PROMPT,
)

# =============================================================================
# STATE
# =============================================================================

from .state import SentinelState

# =============================================================================
# ORCHESTRATORS
# =============================================================================

from .langgraph_orchestrator import (
    LangGraphOrchestrator,
    MemoryEnabledOrchestrator,
)

# Legacy
from .orchestrator import Orchestrator, quick_analyze, AnalysisResult

# =============================================================================
# MEMORY MODULE
# =============================================================================

from .memory import (
    MemoryManager,
    MemoryMiddleware,
    SessionMemory,
    ChromaMemory,
    FuzzyMemory,
    MemoryAwareAgentNode,
    get_memory_weighted_synthesis,
)

# =============================================================================
# GRAPH MODULE
# =============================================================================

from .graph import (
    build_graph,
    route_based_on_disagreement,
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

__all__ = [
    # =============================================================================
    # Types
    # =============================================================================
    "Signal",
    "AgentResponse",
    "TradingSignal",
    "SentinelState",
    
    # =============================================================================
    # LLM Factory
    # =============================================================================
    "get_llm_config",
    "create_llm_client",
    "ANALYST_PROMPT",
    "ASTROLOGER_PROMPT",
    "SYNTHESIZER_PROMPT",
    "RISK_MANAGER_PROMPT",
    
    # =============================================================================
    # Orchestrators
    # =============================================================================
    "LangGraphOrchestrator",
    "MemoryEnabledOrchestrator",
    "Orchestrator",
    "quick_analyze",
    "AnalysisResult",
    
    # =============================================================================
    # Memory
    # =============================================================================
    "MemoryManager",
    "MemoryMiddleware",
    "SessionMemory",
    "ChromaMemory",
    "FuzzyMemory",
    "MemoryAwareAgentNode",
    "get_memory_weighted_synthesis",
    
    # =============================================================================
    # Graph
    # =============================================================================
    "build_graph",
    "route_based_on_disagreement",
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
]
