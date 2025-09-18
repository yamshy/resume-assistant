"""
Contract tests for /jobs/analyze endpoint.

This test validates the API contract according to the OpenAPI specification.
The endpoint should accept job descriptions and return structured job analysis.

This is a TDD test that MUST FAIL initially since the endpoint doesn't exist yet.
"""

import pytest
from httpx import AsyncClient


class TestJobsAnalyzeEndpoint:
    """Contract tests for POST /jobs/analyze endpoint."""

    async def test_analyze_job_success(self, async_client: AsyncClient) -> None:
        """Test successful job analysis with valid job description."""
        # Valid job description input
        request_payload = {
            "job_description": """
            Software Engineer at TechCorp

            We are seeking a skilled Software Engineer to join our development team.

            Required Skills:
            - Python programming (3+ years)
            - FastAPI framework
            - RESTful API development
            - SQL databases
            - Git version control

            Responsibilities:
            - Develop and maintain web applications
            - Write clean, testable code
            - Collaborate with cross-functional teams
            - Participate in code reviews

            Location: San Francisco, CA
            Remote work available
            """
        }

        # Make POST request to /jobs/analyze
        response = await async_client.post("/api/v1/jobs/analyze", json=request_payload)

        # Assert successful response
        assert response.status_code == 200

        # Validate response structure matches JobAnalysis schema
        response_data = response.json()

        # Required fields from JobAnalysis schema
        assert "company_name" in response_data
        assert "job_title" in response_data
        assert "location" in response_data
        assert "requirements" in response_data
        assert "key_responsibilities" in response_data
        assert "company_culture" in response_data
        assert "role_level" in response_data
        assert "industry" in response_data

        # Validate data types and structure
        assert isinstance(response_data["company_name"], str)
        assert isinstance(response_data["job_title"], str)
        assert isinstance(response_data["location"], str)
        assert isinstance(response_data["requirements"], list)
        assert isinstance(response_data["key_responsibilities"], list)
        assert isinstance(response_data["company_culture"], str)
        assert isinstance(response_data["role_level"], str)
        assert isinstance(response_data["industry"], str)

        # Validate requirements array structure
        if response_data["requirements"]:
            req = response_data["requirements"][0]
            assert "skill" in req
            assert "importance" in req
            assert "category" in req
            assert "is_required" in req
            assert "context" in req
            assert isinstance(req["importance"], int)
            assert 1 <= req["importance"] <= 5
            assert req["category"] in ["technical", "soft", "language", "certification"]
            assert isinstance(req["is_required"], bool)

        # Validate role_level enum
        assert response_data["role_level"] in ["junior", "mid", "senior", "lead", "executive"]

        # Optional fields validation
        if "department" in response_data:
            assert isinstance(response_data["department"], (str, type(None)))
        if "remote_policy" in response_data:
            assert isinstance(response_data["remote_policy"], (str, type(None)))
        if "salary_range" in response_data:
            assert isinstance(response_data["salary_range"], (str, type(None)))
        if "benefits" in response_data:
            assert isinstance(response_data["benefits"], list)
        if "preferred_qualifications" in response_data:
            assert isinstance(response_data["preferred_qualifications"], list)

    async def test_analyze_job_invalid_request_missing_field(self, async_client: AsyncClient) -> None:
        """Test job analysis with missing required job_description field."""
        # Missing job_description field
        request_payload = {}

        # Make POST request to /jobs/analyze
        response = await async_client.post("/api/v1/jobs/analyze", json=request_payload)

        # Assert validation error response
        assert response.status_code == 400

        # Validate error response structure
        response_data = response.json()
        assert "error" in response_data
        assert "timestamp" in response_data
        assert isinstance(response_data["error"], str)

    async def test_analyze_job_invalid_request_empty_description(self, async_client: AsyncClient) -> None:
        """Test job analysis with empty job description."""
        # Empty job description
        request_payload = {
            "job_description": ""
        }

        # Make POST request to /jobs/analyze
        response = await async_client.post("/api/v1/jobs/analyze", json=request_payload)

        # Assert validation error response
        assert response.status_code == 400

        # Validate error response structure
        response_data = response.json()
        assert "error" in response_data
        assert "timestamp" in response_data

    async def test_analyze_job_invalid_request_wrong_type(self, async_client: AsyncClient) -> None:
        """Test job analysis with wrong data type for job_description."""
        # Wrong data type (should be string)
        request_payload = {
            "job_description": 12345
        }

        # Make POST request to /jobs/analyze
        response = await async_client.post("/api/v1/jobs/analyze", json=request_payload)

        # Assert validation error response
        assert response.status_code == 400

        # Validate error response structure
        response_data = response.json()
        assert "error" in response_data
        assert "timestamp" in response_data

    async def test_analyze_job_minimal_description(self, async_client: AsyncClient) -> None:
        """Test job analysis with minimal but valid job description."""
        # Minimal valid job description
        request_payload = {
            "job_description": "Software Developer needed for startup. Python required."
        }

        # Make POST request to /jobs/analyze
        response = await async_client.post("/api/v1/jobs/analyze", json=request_payload)

        # Should succeed with minimal input
        assert response.status_code == 200

        # Validate required fields are present
        response_data = response.json()
        assert "company_name" in response_data
        assert "job_title" in response_data
        assert "location" in response_data
        assert "requirements" in response_data
        assert "key_responsibilities" in response_data
        assert "company_culture" in response_data
        assert "role_level" in response_data
        assert "industry" in response_data

    async def test_analyze_job_content_type_validation(self, async_client: AsyncClient) -> None:
        """Test that endpoint only accepts JSON content type."""
        # Valid job description but wrong content type
        response = await async_client.post(
            "/api/v1/jobs/analyze",
            data="job_description=Software Developer position",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        # Should reject non-JSON content
        assert response.status_code in [400, 415]  # Bad Request or Unsupported Media Type