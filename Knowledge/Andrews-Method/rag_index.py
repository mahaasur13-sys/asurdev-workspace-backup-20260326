#!/usr/bin/env python3
"""
RAG Indexer для базы знаний методов Эндрюса
Использование: python rag_index.py
"""

import os
import json
from pathlib import Path

BASE_DIR = Path("/home/workspace/Knowledge/Andrews-Method")

def extract_frontmatter(content: str):
    """Извлекает YAML frontmatter из markdown"""
    if content.startswith('---'):
        end = content.find('---', 3)
        if end != -1:
            fm = content[3:end].strip()
            body = content[end+3:].strip()
            meta = {}
            for line in fm.split('\n'):
                if ':' in line:
                    key, val = line.split(':', 1)
                    meta[key.strip()] = val.strip().strip('"').strip("'")
            return meta, body
    return {}, content

def extract_tags(content: str):
    """Извлекает теги из markdown"""
    import re
    tags = re.findall(r'#[\w\u0400-\u04FF]+', content)
    return list(set(tags))

def extract_links(content: str):
    """Извлекает wiki-ссылки [[...]]"""
    import re
    links = re.findall(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]', content)
    return links

def chunk_text(text: str, chunk_size: int = 512):
    """Разбивает текст на чанки"""
    words = text.split()
    chunks = []
    current = []
    current_len = 0
    
    for word in words:
        current_len += len(word) + 1
        if current_len > chunk_size:
            chunks.append(' '.join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
    
    if current:
        chunks.append(' '.join(current))
    
    return chunks

def index_knowledge_base():
    """Индексирует всю базу знаний"""
    documents = []
    
    for md_file in BASE_DIR.rglob("*.md"):
        if "rag_index" in str(md_file):
            continue
            
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        meta, body = extract_frontmatter(content)
        tags = extract_tags(content)
        links = extract_links(content)
        chunks = chunk_text(body)
        
        relative_path = md_file.relative_to(BASE_DIR)
        
        for i, chunk in enumerate(chunks):
            doc = {
                "id": f"{relative_path}::{i}",
                "source": str(relative_path),
                "content": chunk,
                "tags": tags,
                "links": links,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "title": meta.get("title", meta.get("Конспект", relative_path.stem)),
            }
            documents.append(doc)
    
    index_path = BASE_DIR / "rag_index.json"
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)
    
    print(f"Indexed {len(documents)} chunks from {len(list(BASE_DIR.rglob('*.md')))} files")
    return documents

def search(query: str, top_k: int = 5):
    """Простой поиск по ключевым словам"""
    with open(BASE_DIR / "rag_index.json", 'r', encoding='utf-8') as f:
        documents = json.load(f)
    
    query_words = query.lower().split()
    results = []
    
    for doc in documents:
        score = sum(1 for w in query_words if w in doc['content'].lower())
        if score > 0:
            results.append((score, doc))
    
    results.sort(key=lambda x: x[0], reverse=True)
    return [r[1] for r in results[:top_k]]

if __name__ == "__main__":
    docs = index_knowledge_base()
    
    print("\n--- Test search: 'median line' ---")
    results = search("median line")
    for r in results:
        print(f"\n[{r['source']}] {r['title']}")
        print(f"   {r['content'][:200]}...")
