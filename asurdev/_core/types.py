"""
Core types for asurdev Sentinel — DEPRECATED
============================================

This module is kept for backwards compatibility.
All types are now unified in agents/types.py.

Please import from agents.types instead:
    from agents.types import Signal, AgentResponse, TradingSignal
"""

# Re-export from unified types module
from agents.types import (
    Signal,
    AgentResponse,
    TradingSignal,
)

# Backwards compatibility aliases
SignalType = Signal
AgentResult = AgentResponse

__all__ = [
    "Signal",
    "AgentResponse", 
    "TradingSignal",
    "SignalType",  # backwards compat
    "AgentResult",  # backwards compat
]
