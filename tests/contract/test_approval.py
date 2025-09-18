import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_approve_resume_flow(
    async_client: AsyncClient,
    sample_profile_payload: dict[str, object],
    sample_job_posting: str,
) -> None:
    await async_client.put("/profile", json=sample_profile_payload)
    creation = await async_client.post(
        "/resumes/tailor",
        json={"job_description": sample_job_posting},
    )
    resume_id = creation.json()["resume_id"]

    response = await async_client.post(
        f"/resumes/{resume_id}/approve",
        json={
            "decision": "approved",
            "feedback": "Looks great!",
            "approved_sections": ["summary", "experience"],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "approved"
    assert payload["revision_needed"] is False
    assert payload["final_resume_url"].endswith(f"/resumes/{resume_id}/download?format=markdown")
    assert any("Download" in step for step in payload["next_steps"])
