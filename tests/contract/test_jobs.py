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

        # Validate JobAnalysisResponse wrapper structure
        response_data = response.json()

        # Verify wrapper fields
        assert "job_analysis" in response_data
        assert "analysis_metadata" in response_data
        assert "message" in response_data

        # Get the nested job analysis data
        job_analysis = response_data["job_analysis"]

        # Required fields from JobAnalysis schema
        assert "company_name" in job_analysis
        assert "job_title" in job_analysis
        assert "location" in job_analysis
        assert "requirements" in job_analysis
        assert "key_responsibilities" in job_analysis
        assert "company_culture" in job_analysis
        assert "role_level" in job_analysis
        assert "industry" in job_analysis

        # Validate data types and structure
        assert isinstance(job_analysis["company_name"], str)
        assert isinstance(job_analysis["job_title"], str)
        assert isinstance(job_analysis["location"], str)
        assert isinstance(job_analysis["requirements"], list)
        assert isinstance(job_analysis["key_responsibilities"], list)
        assert isinstance(job_analysis["company_culture"], str)
        assert isinstance(job_analysis["role_level"], str)
        assert isinstance(job_analysis["industry"], str)

        # Validate requirements array structure
        if job_analysis["requirements"]:
            req = job_analysis["requirements"][0]
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
        assert job_analysis["role_level"] in ["junior", "mid", "senior", "lead", "executive"]

        # Optional fields validation
        if "department" in job_analysis:
            assert isinstance(job_analysis["department"], (str, type(None)))
        if "remote_policy" in job_analysis:
            assert isinstance(job_analysis["remote_policy"], (str, type(None)))
        if "salary_range" in job_analysis:
            assert isinstance(job_analysis["salary_range"], (str, type(None)))
        if "benefits" in job_analysis:
            assert isinstance(job_analysis["benefits"], list)
        if "preferred_qualifications" in job_analysis:
            assert isinstance(job_analysis["preferred_qualifications"], list)

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

        # Verify wrapper fields
        assert "job_analysis" in response_data
        assert "analysis_metadata" in response_data
        assert "message" in response_data

        # Get the nested job analysis data
        job_analysis = response_data["job_analysis"]

        assert "company_name" in job_analysis
        assert "job_title" in job_analysis
        assert "location" in job_analysis
        assert "requirements" in job_analysis
        assert "key_responsibilities" in job_analysis
        assert "company_culture" in job_analysis
        assert "role_level" in job_analysis
        assert "industry" in job_analysis

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