"""
AstroFin Sentinel v5 — RAG Retriever
Unified knowledge retrieval interface for all agents.
"""

import os
import re
from pathlib import Path
from typing import Optional


class RAGRetriever:
    """
    RAG-ретrieval для агентов.
    
    Каждый агент запрашивает знания через `retrieve()`.
    Возвращает чанки с цитированием.
    """
    
    def __init__(self, knowledge_dir: str = None):
        if knowledge_dir is None:
            # Default: sibling directory to this file
            self.knowledge_dir = Path(__file__).parent
        else:
            self.knowledge_dir = Path(knowledge_dir)
        
        self.chunks_dir = self.knowledge_dir / "chunks"
        self._chunk_cache = {}
    
    def retrieve(
        self,
        query: str,
        domain: Optional[str] = None,
        top_k: int = 5,
        min_relevance: float = 0.3,
    ) -> list[dict]:
        """
        Получить релевантные чанки из базы знаний.
        
        Args:
            query: Конкретный запрос агента
            domain: Опциональный фильтр по домену (astrology/technical/trading)
            top_k: Сколько чанков вернуть
            min_relevance: Минимальный порог релевантности
            
        Returns:
            List[dict] с полями: content, source, relevance_score
        """
        # 1. Load chunks (lazy load + cache)
        all_chunks = self._load_chunks(domain)
        
        # 2. Simple keyword matching (production would use FAISS/BM25)
        query_terms = self._extract_terms(query)
        scored_chunks = []
        
        for chunk in all_chunks:
            chunk_text = chunk["content"].lower()
            score = sum(1 for term in query_terms if term in chunk_text)
            score /= max(len(query_terms), 1)
            
            if score >= min_relevance:
                scored_chunks.append({
                    "content": chunk["content"],
                    "source": chunk["source"],
                    "relevance_score": score,
                    "domain": chunk.get("domain", "unknown"),
                })
        
        # 3. Sort by relevance and return top_k
        scored_chunks.sort(key=lambda x: x["relevance_score"], reverse=True)
        return scored_chunks[:top_k]
    
    def _load_chunks(self, domain: Optional[str] = None) -> list[dict]:
        """Load all markdown chunks from knowledge base."""
        chunks = []
        search_dirs = []
        
        if domain:
            domain_map = {
                "astrology": ["astrology"],
                "technical": ["technical"],
                "trading": ["trading"],
            }
            subdirs = domain_map.get(domain, [])
            for sd in subdirs:
                d = self.chunks_dir / sd
                if d.exists():
                    search_dirs.append(d)
        else:
            if self.chunks_dir.exists():
                search_dirs.append(self.chunks_dir)
        
        for search_dir in search_dirs:
            for md_file in search_dir.rglob("*.md"):
                cache_key = str(md_file)
                if cache_key in self._chunk_cache:
                    chunks.extend(self._chunk_cache[cache_key])
                    continue
                
                try:
                    content = md_file.read_text(encoding="utf-8")
                    file_chunks = self._split_into_chunks(content, md_file, domain)
                    self._chunk_cache[cache_key] = file_chunks
                    chunks.extend(file_chunks)
                except Exception:
                    continue
        
        return chunks
    
    def _split_into_chunks(self, content: str, source_file: Path, domain: str) -> list[dict]:
        """Split markdown file into semantic chunks."""
        chunks = []
        
        # Split by headers (## = major topic, ### = sub-topic)
        sections = re.split(r"\n(?=##\s)", content)
        
        current_section = ""
        current_title = source_file.stem
        
        for section in sections:
            lines = section.strip().split("\n")
            if not lines:
                continue
            
            # Extract title from first header
            if lines[0].startswith("#"):
                current_title = lines[0].lstrip("# ").strip()
                content_part = "\n".join(lines[1:]).strip()
            else:
                content_part = section.strip()
            
            if content_part:
                chunks.append({
                    "content": content_part,
                    "source": f"{source_file.name}#{current_title}",
                    "domain": domain or source_file.parent.name,
                })
        
        return chunks
    
    def _extract_terms(self, query: str) -> list[str]:
        """Extract search terms from query."""
        # Remove common stopwords
        stopwords = {
            "и", "в", "на", "с", "по", "для", "как", "что", "это",
            "the", "a", "an", "and", "or", "but", "in", "on", "at",
            "to", "for", "of", "is", "are", "was", "were",
        }
        
        words = re.findall(r"\b\w+\b", query.lower())
        return [w for w in words if w not in stopwords and len(w) > 2]


# ─── Agent Tool Interface ──────────────────────────────────────────────────────

def retrieve_knowledge(query: str, domain: Optional[str] = None) -> str:
    """
    Инструмент для агентов: запрашивает RAG базу.
    
    Агент должен вызывать это когда:
    - Вопрос выходит за рамки его instructions.md
    - Нужен факт, а не мнение
    - Требуется подтверждение из базы знаний
    
    Returns:
        Markdown string с цитированными чанками
    """
    retriever = RAGRetriever()
    chunks = retriever.retrieve(query, domain=domain, top_k=5)
    
    if not chunks:
        return "⚠️ В базе знаний не найдена релевантная информация."
    
    result_lines = [f"### Результаты RAG-поиска по запросу: «{query}»\n"]
    
    for i, chunk in enumerate(chunks, 1):
        result_lines.append(
            f"**[{i}]** {chunk['source']} "
            f"(релевантность: {chunk['relevance_score']:.0%})\n\n"
            f"{chunk['content'][:500]}"
            f"{'...' if len(chunk['content']) > 500 else ''}\n"
        )
    
    return "\n---\n".join(result_lines)
