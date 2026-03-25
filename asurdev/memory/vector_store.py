"""
Persistent Memory — ChromaDB RAG Pipeline
asurdev Sentinel v2.1
"""
import chromadb
from chromadb.config import Settings
from datetime import datetime
from typing import List, Dict, Any, Optional
import hashlib
import json


class VectorMemory:
    """
    ChromaDB-based persistent memory for agents.
    Stores embeddings of analysis, feedback, and outcomes.
    """
    
    def __init__(self, persist_dir: str = "./data/chroma_db"):
        self.persist_dir = persist_dir
        self.client = chromadb.PersistentClient(path=persist_dir)
        
        # Collections
        self.analysis_col = self.client.get_or_create_collection(
            name="analysis",
            metadata={"description": "Agent analysis records"}
        )
        self.feedback_col = self.client.get_or_create_collection(
            name="feedback",
            metadata={"description": "User feedback on predictions"}
        )
        self.outcomes_col = self.client.get_or_create_collection(
            name="outcomes",
            metadata={"description": "Actual market outcomes"}
        )
        self.patterns_col = self.client.get_or_create_collection(
            name="patterns",
            metadata={"description": "Discovered patterns and learnings"}
        )
    
    def add_analysis(
        self,
        symbol: str,
        agent: str,
        signal: str,
        confidence: float,
        reasoning: str,
        market_state: Dict[str, Any],
        metadata: Optional[Dict] = None
    ) -> str:
        """Store agent analysis for future reference"""
        doc_id = hashlib.sha256(
            f"{symbol}{agent}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]
        
        self.analysis_col.add(
            documents=[json.dumps({
                "symbol": symbol,
                "agent": agent,
                "signal": signal,
                "confidence": confidence,
                "reasoning": reasoning,
                "market_state": market_state,
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat()
            })],
            ids=[doc_id],
            metadatas=[{
                "symbol": symbol,
                "agent": agent,
                "signal": signal,
                "confidence": confidence
            }]
        )
        return doc_id
    
    def add_feedback(
        self,
        analysis_id: str,
        helpful: bool,
        rating: int,  # 1-5
        correction: Optional[str] = None,
        notes: Optional[str] = None
    ) -> str:
        """Store user feedback on analysis"""
        doc_id = f"fb_{analysis_id}_{datetime.now().timestamp()}"
        
        self.feedback_col.add(
            documents=[json.dumps({
                "analysis_id": analysis_id,
                "helpful": helpful,
                "rating": rating,
                "correction": correction,
                "notes": notes,
                "timestamp": datetime.now().isoformat()
            })],
            ids=[doc_id],
            metadatas=[{
                "analysis_id": analysis_id,
                "rating": rating,
                "helpful": helpful
            }]
        )
        return doc_id
    
    def add_outcome(
        self,
        symbol: str,
        prediction: str,
        timeframe_hours: int,
        actual_direction: str,  # "correct" / "partial" / "wrong"
        actual_price_change: float,
        notes: Optional[str] = None
    ) -> str:
        """Store actual market outcome for learning"""
        doc_id = f"out_{symbol}_{datetime.now().timestamp()}"
        
        self.outcomes_col.add(
            documents=[json.dumps({
                "symbol": symbol,
                "prediction": prediction,
                "timeframe_hours": timeframe_hours,
                "actual_direction": actual_direction,
                "actual_price_change": actual_price_change,
                "notes": notes,
                "timestamp": datetime.now().isoformat()
            })],
            ids=[doc_id],
            metadatas=[{
                "symbol": symbol,
                "prediction": prediction,
                "actual_direction": actual_direction
            }]
        )
        return doc_id
    
    def recall_similar(
        self,
        query: str,
        collection: str = "analysis",
        n_results: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[Dict]:
        """Recall similar past analyses"""
        col = self._get_collection(collection)
        
        results = col.query(
            query_texts=[query],
            n_results=n_results,
            where=filter_metadata
        )
        
        recalls = []
        if results["documents"]:
            for doc, meta in zip(results["documents"], results["metadatas"]):
                recalls.append({
                    "document": json.loads(doc[0]) if isinstance(doc[0], str) else doc[0],
                    "metadata": meta[0] if meta else {}
                })
        return recalls
    
    def get_agent_stats(self, agent: str) -> Dict[str, Any]:
        """Get agent performance statistics"""
        # Get all feedback for this agent
        fb_results = self.feedback_col.get(
            where={"rating": {"$gte": 1}}
        )
        
        # Get all outcomes
        out_results = self.outcomes_col.get()
        
        total_analyses = len(fb_results["ids"]) if fb_results["ids"] else 0
        avg_rating = sum(fb_results.get("metadatas", [{}])) / max(total_analyses, 1)
        
        return {
            "agent": agent,
            "total_analyses": total_analyses,
            "avg_rating": avg_rating,
            "last_updated": datetime.now().isoformat()
        }
    
    def learn_pattern(
        self,
        pattern_type: str,
        description: str,
        confidence: float,
        evidence: List[str]
    ) -> str:
        """Store discovered pattern from feedback loop"""
        doc_id = f"pat_{pattern_type}_{datetime.now().timestamp()}"
        
        self.patterns_col.add(
            documents=[json.dumps({
                "pattern_type": pattern_type,
                "description": description,
                "confidence": confidence,
                "evidence": evidence,
                "timestamp": datetime.now().isoformat()
            })],
            ids=[doc_id],
            metadatas=[{
                "pattern_type": pattern_type,
                "confidence": confidence
            }]
        )
        return doc_id
    
    def get_learnings(self, pattern_type: Optional[str] = None) -> List[Dict]:
        """Retrieve learned patterns"""
        results = self.patterns_col.get(
            where={"pattern_type": pattern_type} if pattern_type else None
        )
        
        learnings = []
        if results["documents"]:
            for doc in results["documents"]:
                learnings.append(json.loads(doc))
        return learnings
    
    def _get_collection(self, name: str):
        collections = {
            "analysis": self.analysis_col,
            "feedback": self.feedback_col,
            "outcomes": self.outcomes_col,
            "patterns": self.patterns_col
        }
        return collections.get(name, self.analysis_col)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get memory summary stats"""
        return {
            "analysis_count": self.analysis_col.count(),
            "feedback_count": self.feedback_col.count(),
            "outcomes_count": self.outcomes_col.count(),
            "patterns_count": self.patterns_col.count(),
            "persist_dir": self.persist_dir
        }


# Singleton instance
_memory: Optional[VectorMemory] = None


def get_memory(persist_dir: str = "./data/chroma_db") -> VectorMemory:
    global _memory
    if _memory is None:
        _memory = VectorMemory(persist_dir)
    return _memory
