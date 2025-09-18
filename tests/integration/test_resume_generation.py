import pytest

from resume_core.agents.job_analysis_agent import JobAnalysisAgent
from resume_core.agents.profile_matching_agent import ProfileMatchingAgent
from resume_core.agents.resume_generation_agent import ResumeGenerationAgent
from resume_core.models.resume import TailoredResume
from tests.factories import SAMPLE_JOB_POSTING, build_sample_profile


@pytest.mark.asyncio
async def test_resume_generation_produces_markdown() -> None:
    profile = build_sample_profile()
    analysis = await JobAnalysisAgent().analyze(job_posting=SAMPLE_JOB_POSTING)
    matching = await ProfileMatchingAgent().match(profile=profile, analysis=analysis)
    resume = await ResumeGenerationAgent().generate(
        profile=profile,
        analysis=analysis,
        matching=matching,
    )
    assert isinstance(resume, TailoredResume)
    assert resume.markdown.startswith("# ")
    assert "FastAPI" in resume.markdown
