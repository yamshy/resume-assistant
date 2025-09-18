"""
Resume tailoring endpoints for Resume Assistant API.

Handles the complete resume tailoring workflow using the 5-agent pipeline
and storage services for session management.

Constitutional compliance:
- Thin FastAPI route handlers (no business logic)
- Delegates to ResumeTailoringService for agent orchestration
- Structured error responses
- Standard REST patterns
"""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from models.approval import ApprovalRequest
from models.job_analysis import JobAnalysis
from models.matching import MatchingResult
from models.profile import UserProfile
from models.resume_optimization import TailoredResume
from models.validation import ValidationResult
from services.profile_service import create_profile_service
from services.storage_service import create_storage_service
from services.tailoring_service import create_resume_tailoring_service


class ResumeTailoringRequest(BaseModel):
    """Request model for resume tailoring."""

    job_posting_text: str = Field(
        ..., min_length=50, description="Raw job posting text to tailor resume against"
    )
    use_stored_profile: bool = Field(
        True, description="Whether to use stored profile or require profile in request"
    )
    profile: UserProfile = Field(
        None, description="User profile data (required if use_stored_profile is False)"
    )


class ResumeTailoringResponse(BaseModel):
    """Response model for resume tailoring."""

    session_id: str
    processing_time_seconds: float
    job_analysis: JobAnalysis
    matching_result: MatchingResult
    tailored_resume: TailoredResume
    validation_result: ValidationResult
    approval_workflow: ApprovalRequest
    final_status: dict[str, Any]
    message: str


# Create router for resume endpoints
router = APIRouter(prefix="/resumes", tags=["resumes"])

# Initialize services
tailoring_service = create_resume_tailoring_service()
profile_service = create_profile_service()
storage_service = create_storage_service()


@router.post("/tailor", response_model=ResumeTailoringResponse)
async def tailor_resume(request: ResumeTailoringRequest) -> ResumeTailoringResponse:
    """
    Generate a tailored resume using the complete 5-agent pipeline.

    Orchestrates the full resume tailoring workflow:
    1. Job Analysis Agent → Extract job requirements
    2. Profile Matching Agent → Match profile against job
    3. Resume Generation Agent → Create tailored content
    4. Validation Agent → Verify accuracy
    5. Human Interface Agent → Determine approval workflow

    Args:
        request: Resume tailoring request with job posting and profile data

    Returns:
        ResumeTailoringResponse: Complete pipeline results

    Raises:
        HTTPException: If tailoring fails or inputs are invalid
    """
    try:
        # Validate job posting length
        if len(request.job_posting_text.strip()) < 50:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Job posting text must be at least 50 characters long",
            )

        # Get user profile
        if request.use_stored_profile:
            user_profile = await profile_service.load_profile()
            if user_profile is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="No stored profile found. Please create a profile first or provide profile data in request.",
                )
        else:
            if request.profile is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Profile data is required when use_stored_profile is False",
                )
            user_profile = request.profile

        # Execute complete tailoring pipeline
        pipeline_results = await tailoring_service.tailor_resume(
            user_profile=user_profile, job_posting_text=request.job_posting_text
        )

        # Save session data for later retrieval
        await storage_service.save_session_data(
            session_id=pipeline_results["session_id"], pipeline_data=pipeline_results
        )

        # Extract pipeline components for response
        pipeline_data = pipeline_results["pipeline_results"]

        return ResumeTailoringResponse(
            session_id=pipeline_results["session_id"],
            processing_time_seconds=pipeline_results["processing_time_seconds"],
            job_analysis=pipeline_data["job_analysis"],
            matching_result=pipeline_data["matching_result"],
            tailored_resume=pipeline_data["tailored_resume"],
            validation_result=pipeline_data["validation_result"],
            approval_workflow=pipeline_data["approval_workflow"],
            final_status=pipeline_results["final_status"],
            message="Resume tailored successfully",
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Input validation error: {str(e)}",
        ) from e
    except Exception as e:
        # Handle pipeline failures
        if "Resume tailoring pipeline failed" in str(e):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Tailoring failed: {str(e)}",
            ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Resume tailoring service error: {str(e)}",
            ) from e


@router.get("/{session_id}")
async def get_tailoring_session(session_id: str) -> dict[str, Any]:
    """
    Retrieve results from a previous tailoring session.

    Args:
        session_id: Session identifier from tailoring request

    Returns:
        Dict with session data

    Raises:
        HTTPException: If session not found
    """
    try:
        session_data = await storage_service.load_session_data(session_id)

        if session_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Session {session_id} not found"
            )

        return session_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load session: {str(e)}",
        ) from e


@router.get("/tailor/health")
async def tailoring_health() -> dict[str, Any]:
    """
    Health check for resume tailoring service.

    Returns:
        Dict with service status and agent health
    """
    try:
        status_info = await tailoring_service.get_pipeline_status("health-check")
        return {"service": "resume_tailoring", "status": "healthy", "pipeline_status": status_info}
    except Exception as e:
        return {"service": "resume_tailoring", "status": "unhealthy", "error": str(e)}


__all__ = ["router", "ResumeTailoringRequest", "ResumeTailoringResponse"]
