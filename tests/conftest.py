from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app import main as app_module
from app.agents import MemoryAgent, ResumeOrchestrator
from app.storage import MemoryStorage


class FakeOpenAI:
    """Minimal stub that records calls and returns queued responses."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []
        self.responses: list[str] = []

        class _Completions:
            def __init__(self, outer: FakeOpenAI) -> None:
                self.outer = outer

            async def create(self, *args: Any, **kwargs: Any) -> SimpleNamespace:
                outer = self.outer
                outer.calls.append({"args": args, "kwargs": kwargs})
                content = outer.responses.pop(0) if outer.responses else "{}"
                if isinstance(content, dict):
                    content = json.dumps(content)
                message = SimpleNamespace(content=content)
                return SimpleNamespace(choices=[SimpleNamespace(message=message)])

        class _Chat:
            def __init__(self, outer: FakeOpenAI) -> None:
                self.completions = _Completions(outer)

        self.chat = _Chat(self)

    def queue_response(self, payload: Any) -> None:
        self.responses.append(payload)


@pytest.fixture(autouse=True)
def app_context(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    data_dir = tmp_path / "data"
    storage = MemoryStorage(data_dir)
    orchestrator_llm = FakeOpenAI()
    memory_llm = FakeOpenAI()
    orchestrator = ResumeOrchestrator(storage=storage, client=orchestrator_llm, model="test-model")
    memory_agent = MemoryAgent(storage=storage, client=memory_llm, model="test-model")

    monkeypatch.setattr(app_module, "storage", storage)
    monkeypatch.setattr(app_module, "orchestrator", orchestrator)
    monkeypatch.setattr(app_module, "memory_agent", memory_agent)

    yield {
        "storage": storage,
        "orchestrator": orchestrator,
        "memory_agent": memory_agent,
        "orchestrator_llm": orchestrator_llm,
        "memory_llm": memory_llm,
    }


@pytest.fixture
def client() -> TestClient:
    return TestClient(app_module.app)


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app_module.app), base_url="http://test"
    ) as ac:
        yield ac
