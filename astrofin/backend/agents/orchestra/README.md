# AgentOrchestra — Новая Архитектура AstroFin

## Концепция

AgentOrchestra заменяет monolithic `AstroCouncilAgent` на **систему оркестрации** где:

```
User Query → Conductor → [Planner + MCP Manager + Memory] → Sub-Agents → Final Signal
```

## Компоненты

### 1. ConductorAgent (Главный)
```python
from agents.orchestra import ConductorAgent

conductor = ConductorAgent()
result = await conductor.analyze({
    "query": "Проанализируй BTC на LONG",
    "symbol": "BTC",
    "timeframe": "1d",
    "price": 67000
})
```

**Веса (сумма = 100%):**
| Блок | Агенты | Вес |
|------|--------|-----|
| Астрология | AstroCouncil | 25% |
| Фундаментал | Fundamental, Macro, Bull/Bear | 30% |
| Quant/ML | Quant, Predictor | 20% |
| Flow/Sentiment | OptionsFlow, Sentiment | 15% |
| Technical | Technical | 5% |
| Risk | Risk | 5% |

### 2. PlanningAgent (Планировщик)
```python
from agents.orchestra import PlanningAgent

planner = PlanningAgent()
plan = await planner.create_plan(
    "Проанализируй BTC на LONG",
    {"symbol": "BTC", "timeframe": "1d"}
)
```

**Стратегии оркестрации:**
- `PARALLEL` — все задачи одновременно
- `SEQUENTIAL` — последовательно
- `CONDITIONAL` — с учётом зависимостей

### 3. MCPManager (Управление инструментами)
```python
from agents.orchestra import MCPManager

mcp = MCPManager()
tool = await mcp.get_or_create_tool("Нужны данные по опционам")

stats = mcp.get_stats()
# {
#     "total_tools": 12,
#     "dynamic_tools": 6,
#     "total_executions": 847,
#     "top_tools": [...]
# }
```

**Встроенные инструменты:**
- `swiss_ephemeris` — планетные позиции
- `polygon_client` — рыночные данные
- `binance_client` — крипто-данные
- `fred_client` — макро-данные
- `redis_cache` — кэширование
- `shared_memory` — долгосрочная память

## Архитектура vs Старая

| Компонент | Старая (AstroCouncilAgent) | Новая (AgentOrchestra) |
|-----------|---------------------------|------------------------|
| Главный | AstroCouncilAgent | ConductorAgent |
| Планирование | ❌ | ✅ PlanningAgent |
| Инструменты | Статичные | ✅ MCPManager (динамические) |
| Память | ❌ | ✅ SharedMemoryBank |
| Агенты | 9 | 18+ |
| Orchestration | Параллельный | Параллельный/Последовательный/Conditional |
| Веса | 100% | 100% |

## Запуск

```python
# Backend
cd astrofin/backend
POLYGON_API_KEY=your_key python3 main.py

# API: POST /analyze
{
    "query": "Проанализируй BTC на LONG",
    "symbol": "BTC",
    "timeframe": "1d"
}
```

## Roadmap

- [x] ConductorAgent (v1)
- [x] PlanningAgent
- [x] MCPManager
- [ ] Интеграция SharedMemoryBank
- [ ] LLM-based planner (Claude/GPT)
- [ ] Dynamic tool generation
- [ ] Agent learning from feedback
