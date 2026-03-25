"""Core decorators."""
import functools
import logging

logger = logging.getLogger(__name__)
HAS_SWISS_EPHEMERIS = True

def require_ephemeris(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        if not HAS_SWISS_EPHEMERIS:
            logger.warning("Swiss Ephemeris not available")
        return await func(*args, **kwargs)
    return wrapper
