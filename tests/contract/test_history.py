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

        Expected behavior per implementation:
        - Status: 200 OK
        - Content-Type: application/json
        - Response body: HistoryResponse schema with pagination info
        """
        response = await async_client.get("/api/v1/resumes/history")

        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

        history_data = response.json()

        # Verify HistoryResponse schema
        assert "history" in history_data
        assert "total_count" in history_data
        assert "page" in history_data
        assert "page_size" in history_data
        assert "has_more" in history_data
        assert "message" in history_data

        # Verify data types
        assert isinstance(history_data["history"], list)
        assert isinstance(history_data["total_count"], int)
        assert isinstance(history_data["page"], int)
        assert isinstance(history_data["page_size"], int)
        assert isinstance(history_data["has_more"], bool)
        assert isinstance(history_data["message"], str)

        # Verify HistoryItem structure if history exists
        if history_data["history"]:
            history_item = history_data["history"][0]
            assert "exported_at" in history_item
            assert "job_title" in history_item
            assert "company_name" in history_item
            assert "resume_file" in history_item
            assert "file_path" in history_item
            assert "file_size" in history_item
            assert "optimizations_count" in history_item

    @pytest.mark.asyncio
    async def test_get_resume_history_with_page_size(self, async_client: AsyncClient) -> None:
        """Test GET /resumes/history with page_size parameter."""
        response = await async_client.get("/api/v1/resumes/history?page_size=5")

        assert response.status_code == 200
        history_data = response.json()

        # Verify page_size is respected
        assert history_data["page_size"] == 5
        assert len(history_data["history"]) <= 5

    @pytest.mark.asyncio
    async def test_get_resume_history_with_page(self, async_client: AsyncClient) -> None:
        """Test GET /resumes/history with page parameter."""
        response = await async_client.get("/api/v1/resumes/history?page=2")

        assert response.status_code == 200
        history_data = response.json()

        # Verify page is applied
        assert history_data["page"] == 2

    @pytest.mark.asyncio
    async def test_get_resume_history_with_page_and_page_size(self, async_client: AsyncClient) -> None:
        """Test GET /resumes/history with both page and page_size parameters."""
        response = await async_client.get("/api/v1/resumes/history?page=2&page_size=3")

        assert response.status_code == 200
        history_data = response.json()

        # Verify parameters are applied
        assert history_data["page"] == 2
        assert history_data["page_size"] == 3
        assert len(history_data["history"]) <= 3

    @pytest.mark.asyncio
    async def test_get_resume_history_default_parameters(self, async_client: AsyncClient) -> None:
        """Test GET /resumes/history uses default parameters when none provided."""
        response = await async_client.get("/api/v1/resumes/history")

        assert response.status_code == 200
        history_data = response.json()

        # Verify default values per OpenAPI spec
        assert history_data["page"] == 1      # Default page
        assert history_data["page_size"] == 10  # Default page_size

    @pytest.mark.asyncio
    async def test_get_resume_history_page_size_validation(self, async_client: AsyncClient) -> None:
        """Test GET /resumes/history validates page_size parameter constraints."""
        # Test minimum page_size (should be 1)
        response = await async_client.get("/api/v1/resumes/history?page_size=0")
        assert response.status_code == 422  # Validation error

        # Test maximum page_size (should be 100)
        response = await async_client.get("/api/v1/resumes/history?page_size=101")
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_resume_history_page_validation(self, async_client: AsyncClient) -> None:
        """Test GET /resumes/history validates page parameter constraints."""
        # Test negative page (should be >= 1)
        response = await async_client.get("/api/v1/resumes/history?page=0")
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_resume_history_invalid_parameter_types(self, async_client: AsyncClient) -> None:
        """Test GET /resumes/history handles invalid parameter types."""
        # Test non-integer page_size
        response = await async_client.get("/api/v1/resumes/history?page_size=abc")
        assert response.status_code == 422  # Validation error

        # Test non-integer page
        response = await async_client.get("/api/v1/resumes/history?page=xyz")
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_get_resume_history_empty_result(self, async_client: AsyncClient) -> None:
        """Test GET /resumes/history handles empty history gracefully."""
        response = await async_client.get("/api/v1/resumes/history")

        assert response.status_code == 200
        history_data = response.json()

        # Should return valid structure even when empty
        assert "history" in history_data
        assert "total_count" in history_data
        assert "page" in history_data
        assert "page_size" in history_data
        assert "has_more" in history_data
        assert "message" in history_data

        # Empty case should have total_count = 0 and empty history array
        if history_data["total_count"] == 0:
            assert history_data["history"] == []