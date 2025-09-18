import pytest

from resume_core.models.profile import UserProfile
from resume_core.services.profile_service import ProfileService
from resume_core.services.resume_service import ResumeService
from resume_core.services.storage_service import StorageService


@pytest.mark.asyncio
async def test_approval_workflow_updates_status(
    tmp_path,
    sample_profile_payload: dict[str, object],
    sample_job_posting: str,
) -> None:
    storage = StorageService(base_path=tmp_path)
    profile_service = ProfileService(storage)
    resume_service = ResumeService(profile_service=profile_service, storage_service=storage)

    profile = UserProfile.model_validate(sample_profile_payload)
    await profile_service.save_profile(profile)
    result = await resume_service.tailor_resume(sample_job_posting)

    outcome = await resume_service.approve_resume(
        resume_id=str(result.resume_id),
        decision="approved",
        feedback="Ready to submit",
        approved_sections=["summary", "experience"],
    )

    assert outcome.status == "approved"
    assert outcome.revision_needed is False
