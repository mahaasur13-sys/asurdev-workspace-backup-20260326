# Интеграция @require_ephemeris в LangGraph

## Вариант 1: Простые node-функции (рекомендуется)

```python
# nodes/muhurta_node.py
from langgraph.graph.message import MessagesState
from src.decorators import require_ephemeris
from swiss_ephemeris.swiss_ephemeris_tool import swiss_ephemeris


@require_ephemeris
def muhurta_node(state: MessagesState):
    """Пример node с декоратором.

    Декоратор гарантирует, что swiss_ephemeris был вызван ПЕРВЫМ.
    """
    # Здесь уже гарантировано, что swiss_ephemeris был вызван
    last_result = state["messages"][-1]  # результат последнего tool call

    # ... логика поиска мухурты ...
    return {"messages": [{"role": "assistant", "content": "Мухурта найдена..."}]}
```

## Вариант 2: Классы агентов

```python
# agents/muhurta_agent.py
from langgraph.graph.message import MessagesState
from src.decorators import require_ephemeris


class MuhurtaSpecialist:
    """Специалист по мухуртам."""

    @require_ephemeris
    def invoke(self, state: MessagesState):
        # Здесь безопасно работать с данными
        return self._process_muhurta(state)

    def _process_muhurta(self, state):
        # ... внутренняя логика ...
        return {"messages": [{"role": "assistant", "content": "analysis"}]}
```

## Вариант 3: Полный граф

```python
# graph.py
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from nodes.muhurta_node import muhurta_node
from nodes.panchanga_node import panchanga_node
from nodes.astro_node import astro_node
from swiss_ephemeris.swiss_ephemeris_tool import swiss_ephemeris


workflow = StateGraph(MessagesState)

# Добавляем ноды с декоратором — всё работает автоматически
workflow.add_node("muhurta", muhurta_node)
workflow.add_node("panchanga", panchanga_node)
workflow.add_node("astro", astro_node)

# Tool node для Swiss Ephemeris
tools_node = ToolNode([swiss_ephemeris])
workflow.add_node("tools", tools_node)

workflow.add_edge(START, "tools")  # сначала всегда tools (swiss_ephemeris)
workflow.add_conditional_edges("tools", route_after_ephemeris)

graph = workflow.compile()
```

## Обработка ошибки декоратора в графе

```python
def route_after_ephemeris(state: MessagesState):
    """Маршрутизация после вызова ephemeris."""
    last_msg = state["messages"][-1]

    if "CRITICAL ERROR" in str(last_msg.content):
        return "error_handler_node"  # отдельная нода для красивого сообщения

    return "muhurta"  # или следующий агент


def error_handler_node(state: MessagesState):
    """Нода обработки ошибок."""
    return {
        "messages": [{
            "role": "assistant",
            "content": (
                "⚠️ Ошибка: не удалось получить астрономические данные. "
                "Попробуйте изменить дату/координаты."
            )
        }]
    }
```

## Retry с tenacity

```python
# swiss_ephemeris/swiss_ephemeris_tool.py
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import swisseph as swe


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((OSError, RuntimeError, ValueError)),
    reraise=True,
    before_sleep=lambda retry_state: print(f"[RETRY] attempt {retry_state.attempt_number}/3")
)
def safe_swiss_ephemeris_call(input_data: dict) -> dict:
    """Обёртка с автоматическим повтором."""
    swe.set_ephe_path("./ephe")
    # ... вся логика расчёта ...
    return result_dict


def swiss_ephemeris_tool(input_data: dict) -> dict:
    try:
        return safe_swiss_ephemeris_call(input_data)
    except Exception as e:
        return {
            "errors": [str(e)],
            "user_message": "Не удалось получить данные Swiss Ephemeris после 3 попыток."
        }
```

## Запуск тестов

```bash
# Unit тесты
pytest tests/test_audit_compliance.py -v

# E2E тесты
pytest tests/test_swiss_ephemeris.py -v

# Все тесты
pytest tests/ -v --tb=short
```
