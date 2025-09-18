from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from main import app


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
    with patch("src.agents.base_agent.Agent.run") as mock_run:
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

    with patch("src.agents.base_agent.Agent.run", new=mock_run):
        yield
