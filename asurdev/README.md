# asurdev Sentinel v3.2

**asurdev Sentinel** — мультиагентная система для принятия финансовых решений, объединяющая технический анализ, астрологические методы и AI-синтез.

## Два способа использования

### 1. LangGraph Orchestrator (основной)

Полный анализ через LangGraph state machine с параллельными агентами:

```python
from agents import MemoryEnabledOrchestrator
import asyncio

orchestrator = MemoryEnabledOrchestrator()
result = await orchestrator.analyze("BTC", action="hold")

print(f"Вердикт: {result['final_verdict'].value}")
print(f"Уверенность: {result['confidence_avg']:.1f}%")
```

### 2. Board of Directors API (альтернативный)

Быстрый анализ через "Совет Директоров" с голосованием:

```python
from agents._impl.board import BoardOfDirectors
import asyncio

async def main():
    board = BoardOfDirectors(provider="auto", mode="debate")
    await board.initialize()
    verdict = await board.conduct_vote("Should I buy BTC at current levels?")
    print(f"Вердикт: {verdict.recommendation.value}")
    print(f"Уверенность: {verdict.confidence:.0%}")

asyncio.run(main())
```

## Установка

```bash
# Клонирование
cd /home/workspace/asurdevSentinel

# Установка как пакета
pip install -e .

# Или через pyproject.toml
pip install -e ".[dev]"
```

## CLI

```bash
# Анализ через LangGraph
asurdev analyze BTC --action hold

# Быстрый астрологический расчёт
asurdev chart 2026-03-22 12:00:00 --lat 55.75 --lon 37.62

# Текущее состояние
asurdev astro now

# Board of Directors
asurdev board "Should I buy BTC?" --json
```

## API

```bash
# Запуск сервера
cd /home/workspace/asurdevSentinel
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Эндпоинты:
# POST /api/analyze     — LangGraph анализ (sync)
# POST /api/board       — Board API (sync)
# POST /api/board/stream — Board API (SSE streaming)
# GET  /api/chart        — Астрологический расчёт
```

## Архитектура

```
┌─────────────────────────────────────────────────────────────────┐
│                     LangGraph State Machine                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐ │
│  │  Market  │───▶│   Bull   │    │   Bear   │    │   Astro  │ │
│  │ Analyst  │    │Researcher│    │Researcher│    │  Council │ │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘ │
│       └───────────────┴───────────────┴───────────────┘       │
│                               │                                │
│                               ▼                                │
│                    ┌──────────────────┐                       │
│                    │  Cycle + Merriman │ (always run)          │
│                    └────────┬─────────┘                       │
│                             │                                  │
│              ┌──────────────┼──────────────┐                   │
│              │              │              │                   │
│              ▼              ▼              ▼                   │
│        ┌──────────┐   ┌──────────┐   ┌──────────┐             │
│        │   Gann   │   │ Andrews  │   │ Synthesize│ ◄── interrupt│
│        └────┬─────┘   └────┬─────┘   └────┬─────┘             │
│             └──────────────┼──────────────┘                   │
│                            ▼                                  │
│                    ┌──────────────────┐                       │
│                    │  Dow + Meridian  │                       │
│                    └────────┬─────────┘                       │
│                             ▼                                  │
│                    ┌──────────────────┐                       │
│                    │    Synthesis     │                       │
│                    │  C.L.E.A.R. ✨  │                       │
│                    └─────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

## Board of Directors

```
┌─────────────────────────────────────────────────────────────┐
│                    BOARD OF DIRECTORS                         │
├───────────────┬───────────────┬───────────────┬──────────────┤
│    MARKET     │    BULL      │    BEAR      │    ASTRO     │
│   ANALYST     │  RESEARCHER  │  RESEARCHER  │   COUNCIL   │
│    (25%)      │   (15%)      │   (15%)      │    (20%)     │
├───────────────┴───────────────┴───────────────┴──────────────┤
│                      SYNTHESIZER                              │
│              "Что решил совет директоров?"                   │
└─────────────────────────────────────────────────────────────┘
```

## Агенты

### Фундаментальные
| Агент | Описание | Методы |
|-------|----------|--------|
| **MarketAnalyst** | Текущее состояние рынка | Цена, объём, тренд |
| **BullResearcher** | Бычий сценарий | Аргументы за покупку |
| **BearResearcher** | Медвежий сценарий | Аргументы за продажу |

### Астрологические
| Агент | Описание | Методы |
|-------|----------|--------|
| **AstrologerAgent** | Классическая астрология | planetary positions, aspects, lunar cycles |
| **CycleAgent** | Циклы планет | 7-планетные циклы, corned moon |
| **MerrimanAgent** | Методы Р. Мерримана | 7-планетный цикл, Corned Moon, аспекты |
| **MeridianAgent** | Методы Б. Меридиана | Planetary Lines, Elongation, Lunar Nodes |

### Технические
| Агент | Описание | Методы |
|-------|----------|--------|
| **AndrewsAgent** | Метод Э. Эндрюса | Median Line, Pitchfork, Slack Lines |
| **DowTheoryAgent** | Теория Доу | Тренды, подтверждение, дивергенции |
| **GannAgent** | Методы У. Ганна | Gann angles, Square of 9, Time cycles |

## LLM Providers

Система автоматически выбирает провайдера:

1. **Ollama** (локальный) — если запущен
2. **OpenAI GPT-4o** — если `OPENAI_API_KEY` установлен
3. **Anthropic Claude** — если `ANTHROPIC_API_KEY` установлен

```bash
# Установка Ollama
ollama serve  #默认 http://localhost:11434

# Загрузка модели
ollama pull qwen3-coder:32b
```

## Тесты

```bash
# Запуск всех тестов
pytest tests/ -v

# Конкретный тест
pytest tests/test_types.py -v
```

## Структура проекта

```
asurdevSentinel/
├── agents/
│   ├── __init__.py           # Unified exports
│   ├── types.py              # Signal, AgentResponse, TradingSignal
│   ├── llm_factory.py        # LLM provider factory
│   ├── langgraph_orchestrator.py  # Main orchestrator
│   ├── memory/               # RAG + ChromaDB memory
│   ├── graph/                # LangGraph nodes & routing
│   └── _impl/                # Agent implementations
│       ├── board.py          # Board of Directors
│       └── astro_council/    # Astro agents
├── api/
│   └── main.py               # FastAPI + SSE endpoints
├── cli.py                    # Typer CLI
├── swiss_ephemeris/          # Deterministic astrology
├── config/
│   └── settings.py           # pydantic-settings v2
├── pyproject.toml             # Build configuration
└── tests/                    # pytest tests
```

## Версии

| Версия | Дата | Изменения |
|--------|------|-----------|
| v3.0 | 2025 | LangGraph orchestrator, RAG, Astro Council |
| v3.1 | 2026-03 | Unified types, clean architecture |
| **v3.2** | 2026-03-22 | **Board API, SSE streaming, pydantic-settings** |
