import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_download_tailored_resume(
    async_client: AsyncClient,
    sample_profile_payload: dict[str, object],
    sample_job_posting: str,
) -> None:
    await async_client.put("/profile", json=sample_profile_payload)
    creation = await async_client.post(
        "/resumes/tailor", json={"job_description": sample_job_posting}
    )
    resume_id = creation.json()["resume_id"]

    response = await async_client.get(
        f"/resumes/{resume_id}/download", params={"format": "markdown"}
    )
    assert response.status_code == 200
    assert "text/markdown" in response.headers["content-type"].lower()
    assert "# John Developer" in response.text
