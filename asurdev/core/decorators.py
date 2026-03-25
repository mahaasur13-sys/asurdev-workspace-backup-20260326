"""
decorators.py — asurdev Sentinel v3.2
Декораторы для жёсткого соблюдения правил безопасности
"""
from functools import wraps
from typing import Callable, Any
from langgraph.graph.message import MessagesState
import hashlib
import logging

logger = logging.getLogger(__name__)


def require_ephemeris(func: Callable) -> Callable:
    """
    Декоратор-страж: гарантирует, что swiss_ephemeris был вызван ПЕРВЫМ.
    Работает с LangGraph MessagesState и любым агентом.
    
    Пример использования:
        @require_ephemeris
        def muhurta_node(state: MessagesState):
            ...
    """
    @wraps(func)
    def wrapper(agent_instance, state: MessagesState, *args, **kwargs):
        messages = state.get("messages", [])
        
        # Проверяем историю на наличие вызова swiss_ephemeris
        ephemeris_called = False
        ephemeris_call_count = 0
        
        for msg in reversed(messages):  # Проверяем с конца (новые первыми)
            # LangGraph хранит tool calls в AIMessage.tool_calls
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    name = tool_call.get("name", "")
                    if name == "swiss_ephemeris":
                        ephemeris_call_count += 1
                        # Проверяем, что это был ПЕРВЫЙ tool call
                        if messages.index(msg) == 0 or all(
                            messages[i].get("role") != "assistant" 
                            for i in range(messages.index(msg))
                        ):
                            ephemeris_called = True
                        break
            # Старый формат (additional_kwargs)
            elif getattr(msg, "additional_kwargs", {}).get("tool_calls"):
                for tc in msg.additional_kwargs["tool_calls"]:
                    if tc.get("function", {}).get("name") == "swiss_ephemeris":
                        ephemeris_call_count += 1
                        ephemeris_called = True
                        break
        
        if not ephemeris_called:
            error_msg = {
                "role": "system",
                "content": (
                    "CRITICAL ERROR: swiss_ephemeris не был вызван первым! "
                    "Агент прерван согласно правилу аудита от 22 марта 2026."
                )
            }
            state["messages"].append(error_msg)
            logger.error("require_ephemeris: swiss_ephemeris must be called first!")
            raise ValueError("require_ephemeris: swiss_ephemeris must be called first!")
        
        # Логируем успешную проверку (без PII!)
        logger.info(f"asurdev → swiss_ephemeris verified (call #{ephemeris_call_count})")
        
        # Всё хорошо — выполняем оригинальную функцию агента
        return func(agent_instance, state, *args, **kwargs)
    
    return wrapper


