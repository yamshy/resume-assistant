import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["status"] == "ok"
    assert "timestamp" in response_data
