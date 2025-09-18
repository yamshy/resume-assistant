import pytest

from resume_core.agents.job_analysis_agent import JobAnalysisAgent
from resume_core.agents.profile_matching_agent import ProfileMatchingAgent
from tests.factories import SAMPLE_JOB_POSTING, build_sample_profile


@pytest.mark.asyncio
async def test_profile_matching_scores_skills() -> None:
    analysis = await JobAnalysisAgent().analyze(job_posting=SAMPLE_JOB_POSTING)
    matching = await ProfileMatchingAgent().match(
        profile=build_sample_profile(),
        analysis=analysis,
    )
    assert matching.overall_score > 0.5
    assert matching.matched_skills
    assert matching.recommendations
