"""In-memory async Redis replacement for tests."""

from __future__ import annotations

import fnmatch
from datetime import datetime, timedelta
from typing import Dict, Tuple


class InMemoryRedis:
    def __init__(self) -> None:
        self._store: Dict[str, str] = {}
        self._expiry: Dict[str, datetime] = {}

    async def get(self, key: str) -> str | None:
        self._evict_expired()
        return self._store.get(key)

    async def setex(self, key: str, ttl: int, value: str) -> None:
        self._store[key] = value
        self._expiry[key] = datetime.utcnow() + timedelta(seconds=ttl)

    async def scan(self, cursor: int, match: str = "*", count: int = 10) -> Tuple[int, list[str]]:
        self._evict_expired()
        keys = [key for key in self._store if fnmatch.fnmatch(key, match)]
        keys.sort()
        start = cursor
        end = min(start + count, len(keys))
        next_cursor = 0 if end >= len(keys) else end
        return next_cursor, keys[start:end]

    def _evict_expired(self) -> None:
        now = datetime.utcnow()
        expired = [key for key, expiry in self._expiry.items() if expiry <= now]
        for key in expired:
            self._store.pop(key, None)
            self._expiry.pop(key, None)
