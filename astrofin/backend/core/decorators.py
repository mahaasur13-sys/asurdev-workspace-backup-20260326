"""Core decorators for agents."""
from __future__ import annotations

import functools
import logging
from datetime import datetime
from typing import Any, Callable

logger = logging.getLogger(__name__)

HAS_SWISS_EPHEMERIS = True


def require_ephemeris(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that ensures Swiss Ephemeris is available before execution."""

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not HAS_SWISS_EPHEMERIS:
            logger.warning(
                "Swiss Ephemeris not available, %s may return degraded results",
                func.__name__,
            )
        return await func(*args, **kwargs)

    return wrapper


def timing(metric_name: str | None = None) -> Callable[..., Any]:
    """Decorator that logs execution time."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            name = metric_name or func.__name__
            start = datetime.now()
            try:
                result = await func(*args, **kwargs)
                elapsed_ms = (datetime.now() - start).total_seconds() * 1000
                logger.debug("%s completed in %.1fms", name, elapsed_ms)
                return result
            except Exception as e:
                elapsed_ms = (datetime.now() - start).total_seconds() * 1000
                logger.error("%s failed after %.1fms: %s", name, elapsed_ms, e)
                raise

        return wrapper

    return decorator


def cache_ephemeris(ttl_seconds: int = 300) -> Callable[..., Any]:
    """Decorator that caches ephemeris calculations in Redis."""
    _cache: dict[str, tuple[float, Any]] = {}

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            key_parts = [func.__name__]
            for arg in args:
                if isinstance(arg, (str, int, float)):
                    key_parts.append(str(arg))
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")
            cache_key = "|".join(key_parts)

            if cache_key in _cache:
                cached_time, cached_result = _cache[cache_key]
                if (datetime.now() - cached_time).total_seconds() < ttl_seconds:
                    return cached_result

            result = func(*args, **kwargs)
            _cache[cache_key] = (datetime.now(), result)
            return result

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            key_parts = [func.__name__]
            for arg in args:
                if isinstance(arg, (str, int, float)):
                    key_parts.append(str(arg))
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")
            cache_key = "|".join(key_parts)

            if cache_key in _cache:
                cached_time, cached_result = _cache[cache_key]
                if (datetime.now() - cached_time).total_seconds() < ttl_seconds:
                    return cached_result

            result = await func(*args, **kwargs)
            _cache[cache_key] = (datetime.now(), result)
            return result

        if functools.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
