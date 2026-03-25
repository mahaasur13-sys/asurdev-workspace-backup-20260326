# RAG Tools — AstroFin Sentinel
---
version: "1.0.0"
depends_on: "rag/indexer.py"
---

```python
"""
AstroFin Sentinel — RAG Tools
=============================
Инструменты поиска в базе знаний. Доступны всем агентам через LangChain tool decorator.

Usage:
    from rag.tools import retrieve_knowledge, retrieve_astrology, retrieve_agent_guide

    # Привязка к агенту
    tools = [retrieve_knowledge]  # agent_role передаётся из AgentContext
    agent = create_react_agent(model, tools)
"""

from __future__ import annotations

from typing import Literal, Optional

from langchain_core.runnables import Runnable
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma

from rag.indexer import DB_PATH, EMBEDDING_MODEL


# ─── Vector Store (lazy init) ──────────────────────────────

_vectorstore: Optional[Chroma] = None


def _get_vectorstore() -> Chroma:
    """Lazy singleton — открывает Chroma только при первом вызове."""
    global _vectorstore
    if _vectorstore is None:
        _vectorstore = Chroma(
            persist_directory=str(DB_PATH),
            embedding_function=OpenAIEmbeddings(model=EMBEDDING_MODEL),
        )
    return _vectorstore


def _build_retriever(
    agent_role: Optional[str] = None,
    topic: Optional[str] = None,
    category: Optional[str] = None,
    k: int = 6,
) -> Chroma:
    """
    Фабрика retriever с фильтрами.

    Args:
        agent_role:  Роль агента (MuhurtaSpecialist, AstroSpecialist, ...)
        topic:       Ключевая тема (nakshatra_trading, moon_signals, ...)
        category:    Категория (agent, astrology, global, reference)
        k:           Число результатов

    Returns:
        Chroma retriever с применёнными фильтрами
    """
    vs = _get_vectorstore()

    # Строим filter dict
    filter_dict = {}
    if agent_role:
        filter_dict["agent_role"] = agent_role
    if topic:
        filter_dict["topics"] = {"$contains": topic}
    if category:
        filter_dict["category"] = category

    return vs.as_retriever(
        search_kwargs={
            "k": k,
            "filter": filter_dict if filter_dict else None,
        }
    )


# ─── Core RAG Tool ─────────────────────────────────────────

@tool
def retrieve_knowledge(
    query: str,
    agent_role: str = "global",
    k: int = 6,
) -> str:
    """
    Поиск в базе знаний AstroFin Sentinel.

    Используй для:
    - Правил Панчанги, Мухурты, Чохгадии
    - Инструкций конкретного агента
    - Общих принципов (риск-менеджмент, этика, веса сигналов)
    - Справочных данных (эфемериды, планетные данные)

    Args:
        query:       Поисковый запрос на естественном языке
        agent_role:  Роль агента для фильтрации (global, MuhurtaSpecialist,
                     AstroSpecialist, MarketAnalyst, BullResearcher,
                     BearResearcher, Synthesizer). По умолчанию 'global'
        k:           Число возвращаемых чанков (default: 6)

    Returns:
        Текст из найденных чанков, разделённых ---

    Примеры:
        retrieve_knowledge(
            query="Best time to enter LONG on BTC according to Moon phase",
            agent_role="MuhurtaSpecialist"
        )
        retrieve_knowledge(
            query="Weight distribution technical vs astrology signals",
            agent_role="global"
        )
    """
    retriever = _build_retriever(agent_role=agent_role, k=k)
    docs = retriever.invoke(query)

    if not docs:
        return (
            "⚠️ Ничего не найдено в базе знаний по запросу. "
            "Попробуй обобщить запрос или спроси без фильтра по роли."
        )

    return "\n\n---\n\n".join(doc.page_content for doc in docs)


# ─── Specialized RAG Tools ────────────────────────────────

@tool
def retrieve_astrology(
    query: str,
    aspect: Literal["moon", "nakshatra", "planetary", "choghadiya", "muhurta", "house"] = "moon",
    k: int = 5,
) -> str:
    """
    Поиск астрологических данных и правил.

    Используй для:
    - Лунных сигналов и фаз Луны
    - Накшатр и их торговых характеристик
    - Планетных аспектов и транзитов
    - Чохгадии (благоприятные периоды дня)
    - Мухурты (электоральная астрология)
    - Домов и их сигнификаций для финансов

    Args:
        query:    Поисковый запрос (астрологическая тема)
        aspect:   Категория астрологии для фильтрации
        k:        Число возвращаемых чанков (default: 5)

    Returns:
        Текст с астрологическими правилами и данными
    """
    topic_map = {
        "moon":      ["moon_signals", "lunar_cycles"],
        "nakshatra": ["nakshatra_trading", "lunar_stations"],
        "planetary": ["planetary_transits", "aspects"],
        "choghadiya": ["choghadiya_timing", "timing"],
        "muhurta":   ["muhurta", "electional_astrology"],
        "house":     ["house_significations", "sign_benefics"],
    }

    topics = topic_map.get(aspect, ["astrology"])
    results = []

    for topic in topics:
        retriever = _build_retriever(topic=topic, category="astrology", k=k)
        docs = retriever.invoke(query)
        results.extend(docs)

    # Deduplicate по page_content
    seen = set()
    unique = []
    for doc in results:
        key = doc.page_content[:100]
        if key not in seen:
            seen.add(key)
            unique.append(doc)

    if not unique:
        return f"⚠️ Астрологические данные по '{aspect}' не найдены."

    return "\n\n---\n\n".join(doc.page_content for doc in unique[:k])


@tool
def retrieve_agent_guide(
    query: str,
    agent_role: Literal[
        "MuhurtaSpecialist",
        "PanchangaSpecialist",
        "MarketAnalyst",
        "BullResearcher",
        "BearResearcher",
        "AstroSpecialist",
        "Synthesizer",
    ] = "MarketAnalyst",
    k: int = 4,
) -> str:
    """
    Поиск инструкций и гайдов конкретного агента.

    Используй для:
    - Уточнения роли и обязанностей агента
    - Правил генерации рекомендаций
    - Примеров good/bad responses
    - Калибровки стиля ответа

    Args:
        query:      Поисковый запрос
        agent_role: Роль агента (по умолчанию MarketAnalyst)
        k:          Число возвращаемых чанков (default: 4)

    Returns:
        Инструкции и примеры из knowledge base для данного агента
    """
    retriever = _build_retriever(agent_role=agent_role, category="agent", k=k)
    docs = retriever.invoke(query)

    if not docs:
        return f"⚠️ Инструкции для {agent_role} не найдены."

    return "\n\n---\n\n".join(doc.page_content for doc in docs)


# ─── Tool Registry ─────────────────────────────────────────

# Все инструменты — для регистрации в LangChain agent
ALL_TOOLS = [
    retrieve_knowledge,
    retrieve_astrology,
    retrieve_agent_guide,
]

TOOL_BY_ROLE: dict[str, list[Runnable]] = {
    "MuhurtaSpecialist": [retrieve_knowledge, retrieve_astrology],
    "PanchangaSpecialist": [retrieve_knowledge, retrieve_astrology],
    "MarketAnalyst": [retrieve_knowledge, retrieve_astrology],
    "BullResearcher": [retrieve_knowledge],
    "BearResearcher": [retrieve_knowledge],
    "AstroSpecialist": [retrieve_knowledge, retrieve_astrology, retrieve_agent_guide],
    "Synthesizer": [retrieve_knowledge, retrieve_agent_guide],
}
```

