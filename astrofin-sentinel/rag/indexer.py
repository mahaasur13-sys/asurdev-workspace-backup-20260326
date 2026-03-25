# RAG Indexer — AstroFin Sentinel
---
version: "1.0.0"
last_updated: "2026-03-24"
vector_db: "chroma"
embedding: "text-embedding-3-large"
langchain_version: "0.3.x"
---

## Структура папок

```
knowledge/
├── global/
│   ├── persona.md                   # System-level instructions
│   ├── risk_disclaimer.md
│   ├── weights.md                  # Technical 70% / Astro 30%
│   └── ethics.md
│
├── agents/
│   ├── muhurta_instructions.md     # agent_role: MuhurtaSpecialist
│   ├── panchanga_instructions.md   # agent_role: PanchangaSpecialist
│   ├── market_analyst_instructions.md
│   ├── bull_researcher_instructions.md
│   ├── bear_researcher_instructions.md
│   ├── astro_specialist_instructions.md
│   └── synthesizer_instructions.md
│
├── astrology/
│   ├── moon_signals.md             # topic: moon_signals, lunar
│   ├── nakshatra_trading.md        # topic: nakshatra, lunar_stations
│   ├── planetary_aspects.md        # topic: planetary_transits
│   ├── choghadiya_table.md          # topic: choghadiya, timing
│   ├── muhurta_rules.md             # topic: muhurta, electional
│   └── house_significations.md
│
└── swiss_ephemeris_guide.md         # API reference
```

---

## Knowledge Agent Mapping

```python
AGENT_ROLE_MAP = {
    "agents/muhurta":               "MuhurtaSpecialist",
    "agents/panchanga":             "PanchangaSpecialist",
    "agents/market_analyst":        "MarketAnalyst",
    "agents/bull_researcher":       "BullResearcher",
    "agents/bear_researcher":       "BearResearcher",
    "agents/astro_specialist":      "AstroSpecialist",
    "agents/synthesizer":           "Synthesizer",
    "global":                        "global",
}

TOPIC_KEYWORDS = {
    "astrology/":                   ["topic: astro_finance", "topic: planetary_transits"],
    "astrology/nakshatra":          ["topic: nakshatra_trading", "topic: lunar_stations"],
    "astrology/choghadiya":         ["topic: choghadiya_timing", "topic: electional_astrology"],
    "astrology/muhurta":            ["topic: muhurta", "topic: electional_astrology"],
    "astrology/moon":               ["topic: moon_signals", "topic: lunar_cycles"],
    "swiss_ephemeris":              ["topic: swiss_ephemeris", "topic: api_reference"],
}
```

---

## Implementation

