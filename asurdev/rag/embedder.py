"""Embedding pipeline для asurdev Sentinel"""
import os
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False


@dataclass
class EmbeddingResult:
    """Результат эмбеддинга"""
    ids: List[str]
    embeddings: List[List[float]]
    documents: List[str]
    metadatas: List[dict]


class AstroEmbedder:
    """
    Embedding модель для астрологических документов.
    
    Использует sentence-transformers для создания эмбеддингов.
    Альтернатива: OpenAI embeddings (через API).
    """
    
    DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        device: str = "cpu",
        batch_size: int = 32
    ):
        self.model_name = model_name or self.DEFAULT_MODEL
        self.device = device
        self.batch_size = batch_size
        self.model = None
        
        if HAS_SENTENCE_TRANSFORMERS:
            self._load_model()
    
    def _load_model(self):
        """Загрузить модель"""
        if os.environ.get("SKIP_EMBEDDING"):
            return
        
        try:
            self.model = SentenceTransformer(self.model_name, device=self.device)
            print(f"✓ Embedding model loaded: {self.model_name}")
        except Exception as e:
            print(f"⚠ Could not load embedding model: {e}")
            print("  Using mock embeddings for development")
            self.model = None
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Создать эмбеддинги для списка текстов
        
        Args:
            texts: Список текстов для эмбеддинга
            
        Returns:
            Список эмбеддингов (векторов)
        """
        if self.model is None:
            # Mock embeddings для разработки
            return [self._mock_embedding(t) for t in texts]
        
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=self.batch_size,
                show_progress_bar=False,
                convert_to_numpy=True
            )
            return embeddings.tolist()
        except Exception as e:
            print(f"⚠ Embedding error: {e}")
            return [self._mock_embedding(t) for t in texts]
    
    def embed_query(self, query: str) -> List[float]:
        """
        Создать эмбеддинг для запроса
        
        Args:
            query: Текстовый запрос
            
        Returns:
            Эмбеддинг вектор
        """
        if self.model is None:
            return self._mock_embedding(query)
        
        try:
            embedding = self.model.encode(
                [query],
                convert_to_numpy=True
            )
            return embedding[0].tolist()
        except Exception as e:
            print(f"⚠ Query embedding error: {e}")
            return self._mock_embedding(query)
    
    @staticmethod
    def _mock_embedding(text: str) -> List[float]:
        """
        Генерация mock эмбеддинга на основе хеша текста.
        Для разработки когда нет GPU.
        """
        import hashlib
        
        # Простой детерминированный "эмбеддинг" на основе хеша
        hash_bytes = hashlib.sha256(text.encode()).digest()
        
        # Нормализовать в 0-1
        embedding = [b / 255.0 for b in hash_bytes[:384]]  # 384 dims
        
        # Дополнить до 384 если нужно
        while len(embedding) < 384:
            embedding.append(0.0)
        
        # Нормализовать L2
        import math
        norm = math.sqrt(sum(x*x for x in embedding))
        if norm > 0:
            embedding = [x/norm for x in embedding]
        
        return embedding[:384]
    
    @property
    def embedding_dim(self) -> int:
        """Размерность эмбеддинга"""
        return 384  # MiniLM-L6 стандарт


class ChromaStore:
    """
    ChromaDB хранилище для эмбеддингов.
    
    Альтернативы: FAISS, Qdrant, Weaviate
    """
    
    def __init__(
        self,
        persist_directory: str = "./data/rag_index",
        collection_name: str = "asurdev"
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        
        if HAS_CHROMADB:
            self._connect()
    
    def _connect(self):
        """Подключиться к ChromaDB"""
        try:
            Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
            
            # Используем PersistentClient для новых версий chromadb
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False
                )
            )
            
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "asurdev Sentinel knowledge base"}
            )
            print(f"✓ ChromaDB connected: {self.collection_name}")
        except Exception as e:
            print(f"⚠ ChromaDB error: {e}")
            self.client = None
            self.collection = None
    
    def add_documents(
        self,
        ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[dict]
    ):
        """Добавить документы в коллекцию"""
        if self.collection is None:
            return
        
        try:
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
        except Exception as e:
            print(f"⚠ Error adding documents: {e}")
    
    def query(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[dict] = None,
        where_document: Optional[dict] = None
    ) -> dict:
        """Найти похожие документы"""
        if self.collection is None:
            return {"ids": [], "documents": [], "distances": []}
        
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                where_document=where_document
            )
            return results
        except Exception as e:
            print(f"⚠ Query error: {e}")
            return {"ids": [], "documents": [], "distances": []}
    
    def count(self) -> int:
        """Количество документов"""
        if self.collection is None:
            return 0
        return self.collection.count()
