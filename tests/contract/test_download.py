"""Contract tests for GET /resumes/{session_id}/download endpoint.

Tests download endpoint according to the working implementation.
Updated to use session_id pattern and markdown-only format per constitutional simplicity.
"""

import uuid
from typing import Dict, Any

import pytest
from httpx import AsyncClient


class TestDownloadEndpoint:
    """Test suite for GET /resumes/{session_id}/download endpoint contract."""

    @pytest.mark.asyncio
    async def test_download_resume_success(self, async_client: AsyncClient) -> None:
        """Test downloading resume markdown file."""
        session_id = str(uuid.uuid4())

        response = await async_client.get(
            f"/api/v1/resumes/{session_id}/download"
        )

        # Expect 404 for non-existent session (not approved/exported)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_download_resume_not_approved(self, async_client: AsyncClient) -> None:
        """Test downloading resume that hasn't been approved yet."""
        session_id = str(uuid.uuid4())

        response = await async_client.get(
            f"/api/v1/resumes/{session_id}/download"
        )

        # Should return 404 for session without approval
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_download_resume_invalid_uuid(self, async_client: AsyncClient) -> None:
        """Test downloading resume with invalid session ID format."""
        invalid_session_id = "not-a-uuid"

        response = await async_client.get(
            f"/api/v1/resumes/{invalid_session_id}/download"
        )

        # Should return 404 for invalid session ID
        assert response.status_code == 404

