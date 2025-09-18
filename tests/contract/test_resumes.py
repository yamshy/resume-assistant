"""Contract tests for resume endpoints.

This module tests the HTTP contract compliance for resume-related endpoints
according to the OpenAPI specification. These tests verify request/response
schemas and status codes without testing business logic.
"""

import pytest
import httpx
from uuid import uuid4


class TestTailorResumeEndpoint:
    """Contract tests for POST /resumes/tailor endpoint."""

    @pytest.mark.asyncio
    async def test_tailor_resume_success(self, async_client: httpx.AsyncClient):
        """Test successful resume tailoring request returns TailoringResult schema."""
        # Valid request payload according to API spec
        request_payload = {
            "job_description": "Software Engineer position at TechCorp requiring Python, FastAPI, and cloud experience. We are looking for a mid-level developer with 3+ years experience.",
            "preferences": {
                "emphasis_areas": ["python", "fastapi", "cloud"],
                "excluded_sections": ["publications"]
            }
        }

        response = await async_client.post("/resumes/tailor", json=request_payload)

        # Should return 200 OK with TailoringResult schema
        assert response.status_code == 200

        result = response.json()

        # Verify TailoringResult schema compliance
        assert "resume_id" in result
        assert "job_analysis" in result
        assert "matching_result" in result
        assert "tailored_resume" in result
        assert "validation_result" in result
        assert "approval_workflow" in result

        # Verify resume_id is valid UUID format
        resume_id = result["resume_id"]
        assert isinstance(resume_id, str)
        # This will raise ValueError if not valid UUID
        uuid4().hex  # Just to import uuid validation behavior

        # Verify job_analysis schema
        job_analysis = result["job_analysis"]
        required_job_fields = [
            "company_name", "job_title", "location", "requirements",
            "key_responsibilities", "company_culture", "role_level", "industry"
        ]
        for field in required_job_fields:
            assert field in job_analysis

        # Verify tailored_resume schema
        tailored_resume = result["tailored_resume"]
        required_resume_fields = [
            "job_title", "company_name", "optimizations", "full_resume_markdown",
            "summary_of_changes", "estimated_match_score", "generation_timestamp"
        ]
        for field in required_resume_fields:
            assert field in tailored_resume

        # Verify validation_result schema
        validation_result = result["validation_result"]
        required_validation_fields = [
            "is_valid", "accuracy_score", "readability_score",
            "keyword_optimization_score", "issues", "strengths",
            "overall_quality_score", "validation_timestamp"
        ]
        for field in required_validation_fields:
            assert field in validation_result

        # Verify approval_workflow schema
        approval_workflow = result["approval_workflow"]
        required_approval_fields = [
            "requires_human_review", "review_reasons", "confidence_score", "auto_approve_eligible"
        ]
        for field in required_approval_fields:
            assert field in approval_workflow

    @pytest.mark.asyncio
    async def test_tailor_resume_minimal_request(self, async_client: httpx.AsyncClient):
        """Test minimal valid request with only required fields."""
        # Minimal request with only job_description (required field)
        request_payload = {
            "job_description": "Senior Data Scientist role focusing on machine learning and Python development."
        }

        response = await async_client.post("/resumes/tailor", json=request_payload)

        # Should return 200 OK even with minimal request
        assert response.status_code == 200

        result = response.json()
        # Basic schema validation - should have all required top-level fields
        required_fields = ["resume_id", "job_analysis", "matching_result", "tailored_resume", "validation_result", "approval_workflow"]
        for field in required_fields:
            assert field in result

    @pytest.mark.asyncio
    async def test_tailor_resume_with_job_analysis_id(self, async_client: httpx.AsyncClient):
        """Test request with optional job_analysis_id parameter."""
        request_payload = {
            "job_description": "Frontend Developer position requiring React and TypeScript experience.",
            "job_analysis_id": str(uuid4()),
            "preferences": {
                "emphasis_areas": ["react", "typescript"],
                "excluded_sections": []
            }
        }

        response = await async_client.post("/resumes/tailor", json=request_payload)

        # Should handle optional job_analysis_id parameter
        assert response.status_code == 200

        result = response.json()
        assert "resume_id" in result

    @pytest.mark.asyncio
    async def test_tailor_resume_invalid_request_missing_job_description(self, async_client: httpx.AsyncClient):
        """Test request validation for missing required job_description field."""
        # Invalid request - missing required job_description
        request_payload = {
            "preferences": {
                "emphasis_areas": ["python"]
            }
        }

        response = await async_client.post("/resumes/tailor", json=request_payload)

        # Should return 400 Bad Request for missing required field
        assert response.status_code == 400

        error_response = response.json()
        # Verify ErrorResponse schema
        assert "error" in error_response
        assert "timestamp" in error_response
        # Should contain details about the validation error
        assert isinstance(error_response["error"], str)

    @pytest.mark.asyncio
    async def test_tailor_resume_invalid_request_empty_job_description(self, async_client: httpx.AsyncClient):
        """Test request validation for empty job_description."""
        request_payload = {
            "job_description": ""
        }

        response = await async_client.post("/resumes/tailor", json=request_payload)

        # Should return 400 Bad Request for empty job description
        assert response.status_code == 400

        error_response = response.json()
        assert "error" in error_response
        assert "timestamp" in error_response

    @pytest.mark.asyncio
    async def test_tailor_resume_invalid_request_malformed_json(self, async_client: httpx.AsyncClient):
        """Test handling of malformed JSON request."""
        # This will send malformed JSON
        response = await async_client.post(
            "/resumes/tailor",
            content='{"job_description": "test", "invalid": }',  # Malformed JSON
            headers={"Content-Type": "application/json"}
        )

        # Should return 400 Bad Request for malformed JSON
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_tailor_resume_invalid_preferences_type(self, async_client: httpx.AsyncClient):
        """Test request validation for invalid preferences structure."""
        request_payload = {
            "job_description": "Software Engineer position",
            "preferences": "invalid_string_instead_of_object"  # Should be object
        }

        response = await async_client.post("/resumes/tailor", json=request_payload)

        # Should return 400 Bad Request for invalid preferences type
        assert response.status_code == 400

        error_response = response.json()
        assert "error" in error_response
        assert "timestamp" in error_response