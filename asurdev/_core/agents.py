"""
Core agents module — LEGACY WRAPPER
===================================

This module is kept for backwards compatibility.
All types have been moved to agents/types.py

New code should import from:
    from agents.types import Signal, AgentResponse, TradingSignal
    from agents.signal import Signal
    from agents._impl.base_agent import AgentResponse
"""

# Re-export unified types
from agents.types import Signal, AgentResponse, TradingSignal, SignalType, AgentResult

# Keep legacy AgentResult as alias
AgentResult = AgentResponse

__all__ = [
    "Signal",
    "AgentResponse", 
    "TradingSignal",
    "SignalType",
    "AgentResult",  # Legacy alias
]

# ============================================================================
# LEGACY STANDALONE FUNCTIONS — DEPRECATED
# ============================================================================
# 
# These functions have been moved to their respective agent modules:
# 
# OLD LOCATION              → NEW LOCATION
# ----------------------------------------------------------------
# analyze_market()          → agents._impl.market_analyst
# analyze_dow()             → agents._impl.dow_agent
# analyze_andrews()         → agents._impl.andrews_agent  
# analyze_gann()            → agents._impl.gann_agent
# analyze_astrology()       → agents._impl.astro_council
# synthesize_signals()      → agents._impl.synthesizer
#
# If you need these, import from the new locations:
# 
#   from agents._impl.market_analyst import MarketAnalyst
#   from agents._impl.dow_agent import DowTheoryAgent
#   etc.
#
# Or use the LangGraph orchestrator for full analysis:
#
#   from agents.langgraph_orchestrator import LangGraphOrchestrator
#   orchestrator = LangGraphOrchestrator()
#   result = await orchestrator.analyze("BTC")
#
# ============================================================================
