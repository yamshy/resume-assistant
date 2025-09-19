"""Common fixtures for the test suite."""

from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
os.environ.setdefault("REDIS_URL", "memory://")

from app.core import close_cache, close_db, init_cache, init_db
from app.main import app  # noqa: E402  # import after setting env vars


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient]:
    await init_db()
    await init_cache()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    await close_cache()
    await close_db()
