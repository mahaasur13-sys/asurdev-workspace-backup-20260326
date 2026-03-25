"""Redis cache decorator для asurdev (замена @lru_cache)."""

import redis
import json
import hashlib
from functools import wraps
from typing import Any, Callable

# Подключение к Redis (настраивается через env)
_redis_client = None


def get_redis_client() -> redis.Redis:
    """Lazy initialization Redis client."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=0,
            decode_responses=True,
            socket_timeout=5,
            socket_connect_timeout=5,
        )
    return _redis_client


import os


def redis_cache(ttl_seconds: int = 86400):
    """Декоратор кэширования в Redis.

    Args:
        ttl_seconds: Время жизни кэша в секундах (по умолчанию 24 часа)

    Пример использования:
        @redis_cache(ttl_seconds=3600)  # 1 час
        def calculate_panchanga(date, time, lat, lon):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Генерируем уникальный ключ
            key_parts = [
                func.__name__,
                str(args),
                str(sorted(kwargs.items())),
            ]
            key_str = ":".join(key_parts)
            cache_key = hashlib.sha256(key_str.encode()).hexdigest()

            try:
                client = get_redis_client()

                # Проверяем Redis
                cached = client.get(cache_key)
                if cached:
                    return json.loads(cached)

                # Вычисляем результат
                result = func(*args, **kwargs)

                # Сохраняем в Redis
                client.setex(cache_key, ttl_seconds, json.dumps(result))
                return result

            except redis.RedisError as e:
                # Redis недоступен — работаем без кэша
                import logging
                logging.getLogger(__name__).warning(f"Redis unavailable: {e}, computing without cache")
                return func(*args, **kwargs)

        wrapper.cache_key_prefix = f"asurdev:{func.__name__}"
        return wrapper
    return decorator


def invalidate_cache(pattern: str = "*") -> int:
    """Инвалидировать кэш по паттерну.

    Args:
        pattern: Паттерн для удаления (по умолчанию все)

    Returns:
        Количество удалённых ключей
    """
    try:
        client = get_redis_client()
        keys = client.keys(f"asurdev:{pattern}")
        if keys:
            return client.delete(*keys)
        return 0
    except redis.RedisError:
        return 0
