"""
Memory Module — asurdev Sentinel v3.2
=======================================

Persistent memory with RAG + Feedback Loop.

Submodules:
- manager.py: MemoryManager, SessionMemory
- chroma.py: ChromaMemory
- fuzzy.py: FuzzyMemory
- integration.py: MemoryMiddleware, MemoryAwareAgentNode

Usage:
    from agents.memory import MemoryMiddleware, MemoryManager
    
    mm = MemoryMiddleware()
    ctx = mm.get_context_for_agent("astro", "BTC")
"""

from .manager import MemoryManager, SessionMemory, MemoryEntry, MemoryScope
from .chroma import ChromaMemory
from .fuzzy import FuzzyMemory
from .integration import (
    MemoryMiddleware,
    MemoryAwareAgentNode,
    AgentMemoryContext,
    get_memory_weighted_synthesis,
)

# Legacy JSON-based RAG (from AstroFin Sentinel)
try:
    from .json_store import RAGMemory, get_memory, reset_memory
    _json_store_available = True
except ImportError:
    _json_store_available = False
    RAGMemory = None
    get_memory = None
    reset_memory = None

__all__ = [
    # Manager
    "MemoryManager",
    "SessionMemory", 
    "MemoryEntry",
    "MemoryScope",
    # Storage
    "ChromaMemory",
    # Adaptive weights
    "FuzzyMemory",
    # Integration
    "MemoryMiddleware",
    "MemoryAwareAgentNode",
    "AgentMemoryContext",
    "get_memory_weighted_synthesis",
    # Legacy JSON store (AstroFin Sentinel)
    "RAGMemory",
    "get_memory", 
    "reset_memory",
]
