import pytest
from httpx import AsyncClient

JOB_POSTING = """
Security Engineer role focusing on threat modeling and automation. Requires Python, cloud security, and collaboration skills.
"""


@pytest.mark.asyncio
async def test_resume_history_contract(async_client: AsyncClient) -> None:
    await async_client.post(
        "/api/v1/resumes/tailor",
        json={"job_posting": JOB_POSTING},
    )

    response = await async_client.get("/api/v1/resumes/history")
    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload
    assert payload["items"]
    assert {"resume_id", "status"}.issubset(payload["items"][0].keys())
