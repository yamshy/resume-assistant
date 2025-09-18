from __future__ import annotations

from urllib.parse import quote

import pytest
from httpx import AsyncClient


async def _create_resume(
    async_client: AsyncClient,
    sample_profile_payload: dict[str, object],
    sample_job_posting: str,
) -> str:
    await async_client.put("/profile", json=sample_profile_payload)
    creation = await async_client.post(
        "/resumes/tailor", json={"job_description": sample_job_posting}
    )
    assert creation.status_code == 200
    return creation.json()["resume_id"]


@pytest.mark.asyncio
async def test_download_tailored_resume_markdown(
    async_client: AsyncClient,
    sample_profile_payload: dict[str, object],
    sample_job_posting: str,
) -> None:
    resume_id = await _create_resume(
        async_client, sample_profile_payload, sample_job_posting
    )

    response = await async_client.get(
        f"/resumes/{resume_id}/download", params={"format": "markdown"}
    )
    assert response.status_code == 200
    assert "text/markdown" in response.headers["content-type"].lower()
    assert "# John Developer" in response.text


@pytest.mark.asyncio
async def test_download_tailored_resume_pdf(
    async_client: AsyncClient,
    sample_profile_payload: dict[str, object],
    sample_job_posting: str,
) -> None:
    resume_id = await _create_resume(
        async_client, sample_profile_payload, sample_job_posting
    )

    response = await async_client.get(
        f"/resumes/{resume_id}/download", params={"format": "pdf"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert response.content.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_download_tailored_resume_docx(
    async_client: AsyncClient,
    sample_profile_payload: dict[str, object],
    sample_job_posting: str,
) -> None:
    resume_id = await _create_resume(
        async_client, sample_profile_payload, sample_job_posting
    )

    response = await async_client.get(
        f"/resumes/{resume_id}/download", params={"format": "docx"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert response.content.startswith(b"PK")


@pytest.mark.asyncio
async def test_download_tailored_resume_invalid_format(
    async_client: AsyncClient,
    sample_profile_payload: dict[str, object],
    sample_job_posting: str,
) -> None:
    resume_id = await _create_resume(
        async_client, sample_profile_payload, sample_job_posting
    )

    response = await async_client.get(
        f"/resumes/{resume_id}/download", params={"format": "txt"}
    )
    assert response.status_code == 400
    assert response.json()["error"] == "unsupported_format"


@pytest.mark.asyncio
async def test_download_rejects_traversal_attempt(async_client: AsyncClient) -> None:
    traversal_id = quote("../../etc/passwd")
    response = await async_client.get(
        f"/resumes/{traversal_id}/download", params={"format": "markdown"}
    )
    assert response.status_code in {404, 422}
