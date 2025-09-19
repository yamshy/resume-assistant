from __future__ import annotations

"""Caching utilities backed by Redis with graceful fallbacks."""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

try:
    from redis.asyncio import Redis
except Exception:  # pragma: no cover - redis is optional in tests
    Redis = None  # type: ignore

from app.config import get_settings

_cache_client: Redis | None = None
_fallback_store: dict[str, "CacheEntry"] = {}
_lock = asyncio.Lock()


@dataclass
class CacheEntry:
    key: str
    value: Any
    expires_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) > self.expires_at


async def init_cache() -> None:
    """Initialise Redis connection or fallback to in-memory cache."""

    global _cache_client

    if _cache_client is not None:
        return

    settings = get_settings()
    if settings.redis_url.startswith("memory://") or Redis is None:
        _cache_client = None
        return

    try:
        client = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
        await client.ping()
        _cache_client = client
    except Exception:
        _cache_client = None


async def close_cache() -> None:
    global _cache_client, _fallback_store
    if _cache_client is not None:
        await _cache_client.close()
    _cache_client = None
    async with _lock:
        _fallback_store = {}


async def cache_set(key: str, value: Any, ttl: int | None = None) -> None:
    if _cache_client is not None:
        data = json.dumps(value)
        await _cache_client.set(key, data, ex=ttl)
        return

    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl) if ttl else None
    async with _lock:
        _fallback_store[key] = CacheEntry(key=key, value=value, expires_at=expires_at)


async def cache_get(key: str) -> Any | None:
    if _cache_client is not None:
        data = await _cache_client.get(key)
        if data is None:
            return None
        return json.loads(data)

    async with _lock:
        entry = _fallback_store.get(key)
        if entry is None:
            return None
        if entry.is_expired():
            del _fallback_store[key]
            return None
        return entry.value


async def cache_delete(key: str) -> None:
    if _cache_client is not None:
        await _cache_client.delete(key)
        return
    async with _lock:
        _fallback_store.pop(key, None)


def get_cache_client() -> Redis | None:
    return _cache_client


__all__ = [
    "init_cache",
    "close_cache",
    "cache_get",
    "cache_set",
    "cache_delete",
    "get_cache_client",
]
