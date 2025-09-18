"""
Resume history endpoints for Resume Assistant API.

Handles listing and managing historical resume exports and sessions
using the storage service.

Constitutional compliance:
- Thin FastAPI route handlers (no business logic)
- Delegates to storage service for data operations
- Structured error responses
- Standard REST patterns
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from services.storage_service import create_storage_service


class HistoryItem(BaseModel):
    """Single resume history item."""

    exported_at: str
    job_title: str
    company_name: str
    session_id: str | None = None
    resume_file: str
    file_path: str
    file_size: int
    optimizations_count: int


class HistoryResponse(BaseModel):
    """Response model for resume history."""

    history: list[HistoryItem]
    total_count: int
    page: int
    page_size: int
    has_more: bool
    message: str


# Create router for history endpoints
router = APIRouter(prefix="/resumes", tags=["history"])

# Initialize storage service
storage_service = create_storage_service()


@router.get("/history", response_model=HistoryResponse)
async def get_resume_history(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    job_title: str | None = Query(None, description="Filter by job title"),
    company_name: str | None = Query(None, description="Filter by company name"),
) -> HistoryResponse:
    """
    Get paginated history of exported resumes.

    Returns a paginated list of all exported resumes with metadata,
    sorted by export date (newest first).

    Args:
        page: Page number (1-based)
        page_size: Number of items per page
        job_title: Optional filter by job title
        company_name: Optional filter by company name

    Returns:
        HistoryResponse: Paginated history of exported resumes

    Raises:
        HTTPException: If history retrieval fails
    """
    try:
        # Get all exports from storage service
        all_exports = await storage_service.list_exports()

        # Apply filters if provided
        filtered_exports = all_exports
        if job_title:
            filtered_exports = [
                exp
                for exp in filtered_exports
                if job_title.lower() in exp.get("job_title", "").lower()
            ]

        if company_name:
            filtered_exports = [
                exp
                for exp in filtered_exports
                if company_name.lower() in exp.get("company_name", "").lower()
            ]

        # Calculate pagination
        total_count = len(filtered_exports)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_exports = filtered_exports[start_idx:end_idx]

        # Convert to response format
        history_items = []
        for export in page_exports:
            history_items.append(
                HistoryItem(
                    exported_at=export.get("exported_at", ""),
                    job_title=export.get("job_title", "Unknown"),
                    company_name=export.get("company_name", "Unknown"),
                    session_id=export.get("session_id"),
                    resume_file=export.get("resume_file", ""),
                    file_path=export.get("file_path", ""),
                    file_size=export.get("file_size", 0),
                    optimizations_count=export.get("optimizations_count", 0),
                )
            )

        has_more = end_idx < total_count

        return HistoryResponse(
            history=history_items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            has_more=has_more,
            message=f"Retrieved {len(history_items)} resume(s) from history",
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve resume history: {str(e)}",
        ) from e


@router.get("/history/stats")
async def get_history_stats() -> dict[str, Any]:
    """
    Get statistics about resume export history.

    Returns:
        Dict with history statistics

    Raises:
        HTTPException: If stats retrieval fails
    """
    try:
        all_exports = await storage_service.list_exports()

        # Calculate statistics
        total_resumes = len(all_exports)
        companies = {exp.get("company_name", "").strip() for exp in all_exports}
        companies.discard("")  # Remove empty company names

        # Find most recent export
        most_recent = None
        if all_exports:
            most_recent = all_exports[0].get("exported_at")  # Already sorted by date

        # Calculate total file size
        total_size = sum(exp.get("file_size", 0) for exp in all_exports)

        # Find month with most exports
        monthly_counts = {}
        for exp in all_exports:
            try:
                export_date = exp.get("exported_at", "")
                if export_date:
                    # Extract YYYYMM from timestamp format
                    month_key = export_date[:6]  # Assumes YYYYMMDD_HHMMSS format
                    monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
            except Exception:
                continue

        busiest_month = max(monthly_counts.items(), key=lambda x: x[1]) if monthly_counts else None

        return {
            "total_resumes": total_resumes,
            "unique_companies": len(companies),
            "companies_list": sorted(companies),
            "most_recent_export": most_recent,
            "total_file_size_bytes": total_size,
            "busiest_month": {
                "month": busiest_month[0] if busiest_month else None,
                "count": busiest_month[1] if busiest_month else 0,
            },
            "stats_generated_at": datetime.now().isoformat(),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate history stats: {str(e)}",
        ) from e


@router.delete("/history/{resume_file}")
async def delete_resume_from_history(resume_file: str) -> dict[str, str]:
    """
    Delete a specific resume file from history.

    Args:
        resume_file: Name of the resume file to delete

    Returns:
        Dict with deletion confirmation

    Raises:
        HTTPException: If deletion fails or file not found
    """
    try:
        # This would need to be implemented in storage service
        # For now, return not implemented
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Resume deletion not yet implemented",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete resume: {str(e)}",
        ) from e


__all__ = ["router", "HistoryItem", "HistoryResponse"]
