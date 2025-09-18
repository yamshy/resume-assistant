from datetime import datetime

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_profile_not_found(async_client: AsyncClient) -> None:
    response = await async_client.get("/profile")
    assert response.status_code == 404
    payload = response.json()
    assert payload["error"] == "profile_not_found"
    datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00"))


@pytest.mark.asyncio
async def test_put_profile_updates_metadata(
    async_client: AsyncClient, sample_profile_payload: dict[str, object]
) -> None:
    response = await async_client.put("/profile", json=sample_profile_payload)
    assert response.status_code == 200

    saved = response.json()
    assert saved["contact"]["name"] == sample_profile_payload["contact"]["name"]
    assert saved["metadata"]["updated_at"] != sample_profile_payload["metadata"]["updated_at"]
    datetime.fromisoformat(saved["metadata"]["updated_at"].replace("Z", "+00:00"))


@pytest.mark.asyncio
async def test_get_profile_returns_saved_data(
    async_client: AsyncClient, sample_profile_payload: dict[str, object]
) -> None:
    await async_client.put("/profile", json=sample_profile_payload)

    response = await async_client.get("/profile")
    assert response.status_code == 200
    payload = response.json()
    assert payload["contact"]["email"] == sample_profile_payload["contact"]["email"]
    assert len(payload["experience"]) == len(sample_profile_payload["experience"])
