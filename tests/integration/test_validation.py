import pytest

from resume_core.agents.job_analysis_agent import JobAnalysisAgent
from resume_core.agents.profile_matching_agent import ProfileMatchingAgent
from resume_core.agents.resume_generation_agent import ResumeGenerationAgent
from resume_core.agents.validation_agent import ValidationAgent
from resume_core.models.profile import UserProfile
from resume_core.models.resume import TailoredResume


@pytest.mark.asyncio
async def test_validation_agent_flags_missing_skills(
    sample_profile_payload: dict[str, object], sample_job_posting: str
) -> None:
    profile = UserProfile.model_validate(sample_profile_payload)
    analysis = await JobAnalysisAgent().analyze(sample_job_posting)
    matching = await ProfileMatchingAgent().match(profile, analysis)
    resume = await ResumeGenerationAgent().generate(profile, analysis, matching)

    validation = await ValidationAgent().validate(profile, analysis, matching, resume)
    assert validation.is_valid

    stripped_resume = TailoredResume(
        job_title=resume.job_title,
        company_name=resume.company_name,
        optimizations=[],
        full_resume_markdown="# John Developer\n",
        summary_of_changes="",
        estimated_match_score=0.0,
        generation_timestamp=resume.generation_timestamp,
    )
    failed = await ValidationAgent().validate(profile, analysis, matching, stripped_resume)
    assert failed.is_valid is False
    assert any(issue.severity == "high" for issue in failed.issues)
