from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from app.api.deps import get_tailoring_service
from resume_core.models import ApprovalResult, ReviewDecision, TailoringResult
from resume_core.services import (
    JobAnalysisNotFoundError,
    ProfileNotFoundError,
    ResumeNotApprovedError,
    ResumeNotFoundError,
    ResumeTailoringService,
    TailoringPreferences,
    UnsupportedFormatError,
    validate_preferences,
)


class TailorResumeRequest(BaseModel):
    job_description: str = Field(..., min_length=1)
    job_analysis_id: UUID | None = Field(default=None, description="Optional existing analysis ID")
    preferences: dict[str, Any] | None = None


router = APIRouter(tags=["resumes"])


@router.post("/resumes/tailor", response_model=TailoringResult)
async def tailor_resume(
    request: TailorResumeRequest,
    service: ResumeTailoringService = Depends(get_tailoring_service),
) -> TailoringResult:
    try:
        preferences: TailoringPreferences = validate_preferences(request.preferences)
        return await service.tailor_resume(
            job_description=request.job_description,
            job_analysis_id=request.job_analysis_id,
            preferences=preferences,
        )
    except ProfileNotFoundError as exc:  # pragma: no cover - handled by API tests
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except JobAnalysisNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/resumes/{resume_id}/approve", response_model=ApprovalResult)
async def approve_resume(
    resume_id: UUID,
    decision: ReviewDecision,
    service: ResumeTailoringService = Depends(get_tailoring_service),
) -> ApprovalResult:
    try:
        return await service.approve_resume(resume_id, decision)
    except ResumeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/resumes/{resume_id}/download")
async def download_resume(
    resume_id: UUID,
    format: str = "markdown",
    service: ResumeTailoringService = Depends(get_tailoring_service),
) -> Response:
    try:
        content = service.download_resume(resume_id, format)
    except ResumeNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ResumeNotApprovedError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except UnsupportedFormatError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    media_type = "text/markdown" if format == "markdown" else "application/octet-stream"
    return Response(content=content, media_type=media_type)


@router.get("/resumes/history")
async def get_history(
    limit: int = 10,
    offset: int = 0,
    service: ResumeTailoringService = Depends(get_tailoring_service),
) -> dict[str, Any]:
    items, total = service.get_history(limit=limit, offset=offset)
    return {
        "resumes": [item.model_dump(mode="json") for item in items],
        "total": total,
        "limit": limit,
        "offset": offset,
    }

