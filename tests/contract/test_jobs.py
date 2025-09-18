import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_job_analysis_returns_key_skills(
    async_client: AsyncClient, sample_job_posting: str
) -> None:
    response = await async_client.post(
        "/jobs/analyze", json={"job_description": sample_job_posting}
    )
    assert response.status_code == 200

    analysis = response.json()
    assert analysis["job_title"].lower().startswith("senior software engineer")
    extracted = {req["skill"] for req in analysis["requirements"]}
    assert {"Python", "FastAPI"}.issubset(extracted)
    assert analysis["role_level"] == "senior"


@pytest.mark.asyncio
async def test_job_analysis_validates_input(async_client: AsyncClient) -> None:
    response = await async_client.post("/jobs/analyze", json={"job_description": ""})
    assert response.status_code == 400
    payload = response.json()
    assert payload["error"] == "invalid_job_description"
