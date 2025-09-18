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
