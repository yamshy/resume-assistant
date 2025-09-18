import pytest
from httpx import AsyncClient

JOB_POSTING = """
We are seeking a Senior Data Scientist to lead our analytics initiatives. Responsibilities include building machine learning
models, collaborating with engineering, and communicating insights. Requirements: 5+ years experience, proficiency in Python and
SQL, experience with cloud platforms like AWS, strong communication skills, and ability to mentor junior scientists.
"""


@pytest.mark.asyncio
async def test_job_analysis_contract(async_client: AsyncClient) -> None:
    response = await async_client.post(
        "/api/v1/jobs/analyze",
        json={"job_posting": JOB_POSTING},
    )
    assert response.status_code == 200
    payload = response.json()
    analysis = payload["analysis"]
    assert analysis["summary"]
    assert any(req["name"].lower().startswith("python") for req in analysis["requirements"])
    assert analysis["keywords"]
