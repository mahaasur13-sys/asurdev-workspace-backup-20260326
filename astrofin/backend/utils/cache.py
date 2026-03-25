"""Cache utilities."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class CacheManager:
    """Simple Redis cache manager with TTL support."""

    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        val = await self.redis.get(key)
        if val:
            return json.loads(val)
        return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set value with TTL (default 5 minutes)."""
        await self.redis.setex(key, ttl, json.dumps(value, default=str))

    async def delete(self, key: str) -> None:
        """Delete key from cache."""
        await self.redis.delete(key)

    async def clear_prefix(self, prefix: str) -> int:
        """Clear all keys with prefix."""
        keys = []
        async for key in self.redis.scan_iter(match=f"astrofin:{prefix}:*"):
            keys.append(key)
        if keys:
            return await self.redis.delete(*keys)
        return 0
