# AstroFin Sentinel — Спецификация (v2.0 LangGraph)

## Концепция и Видение

**AstroFin Sentinel** — это персональный мультиагентный советник для принятия финансовых решений, объединяющий:
- **Technical Analyst** — количественный анализ рыночных паттернов
- **Fundamental Analyst** — оценка фундаментальных факторов
- **Vedic Astrologer** — ведический астрологический анализ (Манкаси/Джйотиш)
- **Synthesizer** — объединение сигналов в финальную рекомендацию через механизм "Совета Директоров"

Система не даёт готовых ответов — она разыгрывает внутренний совет директоров, где каждая "персона" высказывает своё мнение, а синтезатор формирует объёмную картину для принятия решений пользователем.

---

## Архитектура (LangGraph)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER QUERY                                      │
│              "Что делать с ETH/USDT сегодня?"                           │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         SUPERVISOR (Router)                             │
│  • Parses intent                                                         │
│  • Determines required agents based on query_type                       │
│  • Initializes metadata for each agent                                   │
│  • Sets weights based on query type or user preferences                │
└────────────────────────────┬────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    PARALLEL AGENTS (async)                               │
│                                                                         │
│   ┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│   │  TECHNICAL   │    │   FUNDAMENTAL   │    │   ASTROLOGER    │         │
│   │   ANALYST   │    │    ANALYST      │    │   (MANKASHI)    │         │
│   │             │    │                 │    │                 │         │
│   │  • OHLCV    │    │  • News         │    │  • Birth chart  │         │
│   │  • RSI/MACD │    │  • On-chain     │    │  • Transits     │         │
│   │  • Patterns │    │  • Macro        │    │  • Muhurta      │         │
│   │  • Levels   │    │                 │    │  • Nakshatra    │         │
│   └──────┬──────┘    └────────┬────────┘    └────────┬────────┘         │
│          │                   │                       │                   │
│          └───────────────────┼───────────────────────┘                   │
│                              │ (All run concurrently via asyncio.gather) │
└──────────────────────────────┼───────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         QUALITY GATE                                    │
│  • Validates report completeness                                        │
│  • Checks minimum confidence thresholds                                  │
│  • Handles missing/incomplete data                                      │
│  • Routes to synthesizer or end on failure                             │
└──────────────────────────────┬───────────────────────────────────────────┘
                               │
              ┌────────────────┴────────────────┐
              ▼                                 ▼
          [PASS]                            [FAIL]
              │                                 │
              ▼                                 ▼
┌──────────────────────────────┐    ┌─────────────────────┐
│        SYNTHESIZER          │    │        END          │
│    "Board of Directors"      │    │   (Error/Partial)  │
│                              │    └─────────────────────┘
│  • Weighted scoring          │
│  • Bull/Base/Bear scenarios  │
│  • Final recommendation     │
│  • Risk warnings             │
└──────────────┬───────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    MEMORY (RAG)                                         │
│  • Stores completed analysis                                            │
│  • Retrieves relevant history for context                               │
│  • Session-based memory via LangGraph checkpointer                      │
└──────────────────────────────┬───────────────────────────────────────────┘
                               │
                               ▼
                         [COMPLETE]
```

---

## Query Types

| Type | Agents Used | Description |
|------|-------------|-------------|
| `FULL_ANALYSIS` | Technical + Fundamental + Astrologer | Complete analysis with all agents |
| `TECHNICAL_FUNDAMENTAL` | Technical + Fundamental | Skip astrology for speed |
| `TECHNICAL_ONLY` | Technical | Quick technical scan |
| `QUICK_SCAN` | Technical | Alias for technical only |

---

## Агенты и их роли

### 1. Technical Analyst Agent

**Цель**: Оценка рыночной ситуации через технические индикаторы и паттерны.

**Инструменты**:
- `get_market_data()` — получение OHLCV с Binance/Bybit
- `calculate_indicators()` — RSI, MACD, Bollinger Bands, EMAs
- `detect_patterns()` — голова-плечи, двойное дно, клинья
- `get_support_resistance()` — уровни поддержки/сопротивления

**Промпт-роль**:
```
Ты — опытный технический аналитик с 20-летним стажем.
Ты торгуешь только по системе, без эмоций.
Твои сильные стороны: распознавание паттернов price action,
работа с объёмами, определение ключевых уровней.
Ты всегда даёшь probabilistic оценки (вероятность успеха).
```

**Выход**: `TechnicalReport { signal: str, confidence: float, levels: dict, pattern: str }`

---

### 2. Fundamental Analyst Agent

**Цель**: Оценка фундаментальных факторов, влияющих на актив.

**Инструменты**:
- `get_news_sentiment()` — анализ новостного фона
- `get_onchain_metrics()` — TVL, active addresses, exchange flows
- `get_macro_data()` — ставки, инфляция, DPI

**Промпт-роль**:
```
Ты — фундаментальный аналитик, специализирующийся на криптоактивах.
Ты понимаешь технологию, команду, токеномику и макрофакторы.
Ты не даёшь price targets, но оцениваешь "качество" актива.
Твой девиз: "Цена может быть неправильной годами, но фундаментал eventually winning".
```

**Выход**: `FundamentalReport { verdict: str, strength: float, factors: list, risk_factors: list }`

---

### 3. Vedic Astrologer Agent (Манкаси)

**Цель**: Оценка астрологических факторов для торговли (мухурта, планетарные влияния).

**Инструменты**:
- `mankashi_forecast()` — дневной прогноз Манкаси
- `birth_chart()` — построение натальной карты
- `get_transits()` — текущие транзиты
- `get_dasha()` — текущие периоды планет (даши)

**Промпт-роль**:
```
Ты — ведический астролог, практик Джйотиш с глубоким пониманием
Манкаси системы. Ты анализируешь:
- Накшатры (лунные созвездия)
- Планетарные йоги (особенно для финансов)
- Даши (периоды планет)
- Мухурту (благоприятное время для действий)

