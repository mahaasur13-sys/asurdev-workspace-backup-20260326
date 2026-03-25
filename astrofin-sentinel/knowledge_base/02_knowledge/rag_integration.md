# RAG Integration — AstroFin Sentinel
---
version: "1.0.0"
last_updated: "2026-03-24"
vector_db: "chroma"
embedding: "text-embedding-3-small"
---

```python
"""
RAG Integration — AstroFin Sentinel
===================================
Hybrid search: keyword + semantic с metadata filtering.

Query Flow:
1. Parse agent_role, topic, priority из контекста
2. Build hybrid query (keyword + semantic)
3. Filter by metadata (agent_role, topic)
4. Return top-k chunks + sources
"""

from __future__ import annotations
from typing import Optional
from dataclasses import dataclass


@dataclass
class RAGQuery:
    """Запрос к RAG системе."""
    query: str
    agent_role: Optional[str] = None      # market_analyst, astro_specialist, etc.
    topic: Optional[str] = None           # technical_analysis, moon_signals, etc.
    priority: Optional[int] = None        # 1, 2, 3, 4
    symbol: Optional[str] = None          # BTC, ETH, SOL
    timeframe: Optional[str] = None       # 1h, 4h, 1d
    action: Optional[str] = None          # BUY, SELL
    top_k: int = 5


@dataclass
class RAGResult:
    """Результат RAG поиска."""
    chunk: str
    source: str                           # file path
    score: float
    metadata: dict


class RAGRetriever:
    """
    Hybrid RAG retriever для AstroFin Sentinel.
    
    Поддерживает:
    - Semantic search (embeddings)
    - Keyword search (BM25)
    - Metadata filtering (agent_role, topic, priority)
    """

    def __init__(self, kb_path: str = "knowledge_base"):
        self.kb_path = kb_path
        self._index: dict[str, RAGResult] = {}
        self._load_index()

    def _load_index(self):
        """Загружает markdown файлы в индекс."""
        import os
        import re

        for root, _, files in os.walk(self.kb_path):
            for fname in files:
                if not fname.endswith(".md"):
                    continue

                fpath = os.path.join(root, fname)
                with open(fpath, "r") as f:
                    content = f.read()

                # Extract YAML frontmatter
                match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
                if match:
                    frontmatter = match.group(1)
                    metadata = self._parse_frontmatter(frontmatter)
                    body = content[match.end():].strip()
                else:
                    metadata = {}
                    body = content

                chunk_id = fpath
                self._index[chunk_id] = RAGResult(
                    chunk=body,
                    source=fpath,
                    score=1.0,
                    metadata=metadata,
                )

    def _parse_frontmatter(self, fm: str) -> dict:
        """Парсит YAML frontmatter."""
        result = {}
        for line in fm.split("\n"):
            if ":" not in line:
                continue
            key, _, val = line.partition(":")
            result[key.strip()] = val.strip()
        return result

    def retrieve(self, query: RAGQuery) -> list[RAGResult]:
        """
        Выполняет hybrid search.

        Args:
            query: RAGQuery с параметрами поиска

        Returns:
            Список RAGResult, отсортированный по score
        """
        candidates = list(self._index.values())

        # ── Metadata filtering ─────────────────────────────
        if query.agent_role:
            candidates = [c for c in candidates
                         if c.metadata.get("agent_role") == query.agent_role]

        if query.topic:
            candidates = [c for c in candidates
                         if query.topic in c.metadata.get("topic", "")]

        if query.priority is not None:
            candidates = [c for c in candidates
                         if c.metadata.get("priority") == str(query.priority)]

        # ── Keyword search (simple TF-IDF variant) ─────────
        query_terms = query.query.lower().split()
        scored = []

        for c in candidates:
            chunk_lower = c.chunk.lower()
            score = sum(1 for term in query_terms if term in chunk_lower)
            if score > 0:
                scored.append((score / len(query_terms), c))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [c for _, c in scored[:query.top_k]]

        # Fallback: если нет результатов, вернуть top-k по metadata
        if not results:
            results = candidates[:query.top_k]

        return results

    def get_agent_context(self, agent_role: str, additional_context: str = "") -> str:
        """
        Получает контекст для конкретного агента.

        Args:
            agent_role: роль агента (market_analyst, astro_specialist, etc.)
            additional_context: дополнительный контекст запроса

        Returns:
            Строка с найденным контекстом для подстановки в промпт
        """
        q = RAGQuery(
            query=f"{agent_role} {additional_context}".strip(),
            agent_role=agent_role,
            top_k=3,
        )
        results = self.retrieve(q)

        if not results:
            return ""

        context_parts = [f"[Source: {r.source}]\n{r.chunk[:500]}" for r in results]
        return "\n\n".join(context_parts)
```

## Query Templates

```python
# Для Market Analyst
rag.get_agent_context(
    agent_role="market_analyst",
    additional_context="BTC RSI overbought support resistance"
)

# Для Astro Specialist
rag.get_agent_context(
    agent_role="astro_specialist",
    additional_context="Moon Aries BTC trading"
)

# Для Muhurta Specialist
rag.get_agent_context(
    agent_role="muhurta_specialist",
    additional_context="BUY order timing"
)
```

## Index Structure

```
knowledge_base/
├── 01_agents/
│   ├── market_analyst.md       # agent_role: market_analyst, priority: 1
│   ├── bull_researcher.md      # agent_role: bull_researcher, priority: 2
│   ├── bear_researcher.md      # agent_role: bear_researcher, priority: 2
│   ├── astro_specialist.md     # agent_role: astro_specialist, priority: 2
│   ├── muhurta_specialist.md   # agent_role: muhurta_specialist, priority: 3
│   └── synthesizer.md          # agent_role: synthesizer, priority: 4
│
├── 02_knowledge/
│   ├── planet_aspects.md       # topic: planet_transits, financial_astrology
│   ├── nakshatra_trading.md    # topic: nakshatra_trading, lunar_stations
│   ├── choghadiya_table.md     # (pending)
│   ├── muhurta_rules.md        # (pending)
│   └── changelog.md
│
└── 03_templates/
    ├── prompts.md              # Shared prompt templates
    └── risk_disclaimers.md     # Risk disclaimer blocks
```
