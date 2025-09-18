"""Contract tests for POST /resumes/{resume_id}/approve endpoint.

This test validates the approval endpoint according to the OpenAPI specification.
The test is designed to FAIL initially as part of TDD approach - the endpoint doesn't exist yet.
"""

import uuid
from typing import Any, Dict

import pytest
from httpx import AsyncClient


class TestResumeApprovalEndpoint:
    """Contract tests for resume approval endpoint."""

    async def test_approve_resume_success(self, async_client: AsyncClient) -> None:
        """Test successful resume approval with valid ReviewDecision.

        This test MUST FAIL initially - the endpoint doesn't exist yet.
        Tests the happy path where a valid resume ID and decision are provided.
        """
        # Arrange
        resume_id = str(uuid.uuid4())
        review_decision = {
            "decision": "approved",
            "feedback": "Excellent tailoring, all sections optimized well",
            "requested_modifications": [],
            "approved_sections": ["summary", "experience", "skills"],
            "rejected_sections": []
        }

        # Act
        response = await async_client.post(
            f"/api/v1/resumes/{resume_id}/approve",
            json=review_decision
        )

        # Assert
        assert response.status_code == 200

        # Validate ApprovalResult schema compliance
        response_data = response.json()
        assert "status" in response_data
        assert response_data["status"] in ["approved", "rejected", "needs_revision"]
        assert "revision_needed" in response_data
        assert isinstance(response_data["revision_needed"], bool)
        assert "next_steps" in response_data
        assert isinstance(response_data["next_steps"], list)

        # For approved decision, expect specific response
        assert response_data["status"] == "approved"
        assert response_data["revision_needed"] is False

        # final_resume_url should be present for approved resumes
        if "final_resume_url" in response_data:
            assert response_data["final_resume_url"] is not None

    async def test_approve_resume_needs_revision(self, async_client: AsyncClient) -> None:
        """Test resume approval with needs_revision decision."""
        # Arrange
        resume_id = str(uuid.uuid4())
        review_decision = {
            "decision": "needs_revision",
            "feedback": "Good start but experience section needs improvement",
            "requested_modifications": [
                "Add more quantified achievements in experience section",
                "Improve skills section keyword optimization"
            ],
            "approved_sections": ["summary"],
            "rejected_sections": ["experience", "skills"]
        }

        # Act
        response = await async_client.post(
            f"/api/v1/resumes/{resume_id}/approve",
            json=review_decision
        )

        # Assert
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["status"] == "needs_revision"
        assert response_data["revision_needed"] is True
        assert len(response_data["next_steps"]) > 0

    async def test_approve_resume_rejected(self, async_client: AsyncClient) -> None:
        """Test resume approval with rejected decision."""
        # Arrange
        resume_id = str(uuid.uuid4())
        review_decision = {
            "decision": "rejected",
            "feedback": "Resume doesn't match job requirements well enough",
            "requested_modifications": [],
            "approved_sections": [],
            "rejected_sections": ["summary", "experience", "skills", "education"]
        }

        # Act
        response = await async_client.post(
            f"/api/v1/resumes/{resume_id}/approve",
            json=review_decision
        )

        # Assert
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["status"] == "rejected"
        assert response_data["revision_needed"] is True
        assert "final_resume_url" not in response_data or response_data["final_resume_url"] is None

    async def test_approve_resume_not_found(self, async_client: AsyncClient) -> None:
        """Test approval of non-existent resume returns 404."""
        # Arrange
        non_existent_resume_id = str(uuid.uuid4())
        review_decision = {
            "decision": "approved",
            "feedback": "Looks good",
        }

        # Act
        response = await async_client.post(
            f"/api/v1/resumes/{non_existent_resume_id}/approve",
            json=review_decision
        )

        # Assert
        assert response.status_code == 404

        # Validate ErrorResponse schema (or default FastAPI 404)
        response_data = response.json()
        # Accept either our custom ErrorResponse format or FastAPI default
        assert ("error" in response_data and "timestamp" in response_data) or "detail" in response_data

    async def test_approve_resume_invalid_uuid(self, async_client: AsyncClient) -> None:
        """Test approval with invalid UUID format."""
        # Arrange
        invalid_resume_id = "not-a-valid-uuid"
        review_decision = {
            "decision": "approved"
        }

        # Act
        response = await async_client.post(
            f"/api/v1/resumes/{invalid_resume_id}/approve",
            json=review_decision
        )

        # Assert
        # Should return 422 for invalid UUID or 404 if UUID validation is handled at route level
        assert response.status_code in [404, 422]

    async def test_approve_resume_missing_required_fields(self, async_client: AsyncClient) -> None:
        """Test approval with missing required fields in ReviewDecision."""
        # Arrange
        resume_id = str(uuid.uuid4())
        invalid_review_decision = {
            "feedback": "Missing required decision field"
            # Missing required 'decision' field
        }

        # Act
        response = await async_client.post(
            f"/api/v1/resumes/{resume_id}/approve",
            json=invalid_review_decision
        )

        # Assert
        assert response.status_code == 422  # Validation error

    async def test_approve_resume_invalid_decision_value(self, async_client: AsyncClient) -> None:
        """Test approval with invalid decision value."""
        # Arrange
        resume_id = str(uuid.uuid4())
        invalid_review_decision = {
            "decision": "invalid_decision_value",  # Not in enum [pending, approved, rejected, needs_revision]
            "feedback": "Invalid decision value"
        }

        # Act
        response = await async_client.post(
            f"/api/v1/resumes/{resume_id}/approve",
            json=invalid_review_decision
        )

        # Assert
        assert response.status_code == 422  # Validation error for invalid enum value

    @pytest.mark.parametrize("decision,expected_revision", [
        ("approved", False),
        ("rejected", True),
        ("needs_revision", True),
    ])
    async def test_approve_resume_decision_revision_mapping(
        self,
        async_client: AsyncClient,
        decision: str,
        expected_revision: bool
    ) -> None:
        """Test that revision_needed field matches decision appropriately."""
        # Arrange
        resume_id = str(uuid.uuid4())
        review_decision = {
            "decision": decision,
            "feedback": f"Test {decision} decision"
        }

        # Act
        response = await async_client.post(
            f"/api/v1/resumes/{resume_id}/approve",
            json=review_decision
        )

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["revision_needed"] == expected_revision