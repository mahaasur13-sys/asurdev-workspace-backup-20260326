"""Logseq RAG Pipeline - Embeddings and Vector Search"""
import os
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

class SimpleEmbedder:
    """Simple TF-IDF based embedder (no external dependencies)"""
    
    def __init__(self):
        self.vocab = {}
        self.idf = {}
    
    def fit(self, documents: List[str]):
        """Build vocabulary from documents"""
        word_doc_freq = {}
        total_docs = len(documents)
        
        for doc in documents:
            words = doc.lower().split()
            unique_words = set(words)
            for word in unique_words:
                word_doc_freq[word] = word_doc_freq.get(word, 0) + 1
        
        # Calculate IDF
        self.vocab = {word: i for i, word in enumerate(word_doc_freq.keys())}
        self.idf = {
            word: np.log(total_docs / freq) 
            for word, freq in word_doc_freq.items()
        }
    
    def embed(self, text: str) -> np.ndarray:
        """Create embedding vector for text"""
        words = text.lower().split()
        vec = np.zeros(len(self.vocab)) if self.vocab else np.zeros(100)
        word_count = 0
        
        for word in words:
            if word in self.vocab:
                vec[self.vocab[word]] += 1
                word_count += 1
        
        # TF-IDF normalization
        if word_count > 0:
            vec /= word_count
        
        for word in words:
            if word in self.idf:
                vec[self.vocab[word]] *= self.idf[word]
        
        # Normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        
        return vec

class SimpleVectorStore:
    """Simple in-memory vector store"""
    
    def __init__(self, embedder: SimpleEmbedder):
        self.embedder = embedder
        self.documents = []
        self.vectors = []
    
    def add(self, doc_id: str, text: str, metadata: Dict = None):
        """Add document to store"""
        self.documents.append({
            "id": doc_id,
            "text": text,
            "metadata": metadata or {}
        })
        self.vectors.append(self.embedder.embed(text))
    
    def search(self, query: str, limit: int = 5) -> List[Dict]:
        """Search for similar documents"""
        query_vec = self.embedder.embed(query)
        
        results = []
        for i, vec in enumerate(self.vectors):
            sim = np.dot(query_vec, vec)
            results.append((sim, i))
        
        # Sort by similarity
        results.sort(reverse=True)
        
        return [
            {
                **self.documents[i],
                "score": float(score)
            }
            for score, i in results[:limit]
        ]

class LogseqRAG:
    """RAG pipeline for Logseq knowledge base"""
    
    def __init__(self):
        self.embedder = SimpleEmbedder()
        self.store = None
        self.documents = []
    
    def index(self, pages: List[Dict[str, Any]]):
        """Index Logseq pages"""
        self.documents = []
        texts = []
        
        for page in pages:
            # Index full page content
            full_text = f"{page['title']} {' '.join(page.get('blocks', []))}"
            self.documents.append({
                "type": "page",
                "title": page["title"],
                "text": full_text,
                "metadata": page.get("properties", {})
            })
            texts.append(full_text)
            
            # Index individual blocks
            for i, block in enumerate(page.get("blocks", [])):
                block_text = f"{page['title']}: {block}"
                self.documents.append({
                    "type": "block",
                    "title": page["title"],
                    "block_id": i,
                    "text": block_text,
                    "metadata": {"block_index": i}
                })
                texts.append(block_text)
        
        # Fit embedder and create store
        self.embedder.fit(texts)
        self.store = SimpleVectorStore(self.embedder)
        
        for i, doc in enumerate(self.documents):
            self.store.add(f"doc_{i}", doc["text"], doc)
    
    def query(self, query: str, limit: int = 5) -> List[Dict]:
        """Query the knowledge base"""
        if not self.store:
            return []
        
        results = self.store.search(query, limit)
        
        # Format results
        formatted = []
        for r in results:
            formatted.append({
                "title": r["metadata"].get("title", "Unknown"),
                "type": r["metadata"].get("type", "page"),
                "text": r["text"][:200] + "..." if len(r["text"]) > 200 else r["text"],
                "score": r["score"]
            })
        
        return formatted
    
    def save(self, path: str):
        """Save index to disk"""
        import json
        index_path = Path(path)
        index_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "documents": self.documents,
            "vocab": self.embedder.vocab,
            "idf": self.embedder.idf
        }
        
        with open(index_path, "w") as f:
            json.dump(data, f)
    
    def load(self, path: str) -> bool:
        """Load index from disk"""
        import json
        index_path = Path(path)
        if not index_path.exists():
            return False
        
        try:
            with open(index_path) as f:
                data = json.load(f)
            
            self.documents = data["documents"]
            self.embedder.vocab = data.get("vocab", {})
            self.embedder.idf = data.get("idf", {})
            
            # Rebuild store
            self.store = SimpleVectorStore(self.embedder)
            for i, doc in enumerate(self.documents):
                self.store.add(f"doc_{i}", doc["text"], doc)
            
            return True
        except Exception:
            return False

def create_logseq_rag(pages: List[Dict[str, Any]]) -> LogseqRAG:
    """Create and index a Logseq RAG pipeline"""
    rag = LogseqRAG()
    rag.index(pages)
    return rag
