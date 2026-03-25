# Base Agent — AstroFin Sentinel
---
version: "1.0.0"
depends_on: "rag/tools.py"
---

```python
"""
AstroFin Sentinel — Base Agent
=============================
Базовый класс для всех агентов системы.

Наследование:
    MarketAnalyst, BullResearcher, BearResearcher,
    AstroSpecialist, MuhurtaSpecialist, Synthesizer

Атрибуты:
    role:          Уникальный ID роли агента
    tools:         Привязанные инструменты RAG
    memory:        ChatMessageHistory для context window
    system_prompt: Загружается из agents/<role>/SKILL.md
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Literal, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.memory import BaseMemory
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

# ─── Project Paths ────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent.parent
KB_DIR = PROJECT_ROOT / "knowledge_base"
AGENTS_DIR = PROJECT_ROOT / "agents"

# ─── Logging ─────────────────────────────────────────────────

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# ─── Agent Output Schemas ────────────────────────────────────

class AgentSignal(BaseModel):
    """Сигнал от агента — базовый формат."""
    agent_role: str = Field(description="Роль агента")
    confidence: float = Field(description="Уверенность 0.0–1.0")
    reasoning: str = Field(description="Обоснование решения")
    tags: list[str] = Field(default_factory=list, description="Теги для фильтрации")


class TradingSignal(AgentSignal):
    """Сигнал для торговой рекомендации."""
    direction: Literal["LONG", "SHORT", "NEUTRAL"] = Field(description="Направление")
    asset: str = Field(description="Тикер актива")
    entry_zones: list[str] = Field(
        default_factory=list,
        description="Зоны входа (price levels)"
    )
    risk_reward: Optional[float] = Field(
        default=None,
        description="Соотношение Risk/Reward"
    )
    urgency: Literal["HIGH", "MEDIUM", "LOW"] = Field(
        default="MEDIUM",
        description="Срочность сигнала"
    )
    astrological_notes: Optional[str] = Field(
        default=None,
        description="Астрологические обоснования (если есть)"
    )


class ResearchOutput(BaseModel):
    """Выход BullResearcher / BearResearcher."""
    thesis: str = Field(description="Основной тезис")
    supporting_factors: list[str] = Field(
        default_factory=list,
        description="Поддерживающие факторы"
    )
    counter_arguments: list[str] = Field(
        default_factory=list,
        description="Контраргументы (для честности)"
    )
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    sources: list[str] = Field(default_factory=list, description="Источники данных")


class SynthesisOutput(BaseModel):
    """Выход Synthesizer — финальная рекомендация."""
    decision: Literal["LONG", "SHORT", "NO_POSITION", "WAIT"] = Field(
        description="Итоговое решение"
    )
    confidence_weighted: float = Field(
        description="Взвешенная уверенность (с учётом весов)"
    )
    reasoning_summary: str = Field(description="Резюме логики")
    director_board_votes: dict[str, str] = Field(
        description="Голоса каждого агента: role -> vote_summary"
    )
    risk_assessment: Literal["LOW", "MEDIUM", "HIGH", "EXTREME"] = Field(
        description="Уровень риска"
    )
    action_plan: list[str] = Field(
        default_factory=list,
        description="План действий (шаги)"
    )
    astrological_alignment: str = Field(
        default="",
        description="Астрологическая синхронизация"
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Предупреждения и дисклеймеры"
    )


# ─── Prompt Loader ──────────────────────────────────────────

def load_agent_prompt(role: str) -> str:
    """Загружает system prompt из knowledge_base/agents/<role>.md"""
    prompt_path = KB_DIR / "agents" / f"{role}.md"

    if not prompt_path.exists():
        logger.warning(
            f"Prompt for '{role}' not found at {prompt_path}. "
            f"Using fallback template."
        )
        return _fallback_prompt(role)

    return prompt_path.read_text(encoding="utf-8")


def _fallback_prompt(role: str) -> str:
    """Fallback если файл инструкций не найден."""
    return f"""You are {role}, a specialized agent in the AstroFin Sentinel system.

Your role: {role}

You have access to RAG tools to retrieve:
- Agent-specific instructions
- Astrological rules (Panchanga, Muhurta, Choghadiya)
- General market analysis principles

Always:
1. Be precise and cite your sources from the knowledge base
2. Clearly distinguish between technical analysis and astrological signals
3. Provide confidence levels (0.0–1.0) for your assessments
4. Flag when astrological signals conflict with technical signals

Output format: Follow the Pydantic schema provided by the system.
"""


# ─── Base Agent ─────────────────────────────────────────────

class BaseAgent(ABC):
    """
    Базовый класс агента AstroFin Sentinel.

    Наследуйте для создания конкретного агента:
        class MarketAnalyst(BaseAgent):
            role = "MarketAnalyst"
            output_schema = TradingSignal

    Usage:
        analyst = MarketAnalyst(llm=model)
        result = analyst.run("BTC", {"price": 67000, "volume": ...})
    """

    # Override в subclass
    role: str = "BaseAgent"
    output_schema: type[BaseModel] = AgentSignal

    def __init__(
        self,
        llm: BaseChatModel,
        tools: Optional[list[BaseTool]] = None,
        memory: Optional[BaseMemory] = None,
        temperature: float = 0.3,
        system_prompt: Optional[str] = None,
    ):
        """
        Args:
            llm:          LangChain chat model (OpenAI, Anthropic, Ollama, ...)
            tools:        Список LangChain tools (из rag.tools)
            memory:       ChatMessageHistory или ConversationBufferMemory
            temperature:  Temperature для LLM (default 0.3)
            system_prompt: Кастомный system prompt (иначе загружается из KB)
        """
        self.llm = llm
        self.tools = tools or []
        self.memory = memory
        self._temperature = temperature

        # Загружаем system prompt
        self._system_prompt = (
            system_prompt
            or load_agent_prompt(self.role)
        )

        # Цепочка
        self._chain = self._build_chain()

        # Output parser
        self._parser = PydanticOutputParser(pydantic_object=self.output_schema)

        logger.info(f"Initialized {self.role} with {len(self.tools)} tools")

    # ── Chain Builder ─────────────────────────────────────────

    def _build_chain(self) -> Runnable:
        """Собирает LangChain цепочку: prompt → model → parser."""
        from langchain import hub
        from langchain.agents import AgentExecutor, create_react_agent

        # ReAct agent — стандартный для tool-augmented agents
        agent = create_react_agent(self.llm, self.tools)
        return AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
        )

    # ── Public API ───────────────────────────────────────────

    def run(self, input_text: str, **kwargs) -> BaseModel:
        """
        Основной метод запуска агента.

        Args:
            input_text:  Запрос / задача для агента
            **kwargs:     Дополнительный контекст (asset, timeframe, etc.)

        Returns:
            Pydantic объект (subclass AgentSignal / TradingSignal / etc.)
        """
        # Подмешиваем контекст в system prompt
        context = self._format_context(kwargs)

        result = self._chain.invoke({
            "input": input_text,
            "system_prompt": self._system_prompt,
            "context": context,
        })

        return self._parse_output(result.get("output", ""))

    async def run_async(self, input_text: str, **kwargs) -> BaseModel:
        """Async version."""
        import asyncio

        return await asyncio.to_thread(self.run, input_text, **kwargs)

    # ── Subclass Hooks ───────────────────────────────────────

    @abstractmethod
    def analyze(self, *args, **kwargs) -> BaseModel:
        """Основной метод анализа. Реализуется в subclass."""
        raise NotImplementedError

    # ── Helpers ─────────────────────────────────────────────

    def _format_context(self, kwargs: dict) -> str:
        """Форматирует доп. контекст в читаемый текст."""
        if not kwargs:
            return ""

        parts = [f"**{k}**: {v}" for k, v in kwargs.items()]
        return "\n".join(parts)

    def _parse_output(self, raw: str) -> BaseModel:
        """Парсит выход LLM в Pydantic schema."""
        try:
            # Пробуем извлечь JSON из ответа
            json_str = self._extract_json(raw)
            data = json.loads(json_str)
            return self.output_schema(**data)
        except Exception as e:
            logger.error(f"Parse error in {self.role}: {e}\nRaw: {raw[:500]}")
            # Fallback — возвращаем базовый AgentSignal
            return AgentSignal(
                agent_role=self.role,
                confidence=0.0,
                reasoning=f"Parse error: {e}. Raw: {raw[:200]}",
                tags=["parse_error"],
            )

    def _extract_json(self, text: str) -> str:
        """Извлекает JSON из текста (между ```json ... ``` или ``` ... ```)."""
        import re

        # Ищем ```json ... ``` или ``` ... ```
        patterns = [
            r"```json\s*({\n.*?})\s*```",
            r"```\s*({\n.*?})\s*```",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()

        # Если JSON не найден — возвращаем весь текст
        # (парсер упадёт, но это лучше чем silent fail)
        return text

    def add_memory(self, message: BaseMessage) -> None:
        """Добавляет сообщение в history (для multi-turn)."""
        if self.memory:
            self.memory.chat_memory.add_message(message)

    def clear_memory(self) -> None:
        """Очищает history."""
        if self.memory:
            self.memory.chat_memory.clear()

    def get_history(self) -> list[BaseMessage]:
        """Возвращает историю сообщений."""
        if self.memory:
            return self.memory.chat_memory.messages
        return []
```

