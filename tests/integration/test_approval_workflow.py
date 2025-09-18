import pytest

from resume_core.services.profile_service import ProfileService
from resume_core.services.resume_service import ResumeTailoringService
from tests.factories import SAMPLE_JOB_POSTING, build_sample_profile


@pytest.mark.asyncio
async def test_approval_workflow_records_decisions(tmp_path) -> None:
    profile_service = ProfileService(base_path=tmp_path)
    profile_service.save_profile(build_sample_profile())
    resume_service = ResumeTailoringService(profile_service=profile_service)
    result = await resume_service.tailor_resume(job_posting=SAMPLE_JOB_POSTING)

    approval = await resume_service.approve_resume(
        resume_id=result.resume.resume_id,
        decision="approve",
        comments="Ready to submit",
    )

    assert approval.status == "approved"
    assert approval.history[-1].decision == "approved"
    assert approval.history[-1].comments == "Ready to submit"
