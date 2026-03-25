"""
RAG Memory for AstroFin Sentinel

Provides persistent storage and retrieval of analysis history
using vector embeddings for semantic search.

Features:
- ChromaDB for vector storage
- Semantic search by query/symbol
- Session-based context
- Automatic cleanup of old entries
"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional, Any
from dataclasses import asdict
from pathlib import Path

# We'll use a simple JSON-based storage initially
# Can be upgraded to ChromaDB/FAISS for production

MEMORY_DIR = Path(__file__).parent.parent / ".memory"
MEMORY_FILE = MEMORY_DIR / "analysis_history.json"
INDEX_FILE = MEMORY_DIR / "index.json"


class RAGMemory:
    """
    RAG Memory for storing and retrieving analysis context.
    
    Uses a simple JSON-based store for now with the ability
    to upgrade to ChromaDB for production use.
    """
    
    def __init__(
        self,
        memory_dir: Path = MEMORY_DIR,
        max_entries: int = 1000,
        ttl_days: int = 30
    ):
        self.memory_dir = memory_dir
        self.max_entries = max_entries
        self.ttl_days = ttl_days
        self._ensure_storage()
    
    def _ensure_storage(self):
        """Ensure memory directory and files exist."""
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        if not MEMORY_FILE.exists():
            self._save_memory([])
        if not INDEX_FILE.exists():
            self._save_index({})
    
    def _load_memory(self) -> list:
        """Load memory entries from disk."""
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_memory(self, entries: list):
        """Save memory entries to disk."""
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2, default=str)
    
    def _load_index(self) -> dict:
        """Load search index from disk."""
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    
    def _save_index(self, index: dict):
        """Save search index to disk."""
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    async def store_analysis(self, state: "AnalysisState") -> str:
        """
        Store a completed analysis in memory.
        
        Args:
            state: AnalysisState with completed analysis
            
        Returns:
            Entry ID for the stored analysis
        """
        if not state.final_recommendation:
            return None
        
        entry_id = f"{state.symbol}_{state.session_id}_{int(datetime.now().timestamp())}"
        
        entry = {
            "id": entry_id,
            "symbol": state.symbol,
            "side": state.side,
            "interval": state.interval,
            "composite_score": state.composite_score,
            "recommendation": state.final_recommendation,
            "timestamp": datetime.now().isoformat(),
            "birth_date": state.birth_date,
            "weights": state.weights,
            # Store summaries for quick access
            "technical_signal": state.technical_report.signal if state.technical_report else None,
            "fundamental_signal": state.fundamental_report.signal if state.fundamental_report else None,
            "astrologer_signal": state.astrologer_report.signal if state.astrologer_report else None,
            # Store full markdown for reference
            "markdown": state.markdown_output[:2000] if state.markdown_output else "",
            # Searchable text
            "search_text": self._build_search_text(state)
        }
        
        # Load, append, and save
        entries = self._load_memory()
        entries.append(entry)
        
        # Cleanup old entries
        entries = self._cleanup_old_entries(entries)
        
        # Enforce max entries
        if len(entries) > self.max_entries:
            entries = entries[-self.max_entries:]
        
        self._save_memory(entries)
        
        # Update index
        index = self._load_index()
        index[entry_id] = {
            "symbol": state.symbol,
            "timestamp": entry["timestamp"],
            "search_text": entry["search_text"][:500]
        }
        self._save_index(index)
        
        return entry_id
    
    def _build_search_text(self, state: "AnalysisState") -> str:
        """Build searchable text from state."""
        parts = [
            state.symbol,
            state.side,
            state.interval,
            state.final_recommendation.get("action", "") if state.final_recommendation else "",
        ]
        
        if state.technical_report:
            parts.extend([state.technical_report.signal, state.technical_report.reasoning])
        if state.fundamental_report:
            parts.extend([state.fundamental_report.signal, state.fundamental_report.reasoning])
        if state.astrologer_report:
            parts.extend([state.astrologer_report.signal, state.astrologer_report.reasoning])
        
        return " ".join(str(p) for p in parts if p)
    
    def _cleanup_old_entries(self, entries: list) -> list:
        """Remove entries older than TTL."""
        cutoff = datetime.now() - timedelta(days=self.ttl_days)
        cutoff_str = cutoff.isoformat()
        
        return [
            e for e in entries
            if datetime.fromisoformat(e["timestamp"]) > cutoff
        ]
    
    async def retrieve_relevant(
        self,
        query: str,
        symbol: Optional[str] = None,
        limit: int = 3
    ) -> list[dict]:
        """
        Retrieve relevant past analyses.
        
        For now, uses simple keyword matching.
        Can be upgraded to ChromaDB embeddings for semantic search.
        
        Args:
            query: Search query
            symbol: Optional symbol to filter by
            limit: Maximum number of results
            
        Returns:
            List of relevant analysis entries
        """
        entries = self._load_memory()
        
        if not entries:
            return []
        
        # Filter by symbol if provided
        if symbol:
            entries = [e for e in entries if e.get("symbol") == symbol]
        
        # Simple scoring based on keyword matches
        query_words = set(query.lower().split())
        
        scored = []
        for entry in entries:
            score = 0
            search_text = entry.get("search_text", "").lower()
            
            for word in query_words:
                if word in search_text:
                    score += 1
                    # Bonus for symbol match
                    if word == symbol.lower():
                        score += 2
            
            # Recency boost
            entry_age = datetime.now() - datetime.fromisoformat(entry["timestamp"])
            if entry_age < timedelta(hours=24):
                score *= 1.5
            elif entry_age < timedelta(days=7):
                score *= 1.2
            
            scored.append((score, entry))
        
        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Return top results
        return [entry for score, entry in scored[:limit] if score > 0]
    
    async def get_session_history(
        self,
        session_id: str,
        limit: int = 10
    ) -> list[dict]:
        """Get all analyses for a specific session."""
        entries = self._load_memory()
        session_entries = [
            e for e in entries
            if e.get("session_id", "").startswith(session_id)
        ]
        session_entries.sort(key=lambda x: x["timestamp"], reverse=True)
        return session_entries[:limit]
    
    async def get_symbol_history(
        self,
        symbol: str,
        days: int = 30
    ) -> list[dict]:
        """Get analysis history for a symbol."""
        entries = self._load_memory()
        cutoff = datetime.now() - timedelta(days=days)
        
        symbol_entries = [
            e for e in entries
            if e.get("symbol") == symbol
            and datetime.fromisoformat(e["timestamp"]) > cutoff
        ]
        symbol_entries.sort(key=lambda x: x["timestamp"], reverse=True)
        return symbol_entries
    
    def clear_old_entries(self, days: int = 90) -> int:
        """Manually clear entries older than specified days."""
        entries = self._load_memory()
        cutoff = datetime.now() - timedelta(days=days)
        
        original_count = len(entries)
        entries = [
            e for e in entries
            if datetime.fromisoformat(e["timestamp"]) > cutoff
        ]
        
        self._save_memory(entries)
        return original_count - len(entries)


# ============================================================================
# Global memory instance
# ============================================================================

_memory_instance: Optional[RAGMemory] = None


def get_memory() -> RAGMemory:
    """Get or create global RAG memory instance."""
    global _memory_instance
    if _memory_instance is None:
        _memory_instance = RAGMemory()
    return _memory_instance


def reset_memory():
    """Reset global memory instance (mainly for testing)."""
    global _memory_instance
    _memory_instance = None
