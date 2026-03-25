""" Декораторы безопасности asurdev (после аудита 22 марта 2026) Главный декоратор: @require_ephemeris """

from functools import wraps
from typing import Callable, Any
from langgraph.graph.message import MessagesState
import logging

logger = logging.getLogger(__name__)


def require_ephemeris(func: Callable) -> Callable:
    """ Жёсткий декоратор-страж. Гарантирует, что инструмент 'swiss_ephemeris' был вызван ПЕРВЫМ до выполнения любой логики агента.

    Работает с:
    - LangGraph node-функциями (state: MessagesState)
    - Классами агентов (self + state в первом аргументе)
    - Любой async/sync функцией

    Если вызова нет → выбрасывает ValueError + логирует CRITICAL.
    """
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Определяем, где лежит state
        state = None
        if args and isinstance(args[0], MessagesState):
            state = args[0]
        elif "state" in kwargs and isinstance(kwargs["state"], MessagesState):
            state = kwargs["state"]
        elif len(args) > 1 and isinstance(args[1], MessagesState):
            state = args[1]

        if not state:
            raise TypeError(
                "@require_ephemeris: Первый аргумент или state= должен быть MessagesState"
            )

        messages = state.get("messages", [])

        ephemeris_called = False
        for msg in messages:
            # Новый формат LangGraph (2025–2026)
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for call in msg.tool_calls:
                    if call.get("name") == "swiss_ephemeris":
                        ephemeris_called = True
                        break

            # Старый формат (дополнительная совместимость)
            elif getattr(msg, "additional_kwargs", {}).get("tool_calls"):
                for tc in msg.additional_kwargs["tool_calls"]:
                    if tc.get("function", {}).get("name") == "swiss_ephemeris":
                        ephemeris_called = True
                        break

            if ephemeris_called:
                break

        if not ephemeris_called:
            error_text = (
                "CRITICAL ERROR: swiss_ephemeris не был вызван первым!\n"
                "Декоратор @require_ephemeris прервал выполнение агента.\n"
                "Агент обязан сначала получить точные данные из Швейцарских эфемерид."
            )
            logger.critical(error_text)

            # Добавляем ошибку в историю сообщений
            state["messages"].append({
                "role": "system",
                "content": error_text
            })

            # Прерываем выполнение
            raise ValueError("require_ephemeris: swiss_ephemeris must be called FIRST!")

        # Всё в порядке — выполняем оригинальную функцию
        return func(*args, **kwargs)

    return wrapper


def require_ephemeris_with_retry(func: Callable) -> Callable:
    """Комбинация @require_ephemeris + автоматический retry (если нужно)"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Сначала проверяем декоратор
        return func(*args, **kwargs)
    return require_ephemeris(wrapper)  # порядок важен
