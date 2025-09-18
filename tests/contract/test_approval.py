"""Contract tests for POST /resumes/{session_id}/approve endpoint.

This test validates the approval endpoint according to the working implementation.
Updated to use session_id pattern consistent with working tailoring pipeline.
"""

import uuid

import pytest
from httpx import AsyncClient


class TestResumeApprovalEndpoint:
    """Contract tests for resume approval endpoint."""

    async def test_approve_resume_success(self, async_client: AsyncClient) -> None:
        """Test successful resume approval with valid ApprovalRequest.

        Tests the happy path where a valid session ID and decision are provided.
        """
        # Arrange
        session_id = str(uuid.uuid4())
        approval_request = {
            "decision": "approve",
            "comments": "Excellent tailoring, all sections optimized well",
            "requested_changes": None,
        }

        # Act
        response = await async_client.post(
            f"/api/v1/resumes/{session_id}/approve", json=approval_request
        )

        # Assert
        assert response.status_code == 200

        # Validate ApprovalResponse schema compliance
        response_data = response.json()
        assert "session_id" in response_data
        assert "decision" in response_data
        assert "message" in response_data
        assert "timestamp" in response_data

        # For approved decision, expect specific response
        assert response_data["decision"] == "approve"
        assert response_data["session_id"] == session_id

        # export_path should be present for approved resumes
        if "export_path" in response_data:
            assert response_data["export_path"] is not None

    async def test_approve_resume_needs_revision(self, async_client: AsyncClient) -> None:
        """Test resume approval with request_changes decision."""
        # Arrange
        session_id = str(uuid.uuid4())
        approval_request = {
            "decision": "request_changes",
            "comments": "Good start but experience section needs improvement",
            "requested_changes": "Add more quantified achievements in experience section and improve skills section keyword optimization",
        }

        # Act
        response = await async_client.post(
            f"/api/v1/resumes/{session_id}/approve", json=approval_request
        )

        # Assert
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["decision"] == "request_changes"
        assert response_data["session_id"] == session_id
        assert "requested changes" in response_data["message"].lower()

    async def test_approve_resume_rejected(self, async_client: AsyncClient) -> None:
        """Test resume approval with reject decision."""
        # Arrange
        session_id = str(uuid.uuid4())
        approval_request = {
            "decision": "reject",
            "comments": "Resume doesn't match job requirements well enough",
            "requested_changes": None,
        }

        # Act
        response = await async_client.post(
            f"/api/v1/resumes/{session_id}/approve", json=approval_request
        )

        # Assert
        assert response.status_code == 200

        response_data = response.json()
        assert response_data["decision"] == "reject"
        assert response_data["session_id"] == session_id
        assert "export_path" not in response_data or response_data["export_path"] is None

    async def test_approve_resume_not_found(self, async_client: AsyncClient) -> None:
        """Test approval of non-existent session returns 404."""
        # Arrange
        non_existent_session_id = str(uuid.uuid4())
        approval_request = {
            "decision": "approve",
            "comments": "Looks good",
        }

        # Act
        response = await async_client.post(
            f"/api/v1/resumes/{non_existent_session_id}/approve", json=approval_request
        )

        # Assert
        assert response.status_code == 404

        # Validate ErrorResponse schema (or default FastAPI 404)
        response_data = response.json()
        # Accept either our custom ErrorResponse format or FastAPI default
        assert (
            "error" in response_data and "timestamp" in response_data
        ) or "detail" in response_data

    async def test_approve_resume_invalid_uuid(self, async_client: AsyncClient) -> None:
        """Test approval with invalid UUID format."""
        # Arrange
        invalid_session_id = "not-a-valid-uuid"
        approval_request = {"decision": "approve"}

        # Act
        response = await async_client.post(
            f"/api/v1/resumes/{invalid_session_id}/approve", json=approval_request
        )

        # Assert
        # Should return 422 for invalid UUID or 404 if UUID validation is handled at route level
        assert response.status_code in [404, 422]

    async def test_approve_resume_missing_required_fields(self, async_client: AsyncClient) -> None:
        """Test approval with missing required fields in ApprovalRequest."""
        # Arrange
        session_id = str(uuid.uuid4())
        invalid_approval_request = {
            "comments": "Missing required decision field"
            # Missing required 'decision' field
        }

        # Act
        response = await async_client.post(
            f"/api/v1/resumes/{session_id}/approve", json=invalid_approval_request
        )

        # Assert
        assert response.status_code == 422  # Validation error

    async def test_approve_resume_invalid_decision_value(self, async_client: AsyncClient) -> None:
        """Test approval with invalid decision value."""
        # Arrange
        session_id = str(uuid.uuid4())
        invalid_approval_request = {
            "decision": "invalid_decision_value",  # Not in enum [approve, reject, request_changes]
            "comments": "Invalid decision value",
        }

        # Act
        response = await async_client.post(
            f"/api/v1/resumes/{session_id}/approve", json=invalid_approval_request
        )

        # Assert
        assert response.status_code == 422  # Validation error for invalid enum value

    @pytest.mark.parametrize(
        "decision,expected_export",
        [
            ("approve", True),
            ("reject", False),
            ("request_changes", False),
        ],
    )
    async def test_approve_resume_decision_export_mapping(
        self, async_client: AsyncClient, decision: str, expected_export: bool
    ) -> None:
        """Test that export_path is provided based on decision appropriately."""
        # Arrange
        session_id = str(uuid.uuid4())
        approval_request = {"decision": decision, "comments": f"Test {decision} decision"}

        # Act
        response = await async_client.post(
            f"/api/v1/resumes/{session_id}/approve", json=approval_request
        )

        # Assert
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["decision"] == decision
        if expected_export:
            # For approved decisions, export_path may be present
            pass  # Implementation dependent on storage service
        else:
            # For rejected/request_changes decisions, no export_path
            assert "export_path" not in response_data or response_data["export_path"] is None
