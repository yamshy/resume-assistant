import pytest
from httpx import AsyncClient

JOB_POSTING = """
Site Reliability Engineer role focusing on observability, automation, and Python tooling.
"""


@pytest.mark.asyncio
async def test_resume_download_contract(async_client: AsyncClient) -> None:
    draft = await async_client.post(
        "/api/v1/resumes/tailor",
        json={"job_posting": JOB_POSTING},
    )
    resume_id = draft.json()["resume_id"]
    await async_client.post(
        f"/api/v1/resumes/{resume_id}/approve",
        json={"decision": "approve"},
    )

    response = await async_client.get(f"/api/v1/resumes/{resume_id}/download")
    assert response.status_code == 200
    payload = response.json()
    assert payload["resume_id"] == resume_id
    assert payload["content_type"] == "text/markdown"
    assert payload["content"].startswith("# ")


@pytest.mark.asyncio
async def test_download_invalid_identifier_rejected(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/resumes/not-a-valid-uuid/download")

    assert response.status_code == 422
