"""Logseq Agent - Knowledge Base Integration"""
import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

@dataclass
class LogseqAgent:
    """Agent for Logseq knowledge base integration with RAG"""
    name: str = "LogseqAgent"
    vault_path: Optional[str] = None
    indexes: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.vault_path is None:
            self.vault_path = os.environ.get("LOGSEQ_VAULT_PATH", "~/logseq")
        self.indexes = {}
    
    def index_vault(self, force: bool = False) -> Dict[str, int]:
        """Index the Logseq vault for RAG"""
        from .vault_scanner import scan_logseq_vault
        from .rag_pipeline import create_logseq_rag
        
        vault_path = Path(self.vault_path).expanduser()
        if not vault_path.exists():
            return {"error": "Vault not found", "pages": 0, "blocks": 0}
        
        pages = scan_logseq_vault(str(vault_path))
        if pages:
            self.indexes["main"] = create_logseq_rag(pages)
            return {"pages": len(pages), "blocks": sum(len(p["blocks"]) for p in pages)}
        return {"pages": 0, "blocks": 0}
    
    def query(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Query the knowledge base"""
        if "main" not in self.indexes:
            return []
        return self.indexes["main"].query(query, limit)
    
    def add_page(self, title: str, content: str, properties: Dict = None) -> bool:
        """Add a new page to the vault"""
        vault_path = Path(self.vault_path).expanduser()
        page_path = vault_path / f"{title}.md"
        if page_path.exists():
            return False
        
        with open(page_path, "w") as f:
            f.write(f"---\ntitle: {title}\ncreated: {datetime.now().isoformat()}\n")
            if properties:
                for k, v in properties.items():
                    f.write(f"{k}: {v}\n")
            f.write("---\n\n")
            f.write(content)
        
        if "main" in self.indexes:
            self.indexes["main"].add_document(title, content)
        return True

_logseq_agent: Optional[LogseqAgent] = None

def get_logseq_agent() -> LogseqAgent:
    """Get or create the Logseq agent singleton"""
    global _logseq_agent
    if _logseq_agent is None:
        _logseq_agent = LogseqAgent()
    return _logseq_agent
