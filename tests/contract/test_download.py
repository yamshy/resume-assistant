"""Contract tests for GET /resumes/{resume_id}/download endpoint.

This is a TDD contract test that MUST FAIL initially as the endpoint doesn't exist yet.
Tests download endpoint according to OpenAPI spec at specs/001-resume-tailoring-feature/contracts/api_spec.yaml
"""

import uuid
from typing import Dict, Any

import pytest
from httpx import AsyncClient


class TestDownloadEndpoint:
    """Test suite for GET /resumes/{resume_id}/download endpoint contract."""

    @pytest.mark.asyncio
    async def test_download_resume_markdown_format(self, async_client: AsyncClient) -> None:
        """Test downloading resume in markdown format."""
        resume_id = str(uuid.uuid4())

        response = await async_client.get(
            f"/resumes/{resume_id}/download",
            params={"format": "markdown"}
        )

        # This test MUST fail initially - endpoint doesn't exist
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/markdown; charset=utf-8"
        # Should return markdown content
        content = response.text
        assert isinstance(content, str)
        assert len(content) > 0

    @pytest.mark.asyncio
    async def test_download_resume_pdf_format(self, async_client: AsyncClient) -> None:
        """Test downloading resume in PDF format."""
        resume_id = str(uuid.uuid4())

        response = await async_client.get(
            f"/resumes/{resume_id}/download",
            params={"format": "pdf"}
        )

        # This test MUST fail initially - endpoint doesn't exist
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        # Should return binary PDF content
        content = response.content
        assert isinstance(content, bytes)
        assert len(content) > 0

    @pytest.mark.asyncio
    async def test_download_resume_docx_format(self, async_client: AsyncClient) -> None:
        """Test downloading resume in DOCX format."""
        resume_id = str(uuid.uuid4())

        response = await async_client.get(
            f"/resumes/{resume_id}/download",
            params={"format": "docx"}
        )

        # This test MUST fail initially - endpoint doesn't exist
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        # Should return binary DOCX content
        content = response.content
        assert isinstance(content, bytes)
        assert len(content) > 0

    @pytest.mark.asyncio
    async def test_download_resume_default_format(self, async_client: AsyncClient) -> None:
        """Test downloading resume with default format (markdown)."""
        resume_id = str(uuid.uuid4())

        response = await async_client.get(f"/resumes/{resume_id}/download")

        # This test MUST fail initially - endpoint doesn't exist
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/markdown; charset=utf-8"
        # Should return markdown content as default
        content = response.text
        assert isinstance(content, str)
        assert len(content) > 0

    @pytest.mark.asyncio
    async def test_download_resume_invalid_format(self, async_client: AsyncClient) -> None:
        """Test downloading resume with invalid format parameter."""
        resume_id = str(uuid.uuid4())

        response = await async_client.get(
            f"/resumes/{resume_id}/download",
            params={"format": "invalid"}
        )

        # Should return 422 for invalid enum value
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_download_resume_not_found(self, async_client: AsyncClient) -> None:
        """Test downloading non-existent resume returns 404."""
        resume_id = str(uuid.uuid4())

        response = await async_client.get(
            f"/resumes/{resume_id}/download",
            params={"format": "markdown"}
        )

        # Should return 404 for non-existent resume
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_download_resume_invalid_uuid(self, async_client: AsyncClient) -> None:
        """Test downloading resume with invalid UUID format."""
        invalid_resume_id = "not-a-uuid"

        response = await async_client.get(
            f"/resumes/{invalid_resume_id}/download",
            params={"format": "markdown"}
        )

        # Should return 422 for invalid UUID format
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_download_resume_all_formats_same_content(self, async_client: AsyncClient) -> None:
        """Test that all format downloads work for the same resume ID."""
        resume_id = str(uuid.uuid4())

        # Test all three formats for the same resume
        formats_and_types = [
            ("markdown", "text/markdown; charset=utf-8"),
            ("pdf", "application/pdf"),
            ("docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        ]

        for format_param, expected_content_type in formats_and_types:
            response = await async_client.get(
                f"/resumes/{resume_id}/download",
                params={"format": format_param}
            )

            # This test MUST fail initially - endpoint doesn't exist
            assert response.status_code == 200
            assert response.headers["content-type"] == expected_content_type

            # Verify content is returned
            if format_param == "markdown":
                assert isinstance(response.text, str)
                assert len(response.text) > 0
            else:
                assert isinstance(response.content, bytes)
                assert len(response.content) > 0