import pytest

from resume_core.services.profile_service import ProfileService
from resume_core.services.resume_service import ResumeTailoringService
from tests.factories import SAMPLE_JOB_POSTING, build_sample_profile


@pytest.mark.asyncio
async def test_agent_chain_workflow(tmp_path) -> None:
    profile_service = ProfileService(base_path=tmp_path)
    profile_service.save_profile(build_sample_profile())
    resume_service = ResumeTailoringService(profile_service=profile_service)

    result = await resume_service.tailor_resume(job_posting=SAMPLE_JOB_POSTING)

    assert result.resume.resume_id
    assert result.analysis.requirements
    assert result.matching.overall_score > 0
    assert result.validation.passed is True
    assert result.recommendation.decision in {"approved", "changes_requested"}
