from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import AsyncGenerator, Iterator
from pathlib import Path
from unittest.mock import patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

DATA_DIR = Path(tempfile.mkdtemp(prefix="resume_assistant_tests_"))
os.environ.setdefault("RESUME_ASSISTANT_DATA_DIR", str(DATA_DIR))


def _purge_data_dir() -> None:
    if not DATA_DIR.exists():
        return
    for path in DATA_DIR.iterdir():
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


@pytest.fixture(autouse=True)
def clean_storage() -> Iterator[None]:
    _purge_data_dir()
    yield
    _purge_data_dir()


from app.main import app  # noqa: E402  (import after setting environment)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture
def mock_agent():
    with patch("resume_core.agents.base_agent.Agent.run") as mock_run:
        mock_run.return_value = {
            "analysis": "Mocked analysis result",
            "confidence": 0.95,
        }
        yield mock_run


@pytest.fixture
def mock_agent_async():
    async def mock_run(self, text: str):
        return {
            "analysis": f"Analyzed: {text}",
            "confidence": 0.90,
        }

    with patch("resume_core.agents.base_agent.Agent.run", new=mock_run):
        yield
