import pytest

from resume_core.agents.job_analysis_agent import JobAnalysisAgent
from tests.factories import SAMPLE_JOB_POSTING


@pytest.mark.asyncio
async def test_job_analysis_agent_extracts_requirements() -> None:
    agent = JobAnalysisAgent()
    analysis = await agent.analyze(job_posting=SAMPLE_JOB_POSTING)
    assert analysis.summary
    assert analysis.requirements
    assert any("fastapi" in keyword for keyword in analysis.keywords)
