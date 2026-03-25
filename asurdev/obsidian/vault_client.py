"""Obsidian Vault RAG Client для интеграции с агентами"""
import requests
from typing import List, Dict, Optional
from urllib.parse import quote

class VaultClient:
    def __init__(self, base_url: str = "https://asurdev.zo.space"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def search(self, query: str, top_k: int = 5) -> Dict:
        """Поиск по vault"""
        url = f"{self.base_url}/api/vault/search"
        params = {"q": query, "top_k": top_k}
        resp = self.session.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    
    def by_tag(self, tag: str) -> Dict:
        """Фильтр по тегу"""
        url = f"{self.base_url}/api/vault/search"
        params = {"tag": tag}
        resp = self.session.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    
    def by_file(self, filename: str) -> Dict:
        """Фильтр по файлу"""
        url = f"{self.base_url}/api/vault/search"
        params = {"file": filename}
        resp = self.session.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    
    def get_related(self, query: str, top_k: int = 3) -> List[str]:
        """Получить связанные фрагменты как текст для контекста агента"""
        data = self.search(query, top_k)
        fragments = []
        for r in data.get("results", []):
            fragments.append(f"[{r['file']}] {r['content']}")
        return fragments


class ObsidianKnowledgeBase:
    """База знаний для агентов — использует локальный vault"""
    
    def __init__(self, vault_path: str = "/home/workspace/obsidian-sync"):
        self.vault_path = vault_path
        self.blocks = []
        self._loaded = False
    
    def load(self):
        """Загрузить vault в память"""
        import re
        from pathlib import Path
        
        self.blocks = []
        vault = Path(self.vault_path)
        
        for md_file in vault.rglob("*.md"):
            if ".obsidian" in str(md_file):
                continue
            
            try:
                content = md_file.read_text(encoding='utf-8')
                content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)
                
                for line in content.split('\n'):
                    line = line.strip()
                    if not line or len(line) < 10:
                        continue
                    
                    # Clean page refs
                    clean = re.sub(r'\[\[([^\]]+)\]\]', r'\1', line)
                    # Extract tags
                    tags = re.findall(r'#([a-zA-Zа-яА-Я0-9_-]+)', line)
                    
                    self.blocks.append({
                        "content": clean,
                        "file": str(md_file.relative_to(self.vault_path)),
                        "tags": tags
                    })
            except:
                continue
        
        self._loaded = True
        print(f"Loaded {len(self.blocks)} blocks from vault")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Поиск"""
        if not self._loaded:
            self.load()
        
        query_words = query.lower().split()
        results = []
        
        for block in self.blocks:
            content_lower = block["content"].lower()
            score = sum(1 for w in query_words if w in content_lower)
            if score > 0:
                results.append((score, block))
        
        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:top_k]]
    
    def get_context(self, query: str, max_chars: int = 2000) -> str:
        """Получить контекст для агента"""
        results = self.search(query, 5)
        context_parts = [f"=== Знания из Obsidian Vault ({len(results)} результатов) ==="]
        
        for r in results:
            context_parts.append(f"[{r['file']}] {r['content'][:300]}")
        
        context = "\n\n".join(context_parts)
        return context[:max_chars]


# Глобальный экземпляр
_kb: Optional[ObsidianKnowledgeBase] = None

def get_knowledge_base() -> ObsidianKnowledgeBase:
    global _kb
    if _kb is None:
        _kb = ObsidianKnowledgeBase()
        _kb.load()
    return _kb


if __name__ == "__main__":
    kb = get_knowledge_base()
    
    # Тест
    print("=== Search: 'мухурта' ===")
    results = kb.search("мухурта")
    for r in results[:3]:
        print(f"  [{r['file']}] {r['content'][:100]}...")
    
    print("\n=== Context for agent ===")
    ctx = kb.get_context("астрология")
    print(ctx[:500])
