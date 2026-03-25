"""
AstroFin Sentinel v5 — Base Agent
RAG-first agent implementation with knowledge retrieval.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, TypeVar, Generic
from enum import Enum
import uuid
from datetime import datetime

from knowledge.rag_retriever import RAGRetriever, retrieve_knowledge


class SignalDirection(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"
    AVOID = "AVOID"


@dataclass
class AgentResponse:
    """Стандартный ответ каждого агента."""
    agent_name: str
    signal: SignalDirection
    confidence: float          # 0.0 — 1.0
    reasoning: str
    sources: list[str] = field(default_factory=list)  # RAG chunk IDs
    metadata: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    def to_dict(self) -> dict:
        # Handle both string signals (new) and enum signals (old)
        signal_value = self.signal.value if hasattr(self.signal, 'value') else self.signal
        return {
            "agent_name": self.agent_name,
            "signal": signal_value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "sources": self.sources,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "session_id": self.session_id,
        }


T = TypeVar("T", bound=AgentResponse)


class BaseAgent(ABC, Generic[T]):
    """
    Базовый класс для всех агентов v5.
    
    Каждый агент:
    1. Имеет instructions.md (загружается при инициализации)
    2. Может запрашивать RAG через self.retrieve()
    3. Возвращает AgentResponse
    """
    
    def __init__(
        self,
        name: str,
        instructions_path: str = None,
        domain: str = None,
        weight: float = 0.0,
    ):
        self.name = name
        self.weight = weight
        self.domain = domain
        self.instructions_md = ""
        self._rag = RAGRetriever()
        
        if instructions_path:
            try:
                with open(instructions_path, "r", encoding="utf-8") as f:
                    self.instructions_md = f.read()
            except FileNotFoundError:
                self.instructions_md = f"# {name}\n\nInstructions not found."
    
    def retrieve(
        self,
        query: str,
        domain: str = None,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Запрос к RAG базе знаний.
        
        Использовать когда:
        - Вопрос выходит за рамки instructions.md
        - Нужен факт из авторитетного источника
        - Требуется подтверждение перед выводом
        """
        return self._rag.retrieve(
            query=query,
            domain=domain or self.domain,
            top_k=top_k,
        )
    
    def format_retrieval(self, chunks: list[dict]) -> str:
        """Форматировать результаты RAG для включения в ответ."""
        if not chunks:
            return "• RAG: нет релевантных источников"
        
        lines = ["• RAG источники:"]
        for i, chunk in enumerate(chunks, 1):
            lines.append(
                f"  [{i}] {chunk['source']} "
                f"(релевантность: {chunk['relevance_score']:.0%})"
            )
            # Add first 100 chars of content as preview
            preview = chunk['content'][:100].replace('\n', ' ')
            lines.append(f"      → {preview}...")
        
        return "\n".join(lines)
    
    @abstractmethod
    async def run(self, state: dict) -> AgentResponse:
        """
        Главный метод агента.
        
        Args:
            state: SentinelState из оркестратора
            
        Returns:
            AgentResponse с голосом агента
        """
        pass
    
    def _build_prompt(
        self,
        user_task: str,
        extra_context: str = "",
        use_rag: bool = True,
    ) -> str:
        """
        Построить системный промпт для агента.
        
        Включает:
        1. Instructions.md
        2. RAG chunks если нужно
        3. Extra context
        """
        parts = [
            f"# Instructions for {self.name}\n\n{self.instructions_md}",
        ]
        
        if extra_context:
            parts.append(f"\n# Current Context\n\n{extra_context}")
        
        if use_rag and self.domain:
            # Agent can call self.retrieve() himself, no need to pre-fetch here
            pass
        
        return "\n\n".join(parts)
