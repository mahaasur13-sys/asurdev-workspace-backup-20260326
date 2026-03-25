"""
Obsidian Vault RAG Loader.
Загружает все markdown файлы из Obsidian vault и индексирует их.
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import hashlib


@dataclass
class Document:
    """Документ из RAG базы."""
    id: str
    title: str
    content: str
    source: str  # путь к файлу
    domain: str  # astrology, technical, trading, etc.
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content[:500],  # preview
            "source": self.source,
            "domain": self.domain,
            "tags": self.tags,
            "metadata": self.metadata,
        }


class ObsidianLoader:
    """
    Загружает и индексирует Obsidian vault.
    
    Использование:
        loader = ObsidianLoader("/path/to/obsidian-vault")
        docs = loader.load_all()
        docs = loader.load_by_domain("astrology")
        docs = loader.search("nakshatra")
    """
    
    DOMAIN_PATTERNS = {
        "astrology/vedic": ["мухурта", "накшатр", "vedic", "choghadiya", "muhurta", "nakshatra", "йог", "дasha", "даша"],
        "astrology/western": ["western", "lilly", "dignity", "aspect", "пик", "planetary"],
        "astrology/financial": ["financial", "trading", "market", "moon sign"],
        "technical": ["rsi", "macd", "bollinger", "pattern", "support", "resistance", "andrews", "gann", "elliot", "elliott"],
        "trading": ["position", "swing", "scalp", "risk", "management", "entry", "exit"],
        "general": [],  # default
    }
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self._documents: List[Document] = []
        self._index: Dict[str, List[int]] = {}  # word -> doc indices
        
    def _extract_title(self, content: str, filepath: Path) -> str:
        """Извлекает заголовок из markdown файла."""
        # Try frontmatter title
        match = re.search(r'^title:\s*(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        
        # Try first H1
        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()
        
        # Fallback to filename
        return filepath.stem
    
    def _detect_domain(self, content: str, filepath: Path) -> str:
        """Определяет домен документа."""
        content_lower = content.lower()
        filepath_str = str(filepath).lower()
        
        for domain, patterns in self.DOMAIN_PATTERNS.items():
            if not patterns:  # general
                continue
            if any(p in content_lower or p in filepath_str for p in patterns):
                return domain
        
        return "general"
    
    def _extract_tags(self, content: str) -> List[str]:
        """Извлекает теги из frontmatter или контента."""
        tags = []
        
        # Frontmatter tags
        match = re.search(r'^tags:\s*\[(.+)\]$', content, re.MULTILINE)
        if match:
            tags.extend([t.strip() for t in match.group(1).split(",")])
        
        # Inline tags #tag
        tags.extend(re.findall(r'#([a-zA-Zа-яА-ЯёЁ_-]+)', content))
        
        return list(set(tags))[:20]  # limit to 20
    
    def _clean_content(self, content: str) -> str:
        """Очищает контент от frontmatter и метаданных."""
        # Remove frontmatter
        content = re.sub(r'^---\n[\s\S]*?---\n', '', content)
        
        # Remove images
        content = re.sub(r'!\[[^\]]*\]\([^\)]+\)', '', content)
        
        # Remove HTML
        content = re.sub(r'<[^>]+>', '', content)
        
        # Collapse whitespace
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip()
    
    def _index_document(self, doc: Document) -> None:
        """Индексирует документ для быстрого поиска."""
        words = set(re.findall(r'[a-zA-Zа-яА-ЯёЁ]{3,}', doc.content.lower()))
        for word in words:
            if word not in self._index:
                self._index[word] = []
            self._index[word].append(len(self._documents) - 1)
    
    def load_file(self, filepath: Path) -> Optional[Document]:
        """Загружает один файл."""
        try:
            content = filepath.read_text(encoding="utf-8")
        except Exception:
            try:
                content = filepath.read_text(encoding="latin-1")
            except Exception:
                return None
        
        if len(content) < 50:  # Skip empty/small files
            return None
        
        title = self._extract_title(content, filepath)
        domain = self._detect_domain(content, filepath)
        tags = self._extract_tags(content)
        clean_content = self._clean_content(content)
        
        doc_id = hashlib.md5(f"{filepath}:{title}".encode()).hexdigest()[:12]
        
        doc = Document(
            id=doc_id,
            title=title,
            content=clean_content,
            source=str(filepath.relative_to(self.vault_path)),
            domain=domain,
            tags=tags,
            metadata={
                "size": len(content),
                "loaded_at": datetime.now().isoformat(),
            }
        )
        
        self._index_document(doc)
        return doc
    
    def load_all(self, recursive: bool = True) -> List[Document]:
        """Загружает все markdown файлы из vault."""
        self._documents = []
        self._index = {}
        
        pattern = "**/*.md" if recursive else "*.md"
        
        for filepath in self.vault_path.glob(pattern):
            # Skip hidden and system directories
            if any(part.startswith('.') for part in filepath.parts):
                continue
            
            doc = self.load_file(filepath)
            if doc:
                self._documents.append(doc)
        
        return self._documents
    
    def load_by_domain(self, domain: str) -> List[Document]:
        """Загружает только документы определённого домена."""
        if not self._documents:
            self.load_all()
        
        return [d for d in self._documents if d.domain == domain]
    
    def search(self, query: str, limit: int = 10) -> List[Document]:
        """Ищет документы по запросу."""
        if not self._documents:
            self.load_all()
        
        query_words = set(re.findall(r'[a-zA-Zа-яА-ЯёЁ]{3,}', query.lower()))
        
        scores: Dict[int, float] = {}
        for word in query_words:
            if word in self._index:
                for doc_idx in self._index[word]:
                    scores[doc_idx] = scores.get(doc_idx, 0) + 1
        
        # Sort by score
        sorted_indices = sorted(scores.keys(), key=lambda i: scores[i], reverse=True)
        
        return [self._documents[i] for i in sorted_indices[:limit]]
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику по загруженным документам."""
        if not self._documents:
            self.load_all()
        
        domain_counts: Dict[str, int] = {}
        for doc in self._documents:
            domain_counts[doc.domain] = domain_counts.get(doc.domain, 0) + 1
        
        return {
            "total_documents": len(self._documents),
            "domains": domain_counts,
            "total_size": sum(d.metadata.get("size", 0) for d in self._documents),
            "indexed_words": len(self._index),
        }


# Global loader instance
_obsidian_loader: Optional[ObsidianLoader] = None

def get_obsidian_loader(vault_path: str = "/home/workspace/obsidian-sync") -> ObsidianLoader:
    """Получить глобальный экземпляр ObsidianLoader."""
    global _obsidian_loader
    if _obsidian_loader is None:
        _obsidian_loader = ObsidianLoader(vault_path)
    return _obsidian_loader
