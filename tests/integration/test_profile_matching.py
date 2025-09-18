import pytest

from resume_core.agents.job_analysis_agent import JobAnalysisAgent
from resume_core.agents.profile_matching_agent import ProfileMatchingAgent
from resume_core.models.profile import UserProfile


@pytest.mark.asyncio
async def test_profile_matching_agent_scores_skills(
    sample_profile_payload: dict[str, object], sample_job_posting: str
) -> None:
    profile = UserProfile.model_validate(sample_profile_payload)
    analysis = await JobAnalysisAgent().analyze(sample_job_posting)

    agent = ProfileMatchingAgent()
    result = await agent.match(profile, analysis)

    assert result.overall_match_score >= 0.5
    assert any(match.skill_name == "Python" for match in result.skill_matches)
    missing = {req.skill for req in result.missing_requirements}
    assert "Kubernetes" in missing
