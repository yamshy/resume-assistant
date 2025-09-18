import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert "timestamp" in payload
