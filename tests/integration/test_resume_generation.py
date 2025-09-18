import pytest

from resume_core.agents.job_analysis_agent import JobAnalysisAgent
from resume_core.agents.profile_matching_agent import ProfileMatchingAgent
from resume_core.agents.resume_generation_agent import ResumeGenerationAgent
from resume_core.models.profile import UserProfile


@pytest.mark.asyncio
async def test_resume_generation_agent_creates_markdown(
    sample_profile_payload: dict[str, object], sample_job_posting: str
) -> None:
    profile = UserProfile.model_validate(sample_profile_payload)
    analysis = await JobAnalysisAgent().analyze(sample_job_posting)
    matching = await ProfileMatchingAgent().match(profile, analysis)

    agent = ResumeGenerationAgent()
    resume = await agent.generate(profile, analysis, matching)

    assert resume.full_resume_markdown.startswith("# John Developer")
    assert "## Highlighted Experience" in resume.full_resume_markdown
    assert resume.optimizations
