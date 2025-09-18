"""
Contract tests for the GET /resumes/history endpoint.

This test validates the API contract according to the OpenAPI specification.
The endpoint should return paginated resume history with limit/offset parameters.

This is a TDD test that MUST FAIL initially since the endpoint doesn't exist yet.
"""

import pytest
from httpx import AsyncClient


class TestResumeHistoryEndpoint:
    """Contract tests for GET /resumes/history endpoint."""

    @pytest.mark.asyncio
    async def test_get_resume_history_success(self, async_client: AsyncClient) -> None:
        """
        Test GET /resumes/history returns paginated resume history.

        Expected behavior per OpenAPI spec:
        - Status: 200 OK
        - Content-Type: application/json
        - Response body: Object with resumes array, total, limit, offset
        """
        # This test should FAIL initially - endpoint doesn't exist yet
        response = await async_client.get("/api/v1/resumes/history")

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

        history_data = response.json()

        # Verify response structure per OpenAPI spec
        assert "resumes" in history_data
        assert "total" in history_data
        assert "limit" in history_data
        assert "offset" in history_data

        # Verify data types
        assert isinstance(history_data["resumes"], list)
        assert isinstance(history_data["total"], int)
        assert isinstance(history_data["limit"], int)
        assert isinstance(history_data["offset"], int)

        # Verify ResumeHistoryItem structure if resumes exist
        if history_data["resumes"]:
            resume_item = history_data["resumes"][0]
            assert "resume_id" in resume_item
            assert "job_title" in resume_item
            assert "company_name" in resume_item
            assert "created_at" in resume_item
            assert "status" in resume_item
            assert "match_score" in resume_item

            # Verify data types
            assert isinstance(resume_item["resume_id"], str)
            assert isinstance(resume_item["job_title"], str)
            assert isinstance(resume_item["company_name"], str)
            assert isinstance(resume_item["created_at"], str)
            assert isinstance(resume_item["status"], str)
            assert isinstance(resume_item["match_score"], (int, float))

            # Verify enum values
            assert resume_item["status"] in ["pending", "approved", "rejected", "needs_revision"]
            assert 0 <= resume_item["match_score"] <= 1

    @pytest.mark.asyncio
    async def test_get_resume_history_with_limit(self, async_client: AsyncClient) -> None:
        """Test GET /resumes/history with limit parameter."""
        response = await async_client.get("/resumes/history?limit=5")

        assert response.status_code == 200
        history_data = response.json()

        # Verify limit is respected
        assert history_data["limit"] == 5
        assert len(history_data["resumes"]) <= 5

    @pytest.mark.asyncio
    async def test_get_resume_history_with_offset(self, async_client: AsyncClient) -> None:
        """Test GET /resumes/history with offset parameter."""
        response = await async_client.get("/resumes/history?offset=10")

        assert response.status_code == 200
        history_data = response.json()

        # Verify offset is applied
        assert history_data["offset"] == 10

    @pytest.mark.asyncio
    async def test_get_resume_history_with_limit_and_offset(self, async_client: AsyncClient) -> None:
        """Test GET /resumes/history with both limit and offset parameters."""
        response = await async_client.get("/resumes/history?limit=3&offset=5")

        assert response.status_code == 200
        history_data = response.json()

        # Verify parameters are applied
        assert history_data["limit"] == 3
        assert history_data["offset"] == 5
        assert len(history_data["resumes"]) <= 3

    @pytest.mark.asyncio
    async def test_get_resume_history_default_parameters(self, async_client: AsyncClient) -> None:
        """Test GET /resumes/history uses default parameters when none provided."""
        response = await async_client.get("/api/v1/resumes/history")

        assert response.status_code == 200
        history_data = response.json()

        # Verify default values per OpenAPI spec
        assert history_data["limit"] == 10  # Default limit
        assert history_data["offset"] == 0   # Default offset

    @pytest.mark.asyncio
    async def test_get_resume_history_limit_validation(self, async_client: AsyncClient) -> None:
        """Test GET /resumes/history validates limit parameter constraints."""
        # Test minimum limit (should be 1)
        response = await async_client.get("/resumes/history?limit=0")
        assert response.status_code == 422  # Validation error

        # Test maximum limit (should be 100)
        response = await async_client.get("/resumes/history?limit=101")
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_resume_history_offset_validation(self, async_client: AsyncClient) -> None:
        """Test GET /resumes/history validates offset parameter constraints."""
        # Test negative offset (should be >= 0)
        response = await async_client.get("/resumes/history?offset=-1")
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_resume_history_invalid_parameter_types(self, async_client: AsyncClient) -> None:
        """Test GET /resumes/history handles invalid parameter types."""
        # Test non-integer limit
        response = await async_client.get("/resumes/history?limit=abc")
        assert response.status_code == 422  # Validation error

        # Test non-integer offset
        response = await async_client.get("/resumes/history?offset=xyz")
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_resume_history_empty_result(self, async_client: AsyncClient) -> None:
        """Test GET /resumes/history handles empty history gracefully."""
        response = await async_client.get("/api/v1/resumes/history")

        assert response.status_code == 200
        history_data = response.json()

        # Should return valid structure even when empty
        assert "resumes" in history_data
        assert "total" in history_data
        assert "limit" in history_data
        assert "offset" in history_data

        # Empty case should have total = 0 and empty resumes array
        if history_data["total"] == 0:
            assert history_data["resumes"] == []