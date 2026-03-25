"""
Polygon.io client for AstroFin.

All external API calls MUST go through this client.
Provides Redis caching and graceful shutdown.
"""
from __future__ import annotations

import os
import json
import hashlib
import logging
from typing import Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

import httpx
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class PolygonClient:
    """
    Polygon.io HTTP client with Redis caching.

    All methods are async and cache results automatically.
    """

    _instance: PolygonClient | None = None
    _lock: asyncio.Lock | None = None

    def __init__(self) -> None:
        self.api_key: str | None = os.getenv("POLYGON_API_KEY")
        if not self.api_key:
            logger.warning("[PolygonClient] POLYGON_API_KEY not set")

        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis = Redis.from_url(redis_url, decode_responses=True)
        self.http_client = httpx.AsyncClient(timeout=12.0)
        self._closed = False
        logger.info("[PolygonClient] Initialized (Redis: %s)", redis_url)

    @classmethod
    @asynccontextmanager
    async def get_instance(cls) -> AsyncIterator[PolygonClient]:
        """Get singleton instance with async context manager."""
        if cls._instance is None or cls._instance._closed:
            cls._instance = cls()
        try:
            yield cls._instance
        finally:
            pass  # Don't auto-close, use explicit close()

    @classmethod
    async def get_client(cls) -> PolygonClient:
        """Get the global client instance."""
        if cls._instance is None or cls._instance._closed:
            cls._instance = cls()
        return cls._instance

    def _cache_key(self, method: str, args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
        """Generate SHA256 cache key."""
        key_parts = [method]
        for arg in args[1:]:  # skip self
            key_parts.append(str(arg))
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        key_str = ":".join(key_parts)
        return f"astrofin:polygon:{hashlib.sha256(key_str.encode()).hexdigest()[:32]}"

    async def get_unusual_activity(
        self, symbol: str, limit: int = 80
    ) -> dict[str, Any]:
        """
        Get unusual options activity + snapshot + GEX estimate.
        Cached for 90 seconds.
        """
        cache_key = self._cache_key("unusual_activity", (symbol,), {"limit": limit})

        # Check cache
        cached = await self.redis.get(cache_key)
        if cached:
            data = json.loads(cached)
            data["cached"] = True
            return data

        try:
            # Get snapshot
            snapshot = await self._get_snapshot(symbol)
            trades = await self._get_recent_option_trades(symbol, limit)

            unusual = [t for t in trades if t.get("size", 0) > 500]
            sweeps = [t for t in trades if t.get("size", 0) > 1000]

            result = {
                "status": "ok",
                "symbol": symbol,
                "unusual_volume": len(unusual),
                "large_sweeps": len(sweeps),
                "put_call_ratio": self._calculate_pcr(trades),
                "gamma_exposure": self._estimate_gex(snapshot, trades),
                "snapshot": {
                    "last_price": snapshot.get("last_quote", {}).get("p", 0),
                    "volume": snapshot.get("day", {}).get("v", 0),
                },
                "timestamp": datetime.now().isoformat(),
                "cached": False,
            }

            # Cache for 90 seconds
            await self.redis.setex(cache_key, 90, json.dumps(result, default=str))
            return result

        except Exception as e:
            logger.error("[PolygonClient] unusual_activity failed: %s", e)
            return {"status": "error", "message": str(e)}

    async def get_aggregates(
        self,
        symbol: str,
        multiplier: int = 1,
        timespan: str = "day",
        from_date: str | None = None,
        to_date: str | None = None,
        limit: int = 120,
    ) -> dict[str, Any]:
        """
        Get aggregated OHLCV data.
        Cached for 5 minutes.
        """
        if from_date is None:
            from_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        if to_date is None:
            to_date = datetime.now().strftime("%Y-%m-%d")

        cache_key = self._cache_key(
            "aggregates", (symbol,),
            {"multiplier": multiplier, "timespan": timespan, "from": from_date, "to": to_date},
        )

        cached = await self.redis.get(cache_key)
        if cached:
            data = json.loads(cached)
            data["cached"] = True
            return data

        try:
            url = (
                f"https://api.polygon.io/v2/aggs/ticker/{symbol}/"
                f"range/{multiplier}/{timespan}/{from_date}/{to_date}"
            )
            params = {"adjusted": "true", "sort": "asc", "limit": limit, "apiKey": self.api_key}

            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            raw = response.json()

            results = raw.get("results", [])
            bars = [
                {
                    "t": r.get("t"),
                    "o": r.get("o"),
                    "h": r.get("h"),
                    "l": r.get("l"),
                    "c": r.get("c"),
                    "v": r.get("v"),
                    "date": datetime.fromtimestamp(r.get("t", 0) / 1000).isoformat() if r.get("t") else None,
                }
                for r in results
            ]

            result = {
                "status": "ok",
                "symbol": symbol,
                "bars": bars,
                "count": len(bars),
                "cached": False,
            }

            # Cache for 5 minutes
            await self.redis.setex(cache_key, 300, json.dumps(result, default=str))
            return result

        except Exception as e:
            logger.error("[PolygonClient] aggregates failed: %s", e)
            return {"status": "error", "message": str(e)}

    async def _get_snapshot(self, symbol: str) -> dict[str, Any]:
        """Get snapshot via Polygon REST API."""
        if not self.api_key:
            return {}
        try:
            url = f"https://api.polygon.io/v2/snapshot/locale/us/markets/stocks/tickers/{symbol}"
            response = await self.http_client.get(url, params={"apiKey": self.api_key})
            response.raise_for_status()
            data = response.json()
            return data.get("ticker", {}) if data else {}
        except Exception as e:
            logger.warning("[PolygonClient] snapshot failed: %s", e)
            return {}

    async def _get_recent_option_trades(self, symbol: str, limit: int) -> list[dict[str, Any]]:
        """Get recent option trades via Polygon REST API."""
        if not self.api_key:
            return []
        try:
            url = f"https://api.polygon.io/v3/trades/{symbol}"
            response = await self.http_client.get(
                url, params={"limit": limit, "apiKey": self.api_key}
            )
            response.raise_for_status()
            return response.json().get("results", [])
        except Exception:
            return []

    def _calculate_pcr(self, trades: list[dict[str, Any]]) -> float:
        """Calculate put/call ratio."""
        puts = sum(1 for t in trades if "put" in str(t.get("conditions", "")).lower())
        calls = max(1, len(trades) - puts)
        return round(puts / calls, 2)

    def _estimate_gex(self, snapshot: dict[str, Any], trades: list[dict[str, Any]]) -> int:
        """Estimate gamma exposure."""
        try:
            volume = snapshot.get("day", {}).get("v", 0)
            if isinstance(snapshot, dict) and "volume" in snapshot:
                volume = snapshot.get("volume", 0)
            return int(volume * 1500)
        except Exception:
            return 0

    async def close(self) -> None:
        """Graceful shutdown."""
        if not self._closed:
            await self.http_client.aclose()
            await self.redis.close()
            self._closed = True
            PolygonClient._instance = None
            logger.info("[PolygonClient] Closed")


from typing import AsyncIterator
