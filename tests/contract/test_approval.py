import pytest
from httpx import AsyncClient

JOB_POSTING = """
Principal Engineer needed to lead architecture and mentor teams. Requirements include strong communication, experience with
FastAPI services, background in DevOps, and ability to write clear technical documentation.
"""


@pytest.mark.asyncio
async def test_resume_approval_contract(async_client: AsyncClient) -> None:
    draft = await async_client.post(
        "/api/v1/resumes/tailor",
        json={"job_posting": JOB_POSTING},
    )
    resume_id = draft.json()["resume_id"]

    response = await async_client.post(
        f"/api/v1/resumes/{resume_id}/approve",
        json={"decision": "approve", "comments": "Looks great"},
    )
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "approved"
    assert result["resume_id"] == resume_id
    assert result["decision"]["decision"] == "approved"


@pytest.mark.asyncio
async def test_resume_approval_invalid_identifier_rejected(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "/api/v1/resumes/not-a-valid-uuid/approve",
        json={"decision": "approve"},
    )

    assert response.status_code == 422
