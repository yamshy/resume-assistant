"""
Job analysis endpoints for Resume Assistant API.

Handles job posting analysis using the Job Analysis Agent to extract
structured requirements and company information.

Constitutional compliance:
- Thin FastAPI route handlers (no business logic)
- Delegates to Job Analysis Agent for intelligence
- Structured error responses
- Standard REST patterns
"""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from agents.job_analysis_agent import create_job_analysis_agent
from models.job_analysis import JobAnalysis


class JobAnalysisRequest(BaseModel):
    """Request model for job analysis."""

    job_description: str = Field(
        ..., min_length=50, description="Raw job description text to analyze"
    )


class JobAnalysisResponse(BaseModel):
    """Response model for job analysis."""

    job_analysis: JobAnalysis
    analysis_metadata: dict[str, Any]
    message: str


# Create router for job analysis endpoints
router = APIRouter(prefix="/jobs", tags=["jobs"])

# Initialize job analysis agent
job_analysis_agent = create_job_analysis_agent()


@router.post("/analyze", response_model=JobAnalysisResponse)
async def analyze_job_posting(request: JobAnalysisRequest) -> JobAnalysisResponse:
    """
    Analyze a job posting to extract structured requirements.

    Uses the Job Analysis Agent to parse raw job posting text and extract
    company information, job requirements, responsibilities, and other
    structured data needed for resume tailoring.

    Args:
        request: Job analysis request with raw posting text

    Returns:
        JobAnalysisResponse: Structured job analysis results

    Raises:
        HTTPException: If analysis fails or input is invalid
    """
    try:
        # Validate input length
        if len(request.job_description.strip()) < 50:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Job description text must be at least 50 characters long",
            )

        # Analyze job posting using agent
        job_analysis = await job_analysis_agent.run(request.job_description)

        # Prepare metadata about the analysis
        analysis_metadata = {
            "original_text_length": len(request.job_description),
            "requirements_count": len(job_analysis.requirements),
            "required_skills_count": len(
                [req for req in job_analysis.requirements if req.is_required]
            ),
            "preferred_skills_count": len(
                [req for req in job_analysis.requirements if not req.is_required]
            ),
            "responsibilities_count": len(job_analysis.key_responsibilities),
            "analysis_completed_at": job_analysis.analysis_timestamp,
        }

        return JobAnalysisResponse(
            job_analysis=job_analysis,
            analysis_metadata=analysis_metadata,
            message="Job posting analyzed successfully",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Job analysis validation error: {str(e)}",
        ) from e
    except Exception as e:
        # Handle agent failures
        if "Job analysis failed" in str(e):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Unable to analyze job posting: {str(e)}",
            ) from e
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Job analysis service error: {str(e)}",
            ) from e


@router.get("/analyze/health")
async def job_analysis_health() -> dict[str, str]:
    """
    Health check for job analysis service.

    Returns:
        Dict with service status
    """
    return {
        "service": "job_analysis",
        "status": "healthy",
        "agent_loaded": job_analysis_agent is not None,
    }


__all__ = ["router", "JobAnalysisRequest", "JobAnalysisResponse"]