---

## Использование в агентах

```python
# ── LangChain ReAct Agent ────────────────────────────────

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain import hub

from rag.tools import retrieve_knowledge, TOOL_BY_ROLE

# Для AstroSpecialist
model = ChatOpenAI(model="gpt-4o", temperature=0.3)
tools = TOOL_BY_ROLE["AstroSpecialist"]

agent = create_react_agent(model, tools)
executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Вызов с передачей agent_role через input
result = executor.invoke({
    "input": (
        "What is the best Muhurta for entering a LONG position on BTC? "
        "Use retrieve_astrology for timing rules."
    )
})


# ── Tool Call с явной ролью ─────────────────────────────

from rag.tools import retrieve_knowledge, retrieve_astrology, retrieve_agent_guide

# Глобальный поиск
result = retrieve_knowledge.invoke({
    "query": "risk management rules",
    "agent_role": "global"
})

# Астрология Луны
result = retrieve_astrology.invoke({
    "query": "New Moon trading strategy",
    "aspect": "moon"
})

# Инструкции агенту
result = retrieve_agent_guide.invoke({
    "query": "how to construct bullish thesis",
    "agent_role": "BullResearcher"
})
```

---

## Tool Schemas (для OpenAI function calling)

```json
retrieve_knowledge: {
  "name": "retrieve_knowledge",
  "description": "Search AstroFin Sentinel knowledge base for Panchanga, Muhurta, Choghadiya rules or agent instructions.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {"type": "string", "description": "Natural language search query"},
      "agent_role": {"type": "string", "enum": ["global", "MuhurtaSpecialist", "PanchangaSpecialist", "MarketAnalyst", "BullResearcher", "BearResearcher", "AstroSpecialist", "Synthesizer"]},
      "k": {"type": "integer", "default": 6}
    },
    "required": ["query"]
  }
}

retrieve_astrology: {
  "name": "retrieve_astrology",
  "description": "Search astrology knowledge base for lunar signals, nakshatras, planetary aspects, choghadiya, muhurta.",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {"type": "string"},
      "aspect": {"type": "string", "enum": ["moon", "nakshatra", "planetary", "choghadiya", "muhurta", "house"]},
      "k": {"type": "integer", "default": 5}
    },
    "required": ["query", "aspect"]
  }
}
```

---

## Next Steps

| Шаг | Файл | Описание |
|-----|------|----------|
| **3** | `agents/base.py` | Базовый класс агента с tool binding |
| **4** | `agents/market_analyst.py` | MarketAnalyst с TA (ta-lib/pandas) |
| **5** | `agents/astro_specialist.py` | AstroSpecialist с Swiss Ephemeris |
| **6** | `orchestration/graph.py` | LangGraph state + conditional routing |
