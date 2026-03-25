"""
AstroFin Sentinel — Base Agent Framework
=========================================
Все агенты наследуются от BaseAgent и следуют протоколу:
1. Загружают инструкции из {agent_name}_instructions.md
2. Могут запрашивать RAG через retrieve_knowledge
3. Возвращают структурированный AgentResult
"""

from __future__ import annotations
import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


# ──────────────────────────────────────────────
# 1. КОНТРАКТЫ (из contracts/sentinel_state.py)
# ──────────────────────────────────────────────

class Confidence(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Action(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    SKIP = "SKIP"


@dataclass
class RawAstroData:
    timestamp_utc: str
    latitude: float
    longitude: float
    moon_sign: str = ""
    moon_degree: float = 0.0
    moon_phase: str = ""
    nakshatra: str = ""
    yoga: str = ""
    tithi: str = ""
    karana: str = ""
    choghadiya_type: str = ""
    choghadiya_window_start: str = ""
    choghadiya_window_end: str = ""
    is_auspicious: bool = False
    raw: dict = field(default_factory=dict)


@dataclass
class RawMarketData:
    symbol: str
    timeframe: str
    price: float
    volume_24h: float
    change_24h: float
    high_24h: float
    low_24h: float
    rsi: float = 0.0
    macd_signal: str = "neutral"
    trend: str = "neutral"
    support: float = 0.0
    resistance: float = 0.0
    raw_ohlcv: list = field(default_factory=list)


@dataclass
class AgentResult:
    agent_id: str
    agent_role: str
    status: str  # "success" | "error" | "skip"
    findings: dict = field(default_factory=dict)
    narrative: str = ""
    confidence: Confidence = Confidence.MEDIUM
    action_recommendation: Optional[Action] = None
    metadata: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    knowledge_sources: list[str] = field(default_factory=list)  # какие RAG chunk'и использовал


@dataclass
class SentinelState:
    # Контекст запроса
    request_id: str = ""
    symbol: str = ""
    timeframe: str = ""
    user_context: str = ""

    # Момент времени
    analysis_timestamp_utc: str = ""

    # Данные (заполняются на этапе сбора)
    astro: Optional[RawAstroData] = None
    market: Optional[RawMarketData] = None

    # Результаты агентов (заполняются по мере выполнения)
    market_analysis: Optional[AgentResult] = None
    bull_case: Optional[AgentResult] = None
    bear_case: Optional[AgentResult] = None
    astro_analysis: Optional[AgentResult] = None

    # Финальный синтез
    synthesis: Optional[AgentResult] = None

    # Маршрутизация
    next_agent: str = ""
    route_decision: str = ""
    errors: list[str] = field(default_factory=list)


# ──────────────────────────────────────────────
# 2. RAG RETRIEVAL (заглушка — заменить на Chroma/FAISS)
# ──────────────────────────────────────────────

class RAGRetriever:
    """Обёртка над векторной базой знаний. Используйте Chroma/FAISS в проде."""

    def __init__(self, kb_path: str = "knowledge_base"):
        self.kb_path = Path(kb_path)
        self._chunks: list[dict] = []
        # Заглушка — в проде: ChromaDB.from_texts(...)
        self._load_fallback_chunks()

    def _load_fallback_chunks(self):
        """Fallback чанки если БД не инициализирована."""
        self._chunks = [
            {"id": "ch_astro_001", "text": "Choghadiya — система деления дня на 8 частей. Amrita и Shubha — благоприятные типы."},
            {"id": "ch_astro_002", "text": "Muhurta — 1/30 часть дня (около 24 минуты). Используется для точного выбора момента."},
            {"id": "ch_astro_003", "text": "Panjanga — 5 факторов: день недели, Накшатра, Тидхи, Карана, Йога."},
            {"id": "ch_pattern_001", "text": "Бычий поглощение — паттерн разворота вверх. Stop под минимумом поглощённой свечи."},
            {"id": "ch_pattern_002", "text": "Медвежий захват — паттерн разворота вниз. Stop над максимумом захваченной свечи."},
            {"id": "ch_indicator_001", "text": "RSI > 70 — перекупленность. RSI < 30 — перепроданность."},
            {"id": "ch_indicator_002", "text": "MACD гистограмма показывает моментум. Переход через ноль — сигнал смены тренда."},
        ]

    def retrieve(self, query: str, top_k: int = 3) -> list[dict]:
        """
        Поиск релевантных чанков по запросу.
        query: конкретный вопрос (не "всё", а "правила выбора дня для...").
        """
        if not query or len(query) < 5:
            return []
        # Заглушка: тривиальное совпадение по ключевым словам
        query_lower = query.lower()
        scored = []
        for chunk in self._chunks:
            score = sum(1 for word in query_lower.split() if word in chunk["text"].lower())
            if score > 0:
                scored.append((score, chunk))
        scored.sort(reverse=True)
        return [c for _, c in scored[:top_k]]

    def add_chunk(self, chunk_id: str, text: str, metadata: dict | None = None):
        """Добавить новый чанк в базу."""
        self._chunks.append({
            "id": chunk_id,
            "text": text,
            "metadata": metadata or {}
        })


# ──────────────────────────────────────────────
# 3. БАЗОВЫЙ АГЕНТ
# ──────────────────────────────────────────────

class BaseAgent(ABC):
    """
    Базовый класс для всех агентов AstroFin Sentinel.
    
    Протокол:
    1. __init__ → загружает {role}_instructions.md
    2. execute(state) → выполняет анализ
    3. _rag_search(query) → запрашивает БЗ при необходимости
    """

    def __init__(
        self,
        agent_id: str,
        agent_role: str,
        instructions_path: str | Path | None = None,
        kb_path: str = "knowledge_base"
    ):
        self.agent_id = agent_id
        self.agent_role = agent_role
        self.rag = RAGRetriever(kb_path=kb_path)
        self.instructions_md = ""
        self._loaded = False

        # Загрузка инструкций
        if instructions_path:
            p = Path(instructions_path)
        else:
            # Ищем {role}_instructions.md рядом с модулем
            p = Path(__file__).parent / f"{agent_role}_instructions.md"

        if p.exists():
            self.instructions_md = p.read_text(encoding="utf-8")
            self._loaded = True

    def _rag_search(self, query: str, top_k: int = 3) -> list[dict]:
        """
        Правильный RAG-запрос. Вызывать при неуверенности
        или когда вопрос выходит за рамки известного.
        """
        chunks = self.rag.retrieve(query, top_k=top_k)
        return chunks

    def _format_knowledge_sources(self, queries_made: list[str], chunks_used: list[dict]) -> str:
        """Форматирует блок [Источник знаний] для ответа агента."""
        lines = ["[Источник знаний]"]
        lines.append(f"• Личный файл: {'да' if self._loaded else 'нет'}")
        if queries_made:
            lines.append(f"• RAG запросы: {', '.join(queries_made)}")
        if chunks_used:
            chunk_summaries = [f"{c['id']}: {c['text'][:80]}..." for c in chunks_used]
            lines.append(f"• Полезные чанки:")
            for s in chunk_summaries:
                lines.append(f"  — {s}")
        return "\n".join(lines)

    @abstractmethod
    def execute(self, state: SentinelState) -> AgentResult:
        """
        Основной метод. Принимает SentinelState, возвращает AgentResult.
        """
        ...