---

## Использование

```python
# ─── Создание агента ───────────────────────────────────────

from langchain_openai import ChatOpenAI
from langchain.memory import ChatMessageHistory
from rag.tools import TOOL_BY_ROLE, retrieve_knowledge

llm = ChatOpenAI(model="gpt-4o", temperature=0.3)
memory = ChatMessageHistory()

analyst = MarketAnalyst(
    llm=llm,
    tools=TOOL_BY_ROLE["MarketAnalyst"],
    memory=memory,
)

# ─── Запуск ─────────────────────────────────────────────────

signal = analyst.run(
    "Analyze BTC/USDT for potential LONG entry",
    asset="BTC",
    timeframe="4H",
    price=67000,
    rsi=58,
    macd="bullish crossover",
)

print(signal.direction)   # "LONG"
print(signal.confidence) # 0.72
print(signal.reasoning)  # "..."

# ─── Async ──────────────────────────────────────────────────

result = await analyst.run_async(
    "Analyze ETH for SHORT",
    asset="ETH",
    timeframe="1D",
)
```

---

## Наследование для конкретных агентов

```python
# agents/market_analyst.py

class MarketAnalyst(BaseAgent):
    role = "MarketAnalyst"
    output_schema = TradingSignal

    def analyze(
        self,
        asset: str,
        price: float,
        timeframe: str = "4H",
        indicators: Optional[dict] = None,
    ) -> TradingSignal:
        """
        Технический анализ актива.

        Args:
            asset:      Тикер (BTC, ETH, ...)
            price:      Текущая цена
            timeframe:  Таймфрейм (1H, 4H, 1D, ...)
            indicators: {'rsi': 58, 'macd': '...', 'bb': '...'}
        """
        input_text = (
            f"Perform technical analysis on {asset}/USDT.\n"
            f"Price: ${price}\n"
            f"Timeframe: {timeframe}\n"
            f"Indicators: {indicators or {}}"
        )
        return self.run(input_text, asset=asset, timeframe=timeframe)
```

---

## Next Steps

| Шаг | Файл | Описание |
|-----|------|----------|
| **4** | `agents/market_analyst.py` | Технический анализ (TA-Lib/pandas) |
| **5** | `agents/astro_specialist.py` | Астрология (Swiss Ephemeris) |
| **6** | `agents/muhurta_specialist.py` | Мухурта / Чохгадия |
| **7** | `orchestration/graph.py` | LangGraph orchestration |

---
