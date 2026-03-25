"""Retriever с MMR (Maximum Marginal Relevance) для asurdev"""
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class RetrievedChunk:
    """Найденный чанк с метadagрами"""
    content: str
    source: str
    category: str
    relevance_score: float
    distance: float


class AstroRetriever:
    """
    Retriever для астрологических документов.
    
    Особенности:
    - MMR (Maximum Marginal Relevance) для разнообразия
    - Категориальный фильтр
    - Гибридный поиск (семантика + ключевые слова)
    """
    
    def __init__(
        self,
        embedder,  # AstroEmbedder
        store,     # ChromaStore
        default_top_k: int = 5
    ):
        self.embedder = embedder
        self.store = store
        self.default_top_k = default_top_k
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        category_filter: Optional[str] = None,
        use_mmr: bool = True,
        mmr_lambda: float = 0.7
    ) -> List[RetrievedChunk]:
        """
        Найти релевантные чанки.
        
        Args:
            query: Поисковый запрос
            top_k: Количество результатов
            category_filter: Фильтр по категории
            use_mmr: Использовать MMR для разнообразия
            mmr_lambda: Баланс релевантность/разнообразие (0-1)
            
        Returns:
            Список найденных чанков
        """
        top_k = top_k or self.default_top_k
        
        # Получить больше кандидатов для MMR
        fetch_k = min(top_k * 3, 20) if use_mmr else top_k
        
        # Query embedding
        query_embedding = self.embedder.embed_query(query)
        
        # Where clause для фильтра
        where = None
        if category_filter:
            where = {"category": category_filter}
        
        # Поиск
        results = self.store.query(
            query_embedding=query_embedding,
            n_results=fetch_k,
            where=where
        )
        
        if not results or not results.get("ids"):
            return []
        
        # Преобразовать в RetrievedChunk
        chunks = []
        for i, doc_id in enumerate(results["ids"][0]):
            chunk = RetrievedChunk(
                content=results["documents"][0][i],
                source=results["metadatas"][0][i].get("source", ""),
                category=results["metadatas"][0][i].get("category", "unknown"),
                relevance_score=1.0 - results["distances"][0][i],
                distance=results["distances"][0][i]
            )
            chunks.append(chunk)
        
        # MMR для разнообразия
        if use_mmr and len(chunks) > top_k:
            chunks = self._mmr_rerank(chunks, query_embedding, mmr_lambda, top_k)
        
        return chunks[:top_k]
    
    def _mmr_rerank(
        self,
        chunks: List[RetrievedChunk],
        query_embedding: List[float],
        lambda_param: float,
        top_k: int
    ) -> List[RetrievedChunk]:
        """
        MMR reranking для разнообразия результатов.
        
        MMR = λ * relevance - (1-λ) * similarity_to_selected
        """
        selected = []
        remaining = chunks.copy()
        
        query_norm = self._normalize(query_embedding)
        
        while len(selected) < top_k and remaining:
            best_score = -float("inf")
            best_idx = 0
            
            for i, chunk in enumerate(remaining):
                # Relevance к запросу
                relevance = chunk.relevance_score
                
                # Штраф за сходство с уже выбранными
                max_similarity = 0.0
                for sel_chunk in selected:
                    # Простое сходство по категории и источнику
                    if sel_chunk.source == chunk.source:
                        max_similarity = max(max_similarity, 0.8)
                    if sel_chunk.category == chunk.category:
                        max_similarity = max(max_similarity, 0.5)
                
                # MMR score
                mmr_score = lambda_param * relevance - (1 - lambda_param) * max_similarity
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i
            
            selected.append(remaining.pop(best_idx))
        
        return selected
    
    @staticmethod
    def _normalize(vec: List[float]) -> List[float]:
        """Нормализовать вектор L2"""
        import math
        norm = math.sqrt(sum(x*x for x in vec))
        if norm > 0:
            return [x/norm for x in vec]
        return vec
    
    def retrieve_by_category(
        self,
        query: str,
        categories: List[str],
        top_k_per_category: int = 3
    ) -> Dict[str, List[RetrievedChunk]]:
        """
        Найти чанки по категориям.
        
        Для Astro Council: отдельные результаты по Vedic/Western/Financial
        """
        results = {}
        
        for category in categories:
            chunks = self.retrieve(
                query=query,
                top_k=top_k_per_category,
                category_filter=category
            )
            results[category] = chunks
        
        return results
    
    def get_context_for_query(self, query: str, max_length: int = 2000) -> str:
        """
        Получить контекст для LLM запроса.
        
        Формирует текстовый контекст из найденных чанков.
        """
        chunks = self.retrieve(query, top_k=5)
        
        if not chunks:
            return ""
        
        context_parts = []
        current_length = 0
        
        for chunk in chunks:
            # Добавить источник
            source_name = chunk.source.split("/")[-1].replace(".md", "")
            part = f"[{chunk.category.upper()}] {source_name}:\n{chunk.content}\n"
            
            if current_length + len(part) > max_length:
                break
            
            context_parts.append(part)
            current_length += len(part)
        
        return "\n---\n".join(context_parts)
