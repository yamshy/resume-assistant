from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from resume_core.services.resume_service import ResumeTailoringService

router = APIRouter(tags=["resumes"])
_resume_service = ResumeTailoringService()


class ResumeTailorRequest(BaseModel):
    job_posting: str = Field(..., min_length=10)
    profile_overrides: dict[str, Any] | None = None


@router.post("/resumes/tailor", status_code=status.HTTP_201_CREATED)
async def tailor_resume(request: ResumeTailorRequest) -> dict[str, Any]:
    if not request.job_posting.strip():
        raise HTTPException(status_code=400, detail="Job posting text is required")
    result = await _resume_service.tailor_resume(
        job_posting=request.job_posting,
        profile_overrides=request.profile_overrides,
    )
    return {
        "resume_id": result.resume.resume_id,
        "status": result.status,
        "resume": result.resume.model_dump(),
        "analysis": result.analysis.model_dump(),
        "matching": result.matching.model_dump(),
        "validation": result.validation.model_dump(),
        "recommendation": result.recommendation.model_dump(),
    }


@router.get("/resumes/{resume_id}")
def get_resume(resume_id: UUID) -> dict[str, Any]:
    try:
        result = _resume_service.load_resume(str(resume_id))
    except FileNotFoundError as exc:  # pragma: no cover - error mapping
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "resume_id": result.resume.resume_id,
        "status": result.status,
        "resume": result.resume.model_dump(),
        "analysis": result.analysis.model_dump(),
        "matching": result.matching.model_dump(),
        "validation": result.validation.model_dump(),
        "recommendation": result.recommendation.model_dump(),
    }
