"""
Resume download endpoints for Resume Assistant API.

Handles downloading exported resume files and metadata retrieval
using the storage service.

Constitutional compliance:
- Thin FastAPI route handlers (no business logic)
- Delegates to storage service for file operations
- Structured error responses
- Standard REST patterns
"""

from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel

from services.storage_service import create_storage_service
from utils.validation import sanitize_filename


class DownloadMetadata(BaseModel):
    """Metadata for downloadable resume."""

    exported_at: str
    job_title: str
    company_name: str
    session_id: str
    resume_file: str
    file_path: str
    file_size: int
    optimizations_count: int


class DownloadListResponse(BaseModel):
    """Response model for download list."""

    downloads: list[DownloadMetadata]
    total_count: int
    message: str


# Create router for download endpoints
router = APIRouter(prefix="/resumes", tags=["downloads"])

# Initialize storage service
storage_service = create_storage_service()


@router.get("/{session_id}/download")
async def download_resume(session_id: str) -> FileResponse:
    """
    Download the exported resume file for a session.

    Returns the markdown resume file as a downloadable attachment.
    The session must have been approved and exported.

    Args:
        session_id: Session identifier from tailoring/approval

    Returns:
        FileResponse: Resume file for download

    Raises:
        HTTPException: If session not found or no export available
    """
    try:
        # Load session data to find export path
        session_data = await storage_service.load_session_data(session_id)
        if session_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found"
            )

        # Check for approval decision with export path
        approval_decision = session_data.get("approval_decision")
        if not approval_decision:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume has not been approved for download",
            )

        export_path = approval_decision.get("export_path")
        if not export_path:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No exported resume file found for this session",
            )

        # Verify file exists
        file_path = Path(export_path)
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Resume file no longer exists"
            )

        # Get job info for filename
        pipeline_results = session_data.get("pipeline_results", {})
        job_analysis = pipeline_results.get("job_analysis", {})
        job_title = job_analysis.get("job_title", "Resume")
        company_name = job_analysis.get("company_name", "Unknown")

        # Generate download filename
        download_filename = f"{sanitize_filename(company_name)}_{sanitize_filename(job_title)}_Resume.md"

        return FileResponse(path=file_path, filename=download_filename, media_type="text/markdown")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Download failed: {str(e)}"
        ) from e


@router.get("/{session_id}/download/metadata")
async def get_download_metadata(session_id: str) -> dict[str, Any]:
    """
    Get metadata about downloadable resume for a session.

    Args:
        session_id: Session identifier

    Returns:
        Dict with download metadata

    Raises:
        HTTPException: If session not found or no export available
    """
    try:
        session_data = await storage_service.load_session_data(session_id)
        if session_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found"
            )

        approval_decision = session_data.get("approval_decision")
        if not approval_decision or not approval_decision.get("export_path"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No exported resume available for download",
            )

        # Get pipeline data
        pipeline_results = session_data.get("pipeline_results", {})
        job_analysis = pipeline_results.get("job_analysis", {})
        tailored_resume = pipeline_results.get("tailored_resume", {})

        # Check file stats
        export_path = approval_decision["export_path"]
        file_path = Path(export_path)
        file_size = file_path.stat().st_size if file_path.exists() else 0

        return {
            "session_id": session_id,
            "job_title": job_analysis.get("job_title"),
            "company_name": job_analysis.get("company_name"),
            "export_path": export_path,
            "file_size": file_size,
            "file_exists": file_path.exists(),
            "exported_at": approval_decision.get("decided_at"),
            "optimizations_count": len(tailored_resume.get("content_optimizations", [])),
            "estimated_match_score": tailored_resume.get("estimated_match_score"),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get download metadata: {str(e)}",
        ) from e


__all__ = ["router", "DownloadMetadata", "DownloadListResponse"]
