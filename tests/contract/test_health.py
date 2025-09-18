import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_contract_health_endpoint(async_client: AsyncClient) -> None:
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