def log_without_pii(func: Callable) -> Callable:
    """
    Декоратор для логирования БЕЗ PII.
    Удаляет даты рождения, точные координаты, имена пользователей.
    
    Разрешено логировать:
        - hash запроса (request_key)
        - JD_UT
        - ayanamsa
        - compute_флаги
        - роли агентов
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Анонимизируем аргументы
        clean_args = _anonymize_args(args)
        clean_kwargs = _anonymize_kwargs(kwargs)
        
        logger.debug(f"[ANONYMIZED] {func.__name__}", extra={
            "clean_args": clean_args,
            "clean_kwargs": clean_kwargs
        })
        
        return func(*args, **kwargs)
    
    return wrapper


def _anonymize_args(args: tuple) -> list:
    """Анонимизирует позиционные аргументы"""
    cleaned = []
    for arg in args:
        if isinstance(arg, dict):
            cleaned.append(_anonymize_dict(arg))
        elif isinstance(arg, str) and _looks_like_pii(arg):
            cleaned.append(_hash_string(arg))
        else:
            cleaned.append(arg)
    return cleaned


def _anonymize_kwargs(kwargs: dict) -> dict:
    """Анонимизирует именованные аргументы"""
    cleaned = {}
    for key, value in kwargs.items():
        if key in ("date", "birth_date", "dob", "time", "birth_time", "lat", "lon", 
                   "latitude", "longitude", "name", "user_name", "username", "full_name"):
            cleaned[key] = _hash_string(str(value))
        elif isinstance(value, dict):
            cleaned[key] = _anonymize_dict(value)
        else:
            cleaned[key] = value
    return cleaned


def _anonymize_dict(d: dict) -> dict:
    """Рекурсивно анонимизирует словарь"""
    cleaned = {}
    for key, value in d.items():
        if key in ("date", "birth_date", "dob", "time", "birth_time", "lat", "lon",
                   "latitude", "longitude", "name", "user_name", "username", 
                   "full_name", "location", "address"):
            cleaned[key] = _hash_string(str(value))
        elif isinstance(value, dict):
            cleaned[key] = _anonymize_dict(value)
        elif isinstance(value, list):
            cleaned[key] = [_hash_string(str(v)) if _looks_like_pii(str(v)) else v 
                          for v in value]
        else:
            cleaned[key] = value
    return cleaned


def _looks_like_pii(s: str) -> bool:
    """Определяет, содержит ли строка PII"""
    import re
    # Дата в формате YYYY-MM-DD или DD/MM/YYYY
    if re.match(r'\d{4}-\d{2}-\d{2}', s) or re.match(r'\d{2}/\d{2}/\d{4}', s):
        return True
    # Координаты (примерно -90 to 90, -180 to 180)
    coord_pattern = r'[-+]?\d{1,3}\.\d{4,}'
    if re.findall(coord_pattern, s) and abs(float(re.findall(coord_pattern, s)[0])) <= 180:
        return True
    # Имя (заглавная буква + строчные, минимум 2 символа)
    if re.match(r'^[A-Z][a-z]+$', s) and len(s) > 2:
        return True
    return False


def _hash_string(s: str) -> str:
    """Хэширует строку для безопасного логирования"""
    return f"HASH:{hashlib.sha256(s.encode()).hexdigest()[:16]}"


# ============================================================
# Retry с tenacity (для swiss_ephemeris)
# ============================================================
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)


def swiss_ephemeris_retry():
    """
    Retry decorator для вызовов swiss_ephemeris.
    
    Поведение:
        - До 3 попыток
        - Экспоненциальный backoff (1с, 2с, 4с)
        - Логирует каждую попытку
        - После 3 неудач — исключение
    """
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((ConnectionError, TimeoutError, IOError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


class EphemerisRetryHandler:
    """
    Обработчик retry для swiss_ephemeris с fallback.
    
    Использование:
        handler = EphemerisRetryHandler()
        result = handler.call(user_date="2026-03-22", user_time="10:00:00", 
                             lat=55.7558, lon=37.6173)
    """
    
    FALLBACK_LAT = 28.6139  # Delhi (ближайший крупный город)
    FALLBACK_LON = 77.2090
    FALLBACK_TZ = "Asia/Kolkata"
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self._cache = {}  # Простой in-memory cache
    
    def call(self, date: str, time: str, lat: float, lon: float, 
             ayanamsa: str = "lahiri", **kwargs) -> dict:
        """
        Вызывает swiss_ephemeris с retry и fallback.
        
        Returns:
            dict с результатом или {"error": "...", "fallback_used": True}
        """
        from swiss_ephemeris import swiss_ephemeris
        
        cache_key = (date, time, lat, lon, ayanamsa)
        
        # Проверяем кэш
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Пробуем с retry
        for attempt in range(1, self.max_retries + 1):
            try:
                result = swiss_ephemeris(
                    date=date,
                    time=time,
                    lat=lat,
                    lon=lon,
                    ayanamsa=ayanamsa,
                    **kwargs
                )
                self._cache[cache_key] = result
                return result
                
            except (ConnectionError, TimeoutError, IOError) as e:
                logger.warning(f"swiss_ephemeris attempt {attempt}/{self.max_retries} failed: {e}")
                if attempt == self.max_retries:
                    # Fallback: используем Delhi coordinates
                    logger.warning("Using fallback coordinates (Delhi)")
                    try:
                        result = swiss_ephemeris(
                            date=date,
                            time=time,
                            lat=self.FALLBACK_LAT,
                            lon=self.FALLBACK_LON,
                            ayanamsa=ayanamsa,
                            **kwargs
                        )
                        result["_fallback"] = True
                        result["_original_coords"] = {"lat": lat, "lon": lon}
                        self._cache[cache_key] = result
                        return result
                    except Exception as fallback_error:
                        return {
                            "error": f"Не удалось получить эфемериды после {self.max_retries} попыток. "
                                    f"Пожалуйста, попробуйте позже.",
                            "details": str(fallback_error),
                            "retry_count": self.max_retries
                        }
        
        # Технически не должно достичь, но на всякий случай
        return {"error": "Неизвестная ошибка при получении эфемерид"}
