"""
Memory Manager — Session + Short-term Memory
asurdev Sentinel v3.2
"""

from __future__ import annotations
import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

from .chroma import ChromaMemory
from .fuzzy import FuzzyMemory


class MemoryScope(Enum):
    """Memory scope/temporal relevance."""
    SHORT = "short"      # Very short-term (within analysis)
    SESSION = "session"  # Current analysis session
    LONG = "long"        # Persistent across sessions


@dataclass
class MemoryEntry:
    """Single memory entry."""
    id: str
    scope: MemoryScope
    agent: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "scope": self.scope.value,
            "agent": self.agent,
            "content": self.content,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None
        }


class SessionMemory:
    """
    In-memory session storage for current analysis.
    
    Stores recent agent responses and context within a single
    analysis session for fast access.
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.entries: List[MemoryEntry] = []
        self.symbol: Optional[str] = None
        self.action: Optional[str] = None
        self.created_at = datetime.now()
    
    def add(
        self,
        agent: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        scope: MemoryScope = MemoryScope.SESSION,
    ) -> MemoryEntry:
        """Add entry to session memory."""
        entry_id = hashlib.sha256(
            f"{self.session_id}{agent}{content[:100]}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        entry = MemoryEntry(
            id=entry_id,
            scope=scope,
            agent=agent,
            content=content,
            metadata=metadata or {},
        )
        self.entries.append(entry)
        return entry
    
    def get_recent(self, n: int = 5, scope: Optional[MemoryScope] = None) -> List[MemoryEntry]:
        """Get most recent entries."""
        entries = self.entries
        if scope:
            entries = [e for e in entries if e.scope == scope]
        return sorted(entries, key=lambda e: e.created_at, reverse=True)[:n]
    
    def get_for_agent(self, agent: str, limit: int = 3) -> List[MemoryEntry]:
        """Get recent entries for specific agent."""
        agent_entries = [e for e in self.entries if e.agent == agent]
        return sorted(agent_entries, key=lambda e: e.created_at, reverse=True)[:limit]
    
    def get_context_string(self, max_entries: int = 10) -> str:
        """Format session memory as string for LLM context."""
        recent = self.get_recent(max_entries)
        if not recent:
            return ""
        
        lines = ["[Previous Analysis Context]"]
        for entry in reversed(recent):
            lines.append(f"- {entry.agent}: {entry.content[:200]}")
        return "\n".join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "symbol": self.symbol,
            "action": self.action,
            "entries": [e.to_dict() for e in self.entries],
            "created_at": self.created_at.isoformat(),
        }


class MemoryManager:
    """
    Unified memory management interface.
    
    Coordinates:
    - SessionMemory (in-memory, fast)
    - ChromaMemory (persistent, RAG-enabled)
    - FuzzyMemory (adaptive weights)
    
    Usage:
        mm = MemoryManager()
        mm.start_session("btc_001", "BTC", "hold")
        mm.store_analysis(...)
    """
    
    def __init__(self, persist_dir: str = "./data/chroma_db", enable_rag: bool = True):
        self.session: Optional[SessionMemory] = None
        self.chroma: Optional[ChromaMemory] = None
        self.fuzzy: Optional[FuzzyMemory] = None
        
        if enable_rag:
            self.chroma = ChromaMemory(persist_dir)
            self.fuzzy = FuzzyMemory(self.chroma)
    
    def start_session(self, session_id: str, symbol: str, action: str) -> SessionMemory:
        """Start a new analysis session."""
        self.session = SessionMemory(session_id)
        self.session.symbol = symbol
        self.session.action = action
        return self.session
    
    def store_analysis(
        self,
        symbol: str,
        agent: str,
        signal: str,
        confidence: float,
        reasoning: str,
        market_state: Dict[str, Any],
    ) -> Optional[str]:
        """Store analysis to ChromaDB."""
        if not self.chroma or not self.session:
            return None
        
        return self.chroma.store_analysis(
            symbol=symbol,
            agent=agent,
            signal=signal,
            confidence=confidence,
            reasoning=reasoning,
            market_state=market_state,
            session_id=self.session.session_id,
        )
    
    def recall_similar(
        self,
        query: str,
        agent: Optional[str] = None,
        n: int = 5,
    ) -> List[Dict]:
        """Recall similar past analyses from ChromaDB."""
        if not self.chroma:
            return []
        return self.chroma.recall(query=query, agent_filter=agent, n=n)
    
    def add_feedback(
        self,
        analysis_id: str,
        agent: str,
        helpful: bool,
        rating: int,
        correction: Optional[str] = None,
    ):
        """Record user feedback."""
        if self.chroma:
            self.chroma.store_feedback(analysis_id, agent, helpful, rating, correction)
        if self.fuzzy:
            self.fuzzy.update_from_feedback(agent, helpful, rating)
    
    def add_outcome(
        self,
        symbol: str,
        agent: str,
        prediction: str,
        outcome: str,
        confidence: float,
        price_change: float,
    ):
        """Record actual outcome for learning."""
        if self.chroma:
            self.chroma.store_outcome(
                symbol=symbol,
                agent=agent,
                prediction=prediction,
                timeframe_hours=24,
                actual_direction=outcome,
                actual_price_change=price_change,
            )
        if self.fuzzy:
            self.fuzzy.update_from_outcome(agent, symbol, outcome, confidence)
    
    def get_context_for_agent(self, agent: str) -> str:
        """Get formatted context string for agent."""
        if not self.session:
            return ""
        
        context_parts = []
        if self.session.symbol:
            context_parts.append(f"Symbol: {self.session.symbol}")
        
        agent_entries = self.session.get_for_agent(agent, limit=3)
        if agent_entries:
            context_parts.append(f"\nRecent {agent} analyses:")
            for entry in agent_entries:
                context_parts.append(f"- {entry.content[:150]}")
        
        return "\n".join(context_parts)
    
    def get_agent_weights(
        self,
        symbol: Optional[str] = None,
        market_condition: Optional[str] = None,
    ) -> Dict[str, float]:
        """Get adaptive weights for synthesis."""
        if not self.fuzzy:
            from .fuzzy import FuzzyMemory
            return FuzzyMemory.DEFAULT_WEIGHTS
        return self.fuzzy.get_weights(symbol, market_condition)
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get overall memory statistics."""
        if not self.chroma:
            return {"status": "disabled"}
        return self.chroma.get_summary()
