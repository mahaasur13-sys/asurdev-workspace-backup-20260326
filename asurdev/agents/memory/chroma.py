"""
ChromaDB Persistent Storage — RAG for Agent Analyses
asurdev Sentinel v3.2
"""

from __future__ import annotations
import os
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional, List

import chromadb
from chromadb.config import Settings

try:
    from langchain_openai import OpenAIEmbeddings
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


def get_embedder():
    """Get OpenAI embedder for ChromaDB."""
    if LANGCHAIN_AVAILABLE:
        api_key = os.environ.get("asurdev_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if api_key:
            return OpenAIEmbeddings(api_key=api_key, model="text-embedding-3-small")
    return None


class ChromaMemory:
    """
    ChromaDB-backed persistent storage for RAG.
    
    Collections:
    - analyses: Agent analysis records
    - feedback: User feedback on analyses
    - outcomes: Prediction outcomes for learning
    - patterns: Learned market patterns
    
    Usage:
        chroma = ChromaMemory("./data/chroma_db")
        doc_id = chroma.store_analysis("BTC", "astro", "BULLISH", 75, "Strong aspect")
    """
    
    def __init__(self, persist_dir: str = "./data/chroma_db"):
        self.persist_dir = persist_dir
        self.embedder = get_embedder()
        self.client = chromadb.PersistentClient(path=persist_dir)
        
        # Create/access collections
        self.analyses = self.client.get_or_create_collection(
            name="analyses",
            metadata={"description": "Agent analysis records"},
        )
        self.feedback = self.client.get_or_create_collection(
            name="feedback",
            metadata={"description": "User feedback"},
        )
        self.outcomes = self.client.get_or_create_collection(
            name="outcomes",
            metadata={"description": "Prediction outcomes"},
        )
        self.patterns = self.client.get_or_create_collection(
            name="patterns",
            metadata={"description": "Learned patterns"},
        )
    
    def store_analysis(
        self,
        symbol: str,
        agent: str,
        signal: str,
        confidence: float,
        reasoning: str,
        market_state: Dict[str, Any],
        session_id: str,
        metadata: Optional[Dict] = None,
    ) -> str:
        """Store agent analysis to ChromaDB."""
        doc_id = hashlib.sha256(
            f"{symbol}{agent}{session_id}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        doc = json.dumps({
            "symbol": symbol,
            "agent": agent,
            "signal": signal,
            "confidence": confidence,
            "reasoning": reasoning,
            "market_state": market_state,
            "session_id": session_id,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }, ensure_ascii=False)
        
        self.analyses.add(
            documents=[doc],
            ids=[doc_id],
            metadatas=[{
                "symbol": symbol,
                "agent": agent,
                "signal": signal,
                "confidence": confidence,
            }],
        )
        return doc_id
    
    def store_feedback(
        self,
        analysis_id: str,
        agent: str,
        helpful: bool,
        rating: int,
        correction: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> str:
        """Store user feedback."""
        doc_id = f"fb_{analysis_id}_{datetime.now().timestamp()}"
        
        doc = json.dumps({
            "analysis_id": analysis_id,
            "agent": agent,
            "helpful": helpful,
            "rating": rating,
            "correction": correction,
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
        }, ensure_ascii=False)
        
        self.feedback.add(
            documents=[doc],
            ids=[doc_id],
            metadatas=[{
                "analysis_id": analysis_id,
                "agent": agent,
                "rating": rating,
                "helpful": helpful,
            }],
        )
        return doc_id
    
    def store_outcome(
        self,
        symbol: str,
        agent: str,
        prediction: str,
        timeframe_hours: int,
        actual_direction: str,
        actual_price_change: float,
        notes: Optional[str] = None,
    ) -> str:
        """Store prediction outcome for learning."""
        doc_id = f"out_{symbol}_{datetime.now().timestamp()}"
        
        doc = json.dumps({
            "symbol": symbol,
            "agent": agent,
            "prediction": prediction,
            "timeframe_hours": timeframe_hours,
            "actual_direction": actual_direction,
            "actual_price_change": actual_price_change,
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
        }, ensure_ascii=False)
        
        self.outcomes.add(
            documents=[doc],
            ids=[doc_id],
            metadatas=[{
                "symbol": symbol,
                "agent": agent,
                "prediction": prediction,
                "actual_direction": actual_direction,
            }],
        )
        return doc_id
    
    def recall(
        self,
        query: str,
        collection: str = "analyses",
        n: int = 5,
        agent_filter: Optional[str] = None,
        symbol_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Recall similar entries via vector search."""
        col = getattr(self, collection, self.analyses)
        
        where_clause = None
        if agent_filter and symbol_filter:
            where_clause = {"$and": [{"agent": agent_filter}, {"symbol": symbol_filter}]}
        elif agent_filter:
            where_clause = {"agent": agent_filter}
        elif symbol_filter:
            where_clause = {"symbol": symbol_filter}
        
        results = col.query(
            query_texts=[query],
            n_results=n,
            where=where_clause,
        )
        
        recalls = []
        if results["documents"] and results["documents"][0]:
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                try:
                    data = json.loads(doc) if isinstance(doc, str) else doc
                except json.JSONDecodeError:
                    data = {"content": doc}
                recalls.append({"data": data, "metadata": meta})
        
        return recalls
    
    def recall_agent_history(
        self,
        agent: str,
        symbol: Optional[str] = None,
        n: int = 10,
    ) -> List[Dict]:
        """Recall history for specific agent."""
        where_clause = None
        if agent_filter := agent:
            if symbol_filter := symbol:
                where_clause = {"$and": [{"agent": agent_filter}, {"symbol": symbol_filter}]}
            else:
                where_clause = {"agent": agent_filter}
        elif symbol_filter := symbol:
            where_clause = {"symbol": symbol_filter}
        
        results = self.analyses.query(
            query_texts=[f"{agent} analysis"],
            n_results=n,
            where=where_clause,
        )
        
        recalls = []
        if results["documents"] and results["documents"][0]:
            for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
                try:
                    data = json.loads(doc) if isinstance(doc, str) else doc
                except json.JSONDecodeError:
                    data = {"content": doc}
                recalls.append({"data": data, "metadata": meta})
        
        return recalls
    
    def recall_patterns(
        self,
        pattern_type: Optional[str] = None,
        n: int = 5,
    ) -> List[Dict]:
        """Recall learned patterns."""
        results = self.patterns.get(
            where={"pattern_type": pattern_type} if pattern_type else None
        )
        
        patterns = []
        if results["documents"]:
            for doc in results["documents"]:
                try:
                    patterns.append(json.loads(doc))
                except json.JSONDecodeError:
                    pass
        
        return patterns[:n]
    
    def learn_pattern(
        self,
        pattern_type: str,
        description: str,
        confidence: float,
        evidence: List[str],
        agent: Optional[str] = None,
    ) -> str:
        """Store learned pattern."""
        doc_id = f"pat_{pattern_type}_{datetime.now().timestamp()}"
        
        doc = json.dumps({
            "pattern_type": pattern_type,
            "description": description,
            "confidence": confidence,
            "evidence": evidence,
            "agent": agent,
            "timestamp": datetime.now().isoformat(),
        }, ensure_ascii=False)
        
        self.patterns.add(
            documents=[doc],
            ids=[doc_id],
            metadatas=[{
                "pattern_type": pattern_type,
                "confidence": confidence,
            }],
        )
        return doc_id
    
    def get_agent_stats(self, agent: str) -> Dict[str, Any]:
        """Get performance stats for agent."""
        fb_results = self.feedback.get(where={"agent": agent})
        total = len(fb_results["ids"]) if fb_results["ids"] else 0
        
        ratings = []
        correct = 0
        
        if fb_results["documents"]:
            for doc in fb_results["documents"]:
                try:
                    fb = json.loads(doc) if isinstance(doc, str) else doc
                    if "rating" in fb:
                        ratings.append(fb["rating"])
                    if fb.get("helpful"):
                        correct += 1
                except:
                    pass
        
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        
        return {
            "agent": agent,
            "total_analyses": total,
            "avg_rating": avg_rating,
            "accuracy": correct / max(total, 1),
            "last_updated": datetime.now().isoformat(),
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get overall collection statistics."""
        return {
            "analyses_count": self.analyses.count(),
            "feedback_count": self.feedback.count(),
            "outcomes_count": self.outcomes.count(),
            "patterns_count": self.patterns.count(),
            "persist_dir": self.persist_dir,
        }
