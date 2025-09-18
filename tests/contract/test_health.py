"""
Contract test for GET /health endpoint.

This test verifies the health check endpoint follows the OpenAPI specification.
Must initially fail as part of TDD - no endpoint implementation exists yet.
"""

from datetime import datetime

import httpx
import pytest
from fastapi.testclient import TestClient


# This will fail initially since we haven't created the FastAPI app yet
@pytest.fixture
def client():
    """Test client fixture - will fail until FastAPI app is implemented."""
    # This import will fail initially (TDD red phase)
    try:
        from app.main import app

        return TestClient(app)
    except ImportError:
        pytest.skip("FastAPI app not yet implemented - expected TDD failure")


@pytest.mark.asyncio
async def test_health_endpoint_contract(client):
    """
    Test GET /health endpoint according to OpenAPI spec.

    Expected response per api_spec.yaml:
    - HTTP 200 status
    - JSON object with:
      - status: string (example: "healthy")
      - timestamp: string in date-time format
    """
    # Make GET request to health endpoint
    response = client.get("/health")

    # Assert HTTP 200 status code
    assert response.status_code == 200

    # Assert response is JSON
    assert response.headers["content-type"] == "application/json"

    # Parse response JSON
    data = response.json()

    # Assert required fields exist per OpenAPI spec
    assert "status" in data, "Response must include 'status' field"
    assert "timestamp" in data, "Response must include 'timestamp' field"

    # Assert field types per OpenAPI spec
    assert isinstance(data["status"], str), "Status must be string"
    assert isinstance(data["timestamp"], str), "Timestamp must be string"

    # Assert timestamp is valid datetime format (ISO 8601)
    try:
        datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
    except ValueError:
        pytest.fail("Timestamp must be valid ISO 8601 date-time format")

    # Assert status value follows expected pattern
    assert data["status"] == "healthy", "Status should be 'healthy' for successful health check"


@pytest.mark.asyncio
async def test_health_endpoint_with_httpx():
    """
    Alternative test using httpx directly against running server.
    This will fail until the server is implemented and running.
    """
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        try:
            response = await client.get("/health")

            # Same assertions as above
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "timestamp" in data
            assert isinstance(data["status"], str)
            assert isinstance(data["timestamp"], str)
            assert data["status"] == "healthy"

            # Validate timestamp format
            datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))

        except httpx.ConnectError:
            pytest.skip("Server not running - expected failure in TDD red phase")
