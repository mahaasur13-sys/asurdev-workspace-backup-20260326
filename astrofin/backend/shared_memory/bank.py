"""
SharedMemoryBank — Long-Term Memory Bank для агентских решений.

Provides:
- Namespaced storage
- TTL with automatic expiration
- Importance-weighted retention
- Graceful degradation without Redis
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class SharedMemoryBank:
    """Long-Term Memory Bank для хранения агентских решений."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        self._version = "2.0"

    async def store(
        self,
        key: str,
        value: Any,
        ttl: int = 86400,
        namespace: str = "default",
        importance: float = 0.5,
    ) -> None:
        """
        Store value with TTL and importance.

        Args:
            key: Storage key
            value: Value to store
            ttl: Time to live in seconds (default 24h)
            namespace: Logical namespace (e.g., "insights", "predictions")
            importance: 0.0-1.0, higher values live longer
        """
        async with self._lock:
            full_key = f"{namespace}:{key}"
            expires_at = datetime.now().timestamp() + (ttl * max(0.5, importance))

            self._store[full_key] = {
                "value": value,
                "expires_at": expires_at,
                "namespace": namespace,
                "importance": importance,
                "created_at": datetime.now().isoformat(),
            }
            logger.debug("Stored in %s: %s (importance=%.2f)", namespace, key, importance)

    async def get(self, key: str, namespace: str = "default") -> Any | None:
        """Get value if not expired."""
        async with self._lock:
            full_key = f"{namespace}:{key}"
            entry = self._store.get(full_key)

            if not entry:
                return None

            # Check expiration
            if entry["expires_at"] < datetime.now().timestamp():
                del self._store[full_key]
                return None

            return entry["value"]

    async def store_from_response(
        self, agent_name: str, response: Any, importance: float = 0.5
    ) -> None:
        """Store agent response in memory."""
        await self.store(
            key=f"response_{agent_name}",
            value=response.to_dict() if hasattr(response, "to_dict") else response,
            namespace="responses",
            importance=importance,
        )

    async def get_agent_votes(self, symbol: str) -> list[dict[str, Any]]:
        """Get historical agent votes for symbol."""
        async with self._lock:
            results = []
            now = datetime.now().timestamp()

            for key, entry in self._store.items():
                if entry["expires_at"] < now:
                    continue
                if entry.get("namespace") == "insights" and entry["value"].get("symbol") == symbol:
                    results.append(entry["value"])

            return results

    def get_stats(self) -> dict[str, Any]:
        """Get memory statistics."""
        now = datetime.now().timestamp()
        active = sum(1 for e in self._store.values() if e["expires_at"] >= now)
        expired = len(self._store) - active

        return {
            "total_entries": len(self._store),
            "active_entries": active,
            "expired_entries": expired,
            "version": self._version,
        }

    async def cleanup_expired(self) -> int:
        """Remove expired entries. Returns count of removed entries."""
        async with self._lock:
            now = datetime.now().timestamp()
            expired_keys = [k for k, v in self._store.items() if v["expires_at"] < now]

            for key in expired_keys:
                del self._store[key]

            if expired_keys:
                logger.info("Cleaned up %d expired entries", len(expired_keys))

            return len(expired_keys)
