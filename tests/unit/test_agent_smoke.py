import pytest

from agents.base_agent import Agent
from services.analysis import AnalysisService


@pytest.mark.asyncio
async def test_agent_initialization():
    agent = Agent(model_name="gpt-4o")
    assert agent.model_name == "gpt-4o"
    assert agent.api_key is None
    assert not agent._initialized


@pytest.mark.asyncio
async def test_agent_run_requires_mock(mock_agent_async):
    agent = Agent()
    result = await agent.run("test input")
    assert "analysis" in result
    assert result["analysis"] == "Analyzed: test input"


@pytest.mark.asyncio
async def test_analysis_service_with_mock(mock_agent_async):
    service = AnalysisService()
    result = await service.analyze("sample text")
    assert result["status"] == "success"
    assert "result" in result
    assert result["result"]["analysis"] == "Analyzed: sample text"


@pytest.mark.asyncio
async def test_analysis_service_empty_input():
    service = AnalysisService()
    result = await service.analyze("")
    assert result["error"] == "Empty input provided"


@pytest.mark.asyncio
async def test_analysis_service_without_mock():
    service = AnalysisService()
    result = await service.analyze("test without mock")
    assert result["status"] == "mock_required"
    assert result["input"] == "test without mock"
