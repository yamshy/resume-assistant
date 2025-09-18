import pytest
from httpx import AsyncClient


from datetime import datetime


@pytest.mark.asyncio
async def test_health_contract(async_client: AsyncClient) -> None:
    response = await async_client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    timestamp = payload["timestamp"]
    # Ensure timestamp is ISO-8601 parseable
    datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
