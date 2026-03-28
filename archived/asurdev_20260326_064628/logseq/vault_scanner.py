"""Logseq Vault Scanner - Parse Logseq markdown files"""
import re
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

def scan_logseq_vault(vault_path: str) -> List[Dict[str, Any]]:
    """
    Scan Logseq vault for pages and blocks.
    
    Returns list of pages with:
    - title: Page title
    - path: File path
    - blocks: List of content blocks
    - properties: YAML frontmatter
    - tags: Extracted tags
    """
    vault = Path(vault_path)
    if not vault.exists():
        return []
    
    pages = []
    
    # Scan for markdown and org files
    for pattern in ["*.md", "*.org", "**/*.md", "**/*.org"]:
        for file_path in vault.glob(pattern):
            if file_path.is_file() and not file_path.name.startswith("."):
                page = parse_logseq_file(file_path)
                if page:
                    pages.append(page)
    
    return pages

def parse_logseq_file(file_path: Path) -> Dict[str, Any]:
    """Parse a single Logseq file"""
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return None
    
    blocks = []
    properties = {}
    title = file_path.stem
    
    # Parse frontmatter
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1]
            content = parts[2]
            
            for line in frontmatter.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    properties[key.strip()] = value.strip()
            
            if "title" in properties:
                title = properties["title"]
    
    # Extract blocks (paragraphs, headings, lists)
    current_block = []
    in_code_block = False
    
    for line in content.split("\n"):
        # Track code blocks
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        
        if in_code_block:
            continue
        
        # Empty line = new block
        if not line.strip():
            if current_block:
                blocks.append(" ".join(current_block))
                current_block = []
            continue
        
        # Remove Logseq specific syntax
        line = re.sub(r"^\s*[-*+]\s+", "", line)  # List markers
        line = re.sub(r"^\s*#+\s+", "", line)       # Headings
        line = re.sub(r"\[\[([^\]]+)\]\]", r"\1", line)  # Wiki links
        line = re.sub(r"\[\[([^\]]+)\|([^\]]+)\]\]", r"\2", line)  # Alias links
        
        current_block.append(line.strip())
    
    # Add last block
    if current_block:
        blocks.append(" ".join(current_block))
    
    # Extract tags
    tags = set()
    for block in blocks:
        tags.update(re.findall(r"#[a-zA-Z0-9_-]+", block))
    
    return {
        "title": title,
        "path": str(file_path),
        "blocks": [b for b in blocks if b],
        "properties": properties,
        "tags": list(tags),
        "created": properties.get("created", ""),
        "updated": properties.get("updated", datetime.now().isoformat())
    }

def extract_backlinks(content: str) -> List[str]:
    """Extract backlinks from content"""
    return re.findall(r"\[\[([^\]]+)\]\]", content)
