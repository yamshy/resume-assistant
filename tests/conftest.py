import os
import sys
from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from pydantic_ai.models.test import TestModel

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
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
    with patch("agents.base_agent.Agent.run") as mock_run:
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

    with patch("agents.base_agent.Agent.run", new=mock_run):
        yield


@pytest.fixture(autouse=True, scope="session")
def mock_agents_for_contract_tests():
    """Mock all agents with TestModel for contract tests."""
    import os

    # Set a dummy API key for all test execution
    original_api_key = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "test-key-for-mocking"

    try:
        # Import agents and create mocked versions
        from agents.job_analysis_agent import create_job_analysis_agent
        from agents.profile_matching import create_profile_matching_agent
        from agents.resume_generation_agent import create_resume_generation_agent
        from agents.validation_agent import create_validation_agent

        mock_job_agent = create_job_analysis_agent().override(model=TestModel())
        mock_profile_agent = create_profile_matching_agent().override(model=TestModel())
        mock_resume_agent = create_resume_generation_agent().override(model=TestModel())
        mock_validation_agent = create_validation_agent().override(model=TestModel())

        # Patch both module-level instances and creation functions
        with (
            patch("api.jobs.job_analysis_agent", mock_job_agent),
            patch("agents.job_analysis_agent.create_job_analysis_agent", lambda: mock_job_agent),
            patch(
                "agents.profile_matching.create_profile_matching_agent", lambda: mock_profile_agent
            ),
            patch(
                "agents.resume_generation_agent.create_resume_generation_agent",
                lambda: mock_resume_agent,
            ),
            patch("agents.validation_agent.create_validation_agent", lambda: mock_validation_agent),
        ):
            yield
    finally:
        # Restore original API key
        if original_api_key is not None:
            os.environ["OPENAI_API_KEY"] = original_api_key
        else:
            os.environ.pop("OPENAI_API_KEY", None)
