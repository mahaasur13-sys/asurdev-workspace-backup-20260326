"""
RAG Knowledge Base for AstroFin.
Vector-based retrieval from markdown knowledge files.
"""
from __future__ import annotations
import os
import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio

@dataclass
class KnowledgeChunk:
    """A chunk of knowledge for RAG retrieval."""
    content: str
    source: str
    chunk_id: str
    relevance_score: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class RAGKnowledgeBase:
    """
    RAG Knowledge Base for AstroFin agents.
    Loads markdown files and provides semantic search.
    """
    
    def __init__(self, knowledge_dir: str = None):
        self.knowledge_dir = knowledge_dir or "/home/workspace/astrofin/knowledge"
        self._chunks: Dict[str, List[KnowledgeChunk]] = {}
        self._domains = ["technical", "astro", "trading", "election", "mikrotik"]
        self._initialized = False
        
    async def initialize(self):
        """Load all knowledge files."""
        if self._initialized:
            return
            
        for domain in self._domains:
            domain_path = os.path.join(self.knowledge_dir, domain)
            if os.path.exists(domain_path):
                await self._load_domain(domain, domain_path)
        
        self._initialized = True
        
    async def _load_domain(self, domain: str, domain_path: str):
        """Load all markdown files in a domain."""
        self._chunks[domain] = []
        
        for root, dirs, files in os.walk(domain_path):
            for fname in files:
                if fname.endswith(('.md', '.txt')):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Split into chunks
                        chunks = self._split_into_chunks(content, fname)
                        for i, chunk_content in enumerate(chunks):
                            chunk = KnowledgeChunk(
                                content=chunk_content,
                                source=f"knowledge/{domain}/{fname}",
                                chunk_id=f"{domain}_{fname}_{i}",
                                metadata={"domain": domain, "file": fname}
                            )
                            self._chunks[domain].append(chunk)
                    except Exception as e:
                        print(f"Error loading {fpath}: {e}")
    
    def _split_into_chunks(self, content: str, source: str) -> List[str]:
        """Split content into semantic chunks."""
        # Split by headers first
        sections = re.split(r'\n(?=#)', content)
        chunks = []
        current_chunk = []
        current_size = 0
        max_chunk_size = 500  # characters
        
        for section in sections:
            if current_size + len(section) > max_chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
            current_chunk.append(section)
            current_size += len(section)
        
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks if chunks else [content[:max_chunk_size]]
    
    async def retrieve(
        self, 
        query: str, 
        domain: str = None,
        top_k: int = 5,
        min_relevance: float = 0.3
    ) -> List[KnowledgeChunk]:
        """
        Retrieve relevant knowledge chunks for a query.
        
        Args:
            query: Search query
            domain: Optional domain filter
            top_k: Number of results to return
            min_relevance: Minimum relevance score (0-1)
            
        Returns:
            List of relevant KnowledgeChunks
        """
        if not self._initialized:
            await self.initialize()
        
        # Get domains to search
        domains_to_search = [domain] if domain else self._domains
        domains_to_search = [d for d in domains_to_search if d in self._chunks]
        
        # Calculate relevance scores
        scored_chunks = []
        query_words = set(query.lower().split())
        
        for d in domains_to_search:
            for chunk in self._chunks[d]:
                score = self._calculate_relevance(query, query_words, chunk)
                if score >= min_relevance:
                    chunk.relevance_score = score
                    scored_chunks.append(chunk)
        
        # Sort by relevance and return top_k
        scored_chunks.sort(key=lambda x: x.relevance_score, reverse=True)
        return scored_chunks[:top_k]
    
    def _calculate_relevance(
        self, 
        query: str, 
        query_words: set,
        chunk: KnowledgeChunk
    ) -> float:
        """Calculate relevance score between query and chunk."""
        content_lower = chunk.content.lower()
        content_words = set(content_lower.split())
        
        # Word overlap
        overlap = len(query_words & content_words)
        if overlap == 0:
            return 0.0
        
        # TF-based scoring
        word_score = overlap / len(query_words)
        
        # Position bonus (query words appearing early)
        pos_bonus = 0.0
        for i, word in enumerate(query_words):
            if word in content_lower[:200]:  # First 200 chars
                pos_bonus += 0.1
        
        # Section header bonus
        header_bonus = 0.0
        lines = chunk.content.split('\n')
        for line in lines[:3]:  # First 3 lines
            if any(word in line.lower() for word in query_words if len(word) > 3):
                header_bonus += 0.15
        
        return min(1.0, word_score + pos_bonus + header_bonus)
    
    async def get_domain_stats(self) -> Dict[str, int]:
        """Get statistics about loaded knowledge."""
        if not self._initialized:
            await self.initialize()
            
        stats = {}
        for domain, chunks in self._chunks.items():
            stats[domain] = len(chunks)
        return stats
    
    def get_sources(self) -> List[str]:
        """Get list of all knowledge sources."""
        sources = []
        for domain, chunks in self._chunks.items():
            for chunk in chunks:
                if chunk.source not in sources:
                    sources.append(chunk.source)
        return sources


# Global instance
_rag_kb: Optional[RAGKnowledgeBase] = None

async def get_rag_kb() -> RAGKnowledgeBase:
    """Get global RAG knowledge base instance."""
    global _rag_kb
    if _rag_kb is None:
        _rag_kb = RAGKnowledgeBase()
        await _rag_kb.initialize()
    return _rag_kb
