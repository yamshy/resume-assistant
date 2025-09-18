import pytest

from resume_core.models.profile import UserProfile
from resume_core.services.profile_service import ProfileService
from resume_core.services.resume_service import ResumeService
from resume_core.services.storage_service import StorageService


@pytest.mark.asyncio
async def test_complete_agent_chain(
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

    assert result.tailored_resume.full_resume_markdown.startswith("# John Developer")
    assert "## Summary" in result.tailored_resume.full_resume_markdown
    assert result.job_analysis.job_title.lower().startswith("senior software engineer")
    assert result.matching_result.overall_match_score >= 0.5
    assert result.validation_result.is_valid is True
    assert result.approval_workflow.confidence_score >= 0.7
