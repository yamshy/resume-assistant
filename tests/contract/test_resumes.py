from uuid import uuid4

import pytest
from httpx import AsyncClient

JOB_POSTING = """
Join our platform team as a Backend Engineer. Responsibilities include designing REST APIs, collaborating with product teams, and
optimizing services. Key requirements: expertise with FastAPI, experience deploying to cloud (AWS or Azure), strong Python coding
skills, familiarity with CI/CD, and ability to document solutions clearly.
"""


@pytest.mark.asyncio
async def test_resume_tailoring_contract(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "/api/v1/resumes/tailor",
        json={"job_posting": JOB_POSTING},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "draft"
    assert payload["resume"]["markdown"].startswith("# ")
    assert payload["matching"]["overall_score"] >= 0
    assert payload["analysis"]["summary"]


@pytest.mark.asyncio
async def test_get_resume_returns_saved_resume(async_client: AsyncClient) -> None:
    creation = await async_client.post(
        "/api/v1/resumes/tailor",
        json={"job_posting": JOB_POSTING},
    )
    resume_id = creation.json()["resume_id"]

    response = await async_client.get(f"/api/v1/resumes/{resume_id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["resume_id"] == resume_id
    assert payload["resume"]["markdown"].startswith("# ")


@pytest.mark.asyncio
async def test_get_resume_missing_returns_404(async_client: AsyncClient) -> None:
    response = await async_client.get(f"/api/v1/resumes/{uuid4()}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_resume_invalid_identifier_rejected(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/resumes/not-a-valid-uuid")

    assert response.status_code == 422
