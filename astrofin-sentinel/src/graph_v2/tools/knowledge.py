"""
Knowledge retrieval tool with caching.
Uses Chroma for local dev, Pinecone/Supabase for production.
"""

import hashlib
import os
from datetime import datetime
from typing import Optional

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

try:
    from langchain_community.vectorstores import Chroma
    from langchain_community.embeddings import OllamaEmbeddings
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


class KnowledgeRetriever:
    """
    Tool for retrieving relevant knowledge chunks from vectorstore.
    
    Features:
    - Metadata filtering by agent_role + topic
    - Hybrid search (BM25 + semantic) via reranking
    - Cache by JD_UT + query_hash for astro stability
    - Chroma (local) / Pinecone / Supabase (production)
    """
    
    def __init__(
        self,
        persist_directory: str = "./data/knowledge_base",
        collection_name: str = "astrofin_knowledge",
        cache_ttl_seconds: int = 3600,
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.cache_ttl = cache_ttl_seconds
        self._cache: dict = {}
        
        if CHROMA_AVAILABLE and LANGCHAIN_AVAILABLE:
            self._init_chroma()
        else:
            self._vectorstore = None
            self._embedding_model = None
    
    def _init_chroma(self):
        """Initialize Chroma vectorstore with Ollama embeddings."""
        self._embedding_model = OllamaEmbeddings(
            model=os.getenv("EMBEDDING_MODEL", "nomic-embed-text"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
        )
        
        self._vectorstore = Chroma(
            persist_directory=self.persist_directory,
            collection_name=self.collection_name,
            embedding_function=self._embedding_model,
        )
    
    def _get_cache_key(self, query: str, agent_role: str, jd_ut: Optional[float] = None) -> str:
        """Generate cache key from query + role + optional JD_UT."""
        key_parts = [query, agent_role]
        if jd_ut is not None:
            key_parts.append(str(jd_ut))
        key_string = "|".join(key_parts)
        return hashlib.sha256(key_string.encode()).hexdigest()[:16]
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cache entry exists and is still valid."""
        if cache_key not in self._cache:
            return False
        timestamp, _ = self._cache[cache_key]
        return (datetime.now().timestamp() - timestamp) < self.cache_ttl
    
    def retrieve(
        self,
        query: str,
        agent_role: str,
        topic: Optional[str] = None,
        jd_ut: Optional[float] = None,
        top_k: int = 5,
    ) -> str:
        """
        Retrieve knowledge chunks with caching.
        
        Args:
            query: Natural language query
            agent_role: Which agent is asking (MarketAnalyst, BullResearcher, etc.)
            topic: Optional metadata filter (panchanga, technical_analysis, etc.)
            jd_ut: Julian Day UT — if provided, cached by astro state
            top_k: Number of chunks to retrieve
            
        Returns:
            Formatted string of retrieved knowledge chunks
        """
        cache_key = self._get_cache_key(query, agent_role, jd_ut)
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]["result"]
        
        if self._vectorstore is None:
            return self._get_fallback_response(agent_role, query)
        
        where_filter = {"agent_role": agent_role}
        if topic:
            where_filter["topic"] = topic
        
        results = self._vectorstore.similarity_search(
            query=query,
            k=top_k,
            filter=where_filter if where_filter else None,
        )
        
        if not results:
            where_filter = {"agent_role": agent_role}
            results = self._vectorstore.similarity_search(
                query=query,
                k=top_k,
                filter=where_filter,
            )
        
        chunks = []
        for i, doc in enumerate(results):
            source = doc.metadata.get("source", "unknown")
            topic_tag = doc.metadata.get("topic", "")
            chunks.append(
                f"[Chunk {i+1}] (source: {source}, topic: {topic_tag})\n"
                f"{doc.page_content}"
            )
        
        result = "\n\n---\n\n".join(chunks) if chunks else self._get_fallback_response(agent_role, query)
        
        self._cache[cache_key] = (datetime.now().timestamp(), result)
        
        return result
    
    def _get_fallback_response(self, agent_role: str, query: str) -> str:
        """Fallback when vectorstore is unavailable."""
        fallbacks = {
            "MarketAnalyst": (
                "No knowledge base entries found. Use your technical analysis "
                "expertise to evaluate the asset based on price action, indicators, "
                "and chart patterns."
            ),
            "BullResearcher": (
                "No knowledge base entries found. Research bullish catalysts "
                "from recent news, on-chain metrics, and market sentiment."
            ),
            "BearResearcher": (
                "No knowledge base entries found. Identify bearish risks "
                "from liquidation levels, regulatory concerns, and whale activity."
            ),
            "MuhurtaSpecialist": (
                "No knowledge base entries found. Apply Vedic astrology principles "
                "from your instructions: Nakshatra, Tithi, Yoga, Karana, and Choghadiya."
            ),
            "Synthesizer": (
                "No knowledge base entries found. Apply weighted voting methodology: "
                "Market Analyst (1.0), Bull/Bear Researchers (0.8), Muhurta (0.5)."
            ),
            "Supervisor": (
                "No knowledge base entries found. Coordinate specialists following "
                "the workflow: swiss_ephemeris → retrieve_knowledge → dispatch specialists."
            ),
        }
        return fallbacks.get(agent_role, "No relevant knowledge found.")
    
    def add_knowledge(
        self,
        content: str,
        agent_role: str,
        topic: str,
        source: str = "unknown",
        metadata: Optional[dict] = None,
    ):
        """Add new knowledge chunk to vectorstore."""
        if self._vectorstore is None:
            print("Warning: Vectorstore not initialized. Run _init_chroma() first.")
            return
        
        doc_metadata = {
            "agent_role": agent_role,
            "topic": topic,
            "source": source,
            **(metadata or {}),
        }
        
        self._vectorstore.add_texts(
            texts=[content],
            metadatas=[doc_metadata],
        )
    
    def clear_cache(self):
        """Clear the in-memory cache."""
        self._cache.clear()


# Global retriever instance (lazy initialization)
_retriever: Optional[KnowledgeRetriever] = None


def get_retriever() -> KnowledgeRetriever:
    """Get or create global KnowledgeRetriever instance."""
    global _retriever
    if _retriever is None:
        _retriever = KnowledgeRetriever(
            persist_directory=os.getenv(
                "KNOWLEDGE_BASE_DIR", 
                "./data/knowledge_base"
            ),
            collection_name="astrofin_knowledge",
        )
    return _retriever


def retrieve_knowledge(
    query: str,
    agent_role: str,
    topic: Optional[str] = None,
    jd_ut: Optional[float] = None,
) -> str:
    """
    Tool function for retrieving knowledge from vectorstore.
    
    Usage in LangChain/LangGraph:
        from langchain_core.tools import tool
        
        @tool
        def retrieve_knowledge(query: str, agent_role: str, topic: str = None) -> str:
            '''...'''
            return get_retriever().retrieve(
                query=query,
                agent_role=agent_role,
                topic=topic,
            )
    
    Args:
        query: The user's question or topic to retrieve knowledge about
        agent_role: Which agent is calling (MarketAnalyst, BullResearcher, etc.)
        topic: Optional filter for specific topic (panchanga, technical_analysis, etc.)
        jd_ut: Julian Day UT for astro-stable caching
        
    Returns:
        Formatted knowledge chunks or fallback message
    """
    return get_retriever().retrieve(
        query=query,
        agent_role=agent_role,
        topic=topic,
        jd_ut=jd_ut,
    )
