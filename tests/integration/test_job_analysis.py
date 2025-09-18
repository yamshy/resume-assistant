import pytest

from resume_core.agents.job_analysis_agent import JobAnalysisAgent


@pytest.mark.asyncio
async def test_job_analysis_agent_extracts_requirements(sample_job_posting: str) -> None:
    agent = JobAnalysisAgent()
    result = await agent.analyze(sample_job_posting)

    keywords = {req.skill for req in result.requirements}
    assert {"Python", "FastAPI", "PostgreSQL"}.issubset(keywords)
    assert result.role_level == "senior"
