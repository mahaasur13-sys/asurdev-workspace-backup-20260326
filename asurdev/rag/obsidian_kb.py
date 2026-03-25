"""
Obsidian Knowledge Base — индексация Vault в RAG

Запуск:
    python -m rag.obsidian_kb --vault /home/workspace/obsidian-sync --output ./data/rag_index
"""
import argparse
import json
from pathlib import Path
from typing import List, Optional
import hashlib

from .loader import ObsidianLoader
from .embedder import AstroEmbedder, ChromaStore
from .retriever import AstroRetriever


class ObsidianKnowledgeBase:
    """
    Полная RAG система для Obsidian Vault.
    
    Пример использования:
    
    ```python
    # Создать/загрузить KB
    kb = ObsidianKnowledgeBase(
        vault_path="/home/workspace/obsidian-sync",
        persist_dir="./data/rag_index"
    )
    
    # Найти информацию
    results = kb.retrieve("Nakshatra Shatabhisha meaning")
    
    # Получить контекст для LLM
    context = kb.get_context("Что такое Amrit Siddhi Yoga?")
    ```
    """
    
    def __init__(
        self,
        vault_path: str,
        persist_dir: str = "./data/rag_index",
        embedding_model: Optional[str] = None,
        chunk_size: int = 512
    ):
        self.vault_path = Path(vault_path)
        self.persist_dir = Path(persist_dir)
        self.chunk_size = chunk_size
        
        # Компоненты
        self.loader = ObsidianLoader(vault_path)
        self.embedder = AstroEmbedder(model_name=embedding_model)
        self.store = ChromaStore(persist_directory=str(persist_dir))
        self.retriever = AstroRetriever(
            embedder=self.embedder,
            store=self.store,
            default_top_k=5
        )
    
    def build_index(self, force_rebuild: bool = False) -> int:
        """
        Построить индекс.
        
        Args:
            force_rebuild: Перестроить индекс с нуля
            
        Returns:
            Количество проиндексированных документов
        """
        # Проверить существующий индекс
        if not force_rebuild and self.store.count() > 0:
            print(f"✓ Index already exists: {self.store.count()} documents")
            return self.store.count()
        
        print(f"📚 Loading documents from {self.vault_path}...")
        documents = self.loader.load_all()
        print(f"  Found {len(documents)} documents")
        
        # Chunking
        chunks = self._chunk_documents(documents)
        print(f"  Created {len(chunks)} chunks")
        
        # Создать ID и эмбеддинги
        ids = []
        texts = []
        metadatas = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = self._generate_id(chunk["content"], i)
            ids.append(chunk_id)
            texts.append(chunk["content"])
            metadatas.append(chunk["metadata"])
        
        # Эмбеддинги
        print("  Creating embeddings...")
        embeddings = self.embedder.embed_documents(texts)
        
        # Сохранить
        print("  Saving to ChromaDB...")
        self.store.add_documents(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
        
        print(f"✓ Indexed {len(chunks)} chunks")
        return len(chunks)
    
    def _chunk_documents(self, documents: List) -> List[dict]:
        """Разбить документы на чанки"""
        chunks = []
        
        for doc in documents:
            content = doc.content
            metadata = doc.metadata
            
            # Простой chunking по абзацам
            paragraphs = content.split("\n\n")
            current_chunk = ""
            
            for para in paragraphs:
                para = para.strip()
                if not para:
                    continue
                
                if len(current_chunk) + len(para) < self.chunk_size:
                    current_chunk += para + "\n\n"
                else:
                    if current_chunk.strip():
                        chunks.append({
                            "content": current_chunk.strip(),
                            "metadata": metadata.copy()
                        })
                    current_chunk = para + "\n\n"
            
            # Последний чанк
            if current_chunk.strip():
                chunks.append({
                    "content": current_chunk.strip(),
                    "metadata": metadata.copy()
                })
        
        return chunks
    
    def _generate_id(self, content: str, index: int) -> str:
        """Генерация уникального ID для чанка"""
        hash_str = hashlib.sha256(
            f"{content[:100]}{index}".encode()
        ).hexdigest()[:16]
        return f"chunk_{index}_{hash_str}"
    
    def retrieve(self, query: str, **kwargs) -> List:
        """Найти релевантные чанки"""
        return self.retriever.retrieve(query, **kwargs)
    
    def get_context(self, query: str, **kwargs) -> str:
        """Получить контекст для LLM"""
        return self.retriever.get_context_for_query(query, **kwargs)
    
    def get_stats(self) -> dict:
        """Статистика индекса"""
        return {
            "document_count": self.store.count(),
            "vault_path": str(self.vault_path),
            "persist_dir": str(self.persist_dir),
            "embedding_model": self.embedder.model_name,
            "chunk_size": self.chunk_size
        }


def main():
    """CLI для индексации"""
    parser = argparse.ArgumentParser(description="Index Obsidian Vault to RAG")
    parser.add_argument(
        "--vault",
        default="/home/workspace/obsidian-sync",
        help="Path to Obsidian Vault"
    )
    parser.add_argument(
        "--output",
        default="./data/rag_index",
        help="Output directory for ChromaDB"
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Force rebuild index"
    )
    
    args = parser.parse_args()
    
    kb = ObsidianKnowledgeBase(
        vault_path=args.vault,
        persist_dir=args.output
    )
    
    count = kb.build_index(force_rebuild=args.rebuild)
    print(f"\n📊 Stats: {kb.get_stats()}")


if __name__ == "__main__":
    main()