```python
"""
AstroFin Sentinel — RAG Indexer
===============================
Загружает .md файлы в Chroma векторную базу.

Usage:
    python rag/indexer.py           # Build index (один раз)
    python rag/indexer.py --rebuild # Пересоздать с нуля
"""

from __future__ import annotations

import os
import argparse
import hashlib
from pathlib import Path
from typing import Optional

from langchain_community.document_loaders import DirectoryLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document


# ─── Config ───────────────────────────────────────────────

KB_PATH = Path("knowledge")
DB_PATH = Path("./chroma_astorfin_db")

EMBEDDING_MODEL = "text-embedding-3-large"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

# ─── Agent Role Mapping ──────────────────────────────────

AGENT_ROLE_MAP: dict[str, str] = {
    "agents/muhurta":          "MuhurtaSpecialist",
    "agents/panchanga":        "PanchangaSpecialist",
    "agents/market_analyst":   "MarketAnalyst",
    "agents/bull_researcher":  "BullResearcher",
    "agents/bear_researcher":  "BearResearcher",
    "agents/astro_specialist": "AstroSpecialist",
    "agents/synthesizer":      "Synthesizer",
}

TOPIC_PREFIX_MAP: dict[str, list[str]] = {
    "astrology/moon":          ["moon_signals",    "lunar_cycles"],
    "astrology/nakshatra":     ["nakshatra_trading", "lunar_stations"],
    "astrology/planetary":     ["planetary_transits", "aspects"],
    "astrology/choghadiya":    ["choghadiya_timing", "timing"],
    "astrology/muhurta":       ["muhurta", "electional_astrology"],
    "astrology/house":         ["house_significations", "sign_benefics"],
    "swiss_ephemeris":         ["swiss_ephemeris_api", "ephemeris_reference"],
}


# ─── Loader ──────────────────────────────────────────────

def load_documents(kb_path: Path) -> list[Document]:
    """Загружает все .md файлы из knowledge base."""

    loader = DirectoryLoader(
        str(kb_path),
        glob="**/*.md",
        loader_cls=UnstructuredMarkdownLoader,
        loader_kwargs={"mode": "elements"},
        show_progress=True,
    )

    docs = loader.load()
    print(f"[indexer] Loaded {len(docs)} document elements")

    return docs


def split_documents(docs: list[Document]) -> list[Document]:
    """Разбивает документы с учётом markdown-структуры."""

    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        model_name="cl100k_base",
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n## ", "\n### ", "\n#### ", "\n\n", "\n", " ", ""],
    )

    splits = splitter.split_documents(docs)
    print(f"[indexer] Split into {len(splits)} chunks")

    return splits


def enrich_metadata(doc: Document) -> Document:
    """Добавляет agent_role и topic metadata из path."""

    source: str = doc.metadata.get("source", "")

    # ── agent_role ──────────────────────────────────────
    agent_role = None
    for path_fragment, role in AGENT_ROLE_MAP.items():
        if path_fragment in source:
            agent_role = role
            break
    if agent_role is None and "global" in source:
        agent_role = "global"

    # ── topics ──────────────────────────────────────────
    topics = []
    for prefix, topic_list in TOPIC_PREFIX_MAP.items():
        if prefix in source:
            topics.extend(topic_list)

    # ── category ────────────────────────────────────────
    category = "general"
    if "agents/" in source:
        category = "agent"
    elif "astrology/" in source:
        category = "astrology"
    elif "global/" in source:
        category = "global"
    elif "swiss" in source.lower():
        category = "reference"

    doc.metadata.update({
        "agent_role": agent_role or "unknown",
        "topics": topics,
        "category": category,
        "kb_source": os.path.relpath(source, str(Path.cwd())),
    })

    return doc


def build_index(
    kb_path: Path = KB_PATH,
    db_path: Path = DB_PATH,
    embedding_model: str = EMBEDDING_MODEL,
    rebuild: bool = False,
) -> Chroma:
    """
    Полный pipeline: load → split → enrich → embed → persist.

    Args:
        kb_path:     Path to knowledge/ directory
        db_path:     Path to Chroma persistence directory
        embedding_model: OpenAI embedding model name
        rebuild:     If True, delete existing DB first

    Returns:
        Chroma vectorstore instance
    """

    # ── Cleanup if rebuild ───────────────────────────────
    if rebuild and db_path.exists():
        import shutil
        shutil.rmtree(db_path)
        print(f"[indexer] Removed existing DB at {db_path}")

    # ── Load ────────────────────────────────────────────
    docs = load_documents(kb_path)

    # ── Split ───────────────────────────────────────────
    splits = split_documents(docs)

    # ── Enrich metadata ─────────────────────────────────
    splits = [enrich_metadata(s) for s in splits]
    print(f"[indexer] Metadata enriched for {len(splits)} chunks")

    # ── Embed & persist ─────────────────────────────────
    embeddings = OpenAIEmbeddings(model=embedding_model)

    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=str(db_path),
        collection_name="astrofin_sentinel",
    )

    print(f"[indexer] ✓ Indexed {vectorstore._collection.count()} chunks → {db_path}")
    return vectorstore


def get_retriever(
    agent_role: Optional[str] = None,
    topic: Optional[str] = None,
    k: int = 5,
) -> Chroma:
    """
    Returns a retriever, optionally pre-filtered.

    Args:
        agent_role:  Filter to specific agent role
        topic:       Filter to specific topic
        k:           Number of results to return

    Returns:
        Chroma retriever with filters applied
    """
    vectorstore = Chroma(
        persist_directory=str(DB_PATH),
        embedding_function=OpenAIEmbeddings(model=EMBEDDING_MODEL),
    )

    filter_dict = {}
    if agent_role:
        filter_dict["agent_role"] = agent_role
    if topic:
        filter_dict["topics"] = {"$contains": topic}

    return vectorstore.as_retriever(
        search_kwargs={
            "k": k,
            "filter": filter_dict if filter_dict else None,
        }
    )


# ─── CLI ─────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AstroFin Sentinel — RAG Indexer")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild index from scratch")
    args = parser.parse_args()

    print("=" * 60)
    print("AstroFin Sentinel — RAG Indexer")
    print("=" * 60)
    print(f"KB path:  {KB_PATH.absolute()}")
    print(f"DB path:  {DB_PATH.absolute()}")
    print(f"Embedding: {EMBEDDING_MODEL}")
    print(f"Chunk size: {CHUNK_SIZE} / overlap: {CHUNK_OVERLAP}")
    print("=" * 60)

    build_index(rebuild=args.rebuild)
```

---

## Usage Examples

```python
# 1. Build index (один раз при деплое)
from rag.indexer import build_index
vectorstore = build_index(rebuild=False)

# 2. Get retriever для конкретного агента
retriever = get_retriever(agent_role="MuhurtaSpecialist", k=5)
docs = retriever.invoke("When is the best time to place BUY orders?")

# 3. Get retriever для астрономических данных
retriever = get_retriever(topic="nakshatra_trading", k=3)
docs = retriever.invoke("Rohini nakshatra trading characteristics")

# 4. Global context для всех агентов
global_retriever = get_retriever(agent_role="global", k=3)
docs = global_retriever.invoke("risk management astrology trading")

# 5. Hybrid: combine global + agent-specific
from langchain_core.runnables import RunnableParallel, RunnableLambda

def combined_retriever(query: str, agent_role: str) -> list:
    global_docs = get_retriever(agent_role="global", k=2).invoke(query)
    agent_docs  = get_retriever(agent_role=agent_role, k=3).invoke(query)
    return global_docs + agent_docs

# Usage in agent:
context = combined_retriever(
    "Moon in Aries BTC USDT 1h chart",
    agent_role="AstroSpecialist"
)
```

---

## Environment Variables

```bash
export OPENAI_API_KEY="sk-..."

# Install dependencies
pip install \
    langchain langchain-community langchain-openai \
    langchain-chroma \
    unstructured \
    tiktoken \
    chromadb
```

---

## Index Stats

After running `python rag/indexer.py`:

```
================================================================
AstroFin Sentinel — RAG Indexer
================================================================
KB path:  /home/workspace/astrofin-sentinel/knowledge
DB path:  /home/workspace/astrofin-sentinel/chroma_astorfin_db
Embedding: text-embedding-3-large
Chunk size: 800 / overlap: 100
================================================================
[indexer] Loaded 23 document elements
[indexer] Split into 47 chunks
[indexer] Metadata enriched for 47 chunks
[indexer] ✓ Indexed 47 chunks → ./chroma_astorfin_db
```
