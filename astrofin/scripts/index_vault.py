#!/usr/bin/env python3
"""Индексировать Obsidian vault в RAG базу знаний."""
import sys
sys.path.insert(0, '/home/workspace/astrofin')

from knowledge.rag.obsidian_loader import get_obsidian_loader
import json


def main():
    print("🔍 Loading Obsidian vault...")
    
    loader = get_obsidian_loader("/home/workspace/obsidian-sync")
    docs = loader.load_all()
    
    stats = loader.get_stats()
    print(f"\n📊 Loaded {stats['total_documents']} documents")
    print(f"   Domains: {stats['domains']}")
    print(f"   Total size: {stats['total_size'] / 1024:.1f} KB")
    print(f"   Indexed words: {stats['indexed_words']}")
    
    # Show sample by domain
    print("\n📁 Sample documents by domain:")
    for domain in ["astrology/vedic", "astrology/western", "technical", "trading"]:
        domain_docs = [d for d in docs if d.domain == domain][:3]
        if domain_docs:
            print(f"\n   {domain}:")
            for doc in domain_docs:
                print(f"      - {doc.title} ({len(doc.content)} chars)")
    
    # Test search
    print("\n🔎 Test search:")
    for query in ["nakshatra", "muhurta", "RSI", "andrews"]:
        results = loader.search(query, limit=3)
        print(f"\n   Query: '{query}' → {len(results)} results")
        for r in results[:2]:
            print(f"      - {r.title} (score: {r.source})")
    
    # Save index
    index_path = "/home/workspace/astrofin/knowledge/rag/index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump({
            "stats": stats,
            "documents": [d.to_dict() for d in docs]
        }, f, ensure_ascii=False, indent=2)
    print(f"\n✅ Index saved to {index_path}")


if __name__ == "__main__":
    main()
