"""
_core/ — LEGACY MODULE (DEPRECATED)
==================================

This module is kept for backwards compatibility ONLY.

All functionality has been migrated to agents/ package:

NEW LOCATION:
    from agents import Signal, AgentResponse, LangGraphOrchestrator
    from agents.memory import MemoryMiddleware
    from agents.graph import build_graph

MIGRATION GUIDE:
    OLD                         NEW
    ----                         ---
    from _core.types import ...  from agents.types import ...
    from _core.agents import ...  from agents._impl import ...
    from _core.api import app     from agents.langgraph_orchestrator import LangGraphOrchestrator

Please update your imports. This module will be removed in v4.0.
"""

import warnings
warnings.warn(
    "_core/ module is deprecated. Use agents/ instead. "
    "See _core/__init__.py for migration guide.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from new locations for backward compatibility
from agents.types import Signal, AgentResponse, TradingSignal
from agents.langgraph_orchestrator import LangGraphOrchestrator

__all__ = [
    "Signal",
    "AgentResponse", 
    "TradingSignal",
    "LangGraphOrchestrator",
]
