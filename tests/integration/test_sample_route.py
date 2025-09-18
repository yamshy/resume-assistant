import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint_integration(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_invalid_endpoint_returns_404(async_client: AsyncClient):
    response = await async_client.get("/api/v1/nonexistent")
    assert response.status_code == 404