Ты НЕ гадаешь — ты работаешь с астрономическими данными.
Твои рекомендации всегда содержат астрологическое обоснование.
```

**Выход**: `AstroReport { muhurta: str, favorable: list, unfavorable: list, planetary_yoga: str }`

---

### 4. Synthesizer Agent ("Совет Директоров")

**Цель**: Объединение сигналов от всех аналитиков в финальную рекомендацию.

**Механизм**:
1. Получает отчёты от всех трёх аналитиков
2. Присваивает веса каждому сигналу (можно настраивать)
3. Генерирует 3 перспективы: оптимистичную, нейтральную, пессимистичную
4. Формулирует финальное advice с уровнями входа/выхода

**Веса по умолчанию**:
- Technical: 0.30
- Fundamental: 0.30
- Astrological: 0.40 (влияние на решения в системе Манкаси)

---

## RAG Memory

### Структура данных

```python
@dataclass
class MemoryEntry:
    id: str
    symbol: str
    side: str
    composite_score: float
    recommendation: dict
    timestamp: datetime
    technical_signal: str
    fundamental_signal: str
    astrologer_signal: str
    markdown: str  # Full report for reference
    search_text: str  # For keyword matching
```

### Retrieval

- Semantic search by query string
- Filter by symbol
- Recency boost for recent entries
- Returns top-K relevant entries

### Storage

- JSON-based file storage in `.memory/` directory
- Index for fast lookup
- TTL-based cleanup (default 30 days)

---

## CLI Usage

```bash
# Full analysis
python cli.py --symbol BTC/USDT --side buy

# With astrology
python cli.py --symbol ETH/USDT --side sell \
  --birth-date 03.05.1967 --birth-time 07:15

# Quick technical-only
python cli.py --symbol SOL/USDT --quick

# Custom weights
python cli.py --symbol BTC/USDT --weights 0.4 0.4 0.2

# Session-based context
python cli.py --symbol BTC/USDT --session my-session-1

# Different outputs
python cli.py --symbol BTC/USDT --output json
python cli.py --symbol BTC/USDT --output simple
```

---

## Ограничения и предупреждения

1. **⚠️ Не является финансовой рекомендацией** — система для образовательных целей
2. **⚠️ Астрология — вспомогательный инструмент**, не заменяющий финансовый анализ
3. **⚠️ Всегда требуется человеческий контроль** перед принятием решений
4. **⚠️ Прошлые результаты не гарантируют будущих**

---

## Stack

- **Orchestration**: LangChain + **LangGraph**
- **Agents**: LangChain Agents / Custom Actor model
- **Async**: `asyncio` for parallel execution
- **Memory**: RAG with JSON storage (upgradeable to ChromaDB)
- **Checkpoints**: LangGraph MemorySaver for session state
- **Astrology**: Интеграция с `mankashi_forecast_2026_03_23.py`
- **Market Data**: Binance API / YFinance
- **UI**: Telegram Bot / Discord Bot / CLI

---

## Файловая структура

```
astrofin-sentinel/
├── agents/
│   ├── __init__.py
│   ├── technical_analyst.py
│   ├── fundamental_analyst.py
│   ├── astrologer.py
│   ├── synthesizer.py
│   └── orchestrator.py          # Legacy (v1)
├── graph/                       # NEW: LangGraph architecture
│   ├── __init__.py
│   ├── state.py                 # AnalysisState, AgentReport
│   ├── nodes.py                 # All graph nodes
│   ├── graph.py                 # Graph definition
│   └── memory.py                # RAG memory
├── tools/
│   ├── __init__.py
│   ├── market_data.py
│   ├── astrology.py
│   └── news.py
├── prompts/
│   ├── technical_analyst.txt
│   ├── fundamental_analyst.txt
│   ├── astrologer.txt
│   └── synthesizer.txt
├── config/
│   └── settings.yaml
├── main.py                      # Legacy CLI (v1)
├── cli.py                       # NEW: LangGraph CLI
├── SPEC.md
└── reports/
    └── *.md
```
