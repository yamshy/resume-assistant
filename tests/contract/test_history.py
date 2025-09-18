from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _prepare_history(
    async_client: AsyncClient,
    sample_profile_payload: dict[str, object],
    sample_job_posting: str,
) -> tuple[str, str]:
    await async_client.put("/profile", json=sample_profile_payload)

    first = await async_client.post(
        "/resumes/tailor", json={"job_description": sample_job_posting}
    )
    assert first.status_code == 200
    first_id = first.json()["resume_id"]

    approval = await async_client.post(
        f"/resumes/{first_id}/approve",
        json={
            "decision": "approved",
            "feedback": "Ship it",
            "approved_sections": ["summary", "experience", "skills"],
        },
    )
    assert approval.status_code == 200

    second = await async_client.post(
        "/resumes/tailor", json={"job_description": sample_job_posting}
    )
    assert second.status_code == 200
    second_id = second.json()["resume_id"]
    return first_id, second_id


@pytest.mark.asyncio
async def test_get_resume_history(
    async_client: AsyncClient,
    sample_profile_payload: dict[str, object],
    sample_job_posting: str,
) -> None:
    approved_id, pending_id = await _prepare_history(
        async_client, sample_profile_payload, sample_job_posting
    )

    response = await async_client.get(
        "/resumes/history", params={"limit": 1, "offset": 0}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["limit"] == 1
    assert body["offset"] == 0
    assert len(body["resumes"]) == 1
    first_entry = body["resumes"][0]
    assert first_entry["resume_id"] == pending_id
    assert first_entry["status"] == "pending"
    assert 0 <= first_entry["match_score"] <= 1

    offset_response = await async_client.get(
        "/resumes/history", params={"limit": 1, "offset": 1}
    )
    assert offset_response.status_code == 200
    offset_body = offset_response.json()
    assert len(offset_body["resumes"]) == 1
    second_entry = offset_body["resumes"][0]
    assert second_entry["resume_id"] == approved_id
    assert second_entry["status"] == "approved"
