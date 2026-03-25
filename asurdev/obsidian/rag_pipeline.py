"""Obsidian Vault RAG Pipeline"""
import re
import os
from pathlib import Path
from datetime import datetime

class VaultRAG:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.blocks = []
        self.metadata = {"files": 0, "blocks": 0, "tags": set()}
    
    def parse_properties(self, content: str) -> dict:
        """Parse YAML frontmatter properties"""
        props = {}
        match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if match:
            for line in match.group(1).split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    props[key.strip()] = val.strip()
        return props
    
    def extract_tags(self, content: str) -> list:
        """Extract #tags from content"""
        return re.findall(r'#([a-zA-Zа-яА-Я0-9_-]+)', content)
    
    def parse_block(self, line: str, file_path: str, block_id: int) -> dict:
        """Parse a block (line) into structured data"""
        # Remove page refs and clean
        clean = re.sub(r'\[\[([^\]]+)\]\]', r'\1', line)
        clean = re.sub(r'#([a-zA-Zа-яА-Я0-9_-]+)', r'\1', clean)
        
        return {
            "id": block_id,
            "content": clean.strip(),
            "original": line.strip(),
            "file": file_path,
            "tags": self.extract_tags(line),
            "timestamp": datetime.now().isoformat()
        }
    
    def scan_vault(self) -> dict:
        """Scan vault and extract blocks"""
        self.blocks = []
        self.metadata = {"files": 0, "blocks": 0, "tags": set()}
        block_id = 0
        
        for md_file in self.vault_path.rglob("*.md"):
            if ".obsidian" in str(md_file):
                continue
            
            self.metadata["files"] += 1
            try:
                content = md_file.read_text(encoding='utf-8')
                
                # Parse properties
                props = self.parse_properties(content)
                
                # Remove frontmatter and split into blocks
                content = re.sub(r'^---\n.*?\n---\n', '', content, flags=re.DOTALL)
                
                for line in content.split('\n'):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    block = self.parse_block(line, str(md_file.relative_to(self.vault_path)), block_id)
                    block["properties"] = props
                    self.blocks.append(block)
                    self.metadata["blocks"] += 1
                    self.metadata["tags"].update(block["tags"])
                    block_id += 1
                    
            except Exception as e:
                print(f"Error reading {md_file}: {e}")
        
        self.metadata["tags"] = list(self.metadata["tags"])
        return self.metadata
    
    def search(self, query: str, top_k: int = 5) -> list:
        """Simple keyword search"""
        query_words = query.lower().split()
        results = []
        
        for block in self.blocks:
            content_lower = block["content"].lower()
            score = sum(1 for w in query_words if w in content_lower)
            if score > 0:
                results.append((score, block))
        
        results.sort(key=lambda x: x[0], reverse=True)
        return [r[1] for r in results[:top_k]]
    
    def get_by_tag(self, tag: str) -> list:
        """Get all blocks with a specific tag"""
        return [b for b in self.blocks if tag in b["tags"]]
    
    def get_by_file(self, filename: str) -> list:
        """Get all blocks from a specific file"""
        return [b for b in self.blocks if filename in b["file"]]
    
    def summarize_vault(self) -> dict:
        """Get vault summary statistics"""
        files_by_dir = {}
        for block in self.blocks:
            directory = str(Path(block["file"]).parent)
            files_by_dir[directory] = files_by_dir.get(directory, 0) + 1
        
        return {
            "total_files": self.metadata["files"],
            "total_blocks": self.metadata["blocks"],
            "total_tags": len(self.metadata["tags"]),
            "top_tags": sorted(
                [(t, len(self.get_by_tag(t))) for t in self.metadata["tags"]], 
                key=lambda x: x[1], 
                reverse=True
            )[:20],
            "files_by_directory": dict(sorted(files_by_dir.items(), key=lambda x: x[1], reverse=True)[:10])
        }


if __name__ == "__main__":
    rag = VaultRAG("/home/workspace/obsidian-sync")
    meta = rag.scan_vault()
    print(f"=== VAULT SUMMARY ===")
    print(f"Files: {meta['files']}")
    print(f"Blocks: {meta['blocks']}")
    print(f"Tags: {len(meta['tags'])}")
    
    summary = rag.summarize_vault()
    print(f"\n=== TOP TAGS ===")
    for tag, count in summary["top_tags"][:10]:
        print(f"  #{tag}: {count}")
    
    # Test search
    print(f"\n=== SEARCH TEST: 'мухурта' ===")
    results = rag.search("мухурта")
    for r in results[:3]:
        print(f"  [{r['file']}] {r['content'][:100]}...")
