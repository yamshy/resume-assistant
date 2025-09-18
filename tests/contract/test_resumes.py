import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_tailor_resume_pipeline(
    async_client: AsyncClient,
    sample_profile_payload: dict[str, object],
    sample_job_posting: str,
) -> None:
    await async_client.put("/profile", json=sample_profile_payload)

    response = await async_client.post(
        "/resumes/tailor",
        json={
            "job_description": sample_job_posting,
            "preferences": {"emphasis_areas": ["Python", "FastAPI"], "excluded_sections": []},
        },
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["resume_id"]
    analysis = payload["job_analysis"]
    matching = payload["matching_result"]
    resume = payload["tailored_resume"]
    validation = payload["validation_result"]
    approval = payload["approval_workflow"]

    assert analysis["job_title"].startswith("Senior Software Engineer")
    assert matching["overall_match_score"] >= 0
    assert resume["full_resume_markdown"].startswith("# John Developer")
    assert validation["is_valid"] is True
    assert approval["confidence_score"] >= 0
