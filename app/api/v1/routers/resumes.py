from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api.dependencies import get_resume_service
from resume_core.models.resume import TailoringResult
from resume_core.services.resume_service import ResumeService

router = APIRouter(tags=["resumes"])


class TailorPreferences(BaseModel):
    emphasis_areas: list[str] = Field(default_factory=list)
    excluded_sections: list[str] = Field(default_factory=list)


class TailorResumeRequest(BaseModel):
    job_description: str = Field(description="Job posting text to tailor against")
    preferences: TailorPreferences | None = None


@router.post(
    "/resumes/tailor",
    response_model=TailoringResult,
    status_code=status.HTTP_200_OK,
)
async def tailor_resume(
    request: TailorResumeRequest,
    resume_service: ResumeService = Depends(get_resume_service),
) -> TailoringResult:
    description = request.job_description.strip()
    if not description:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "invalid_job_description"},
        )

    preferences = (
        request.preferences.model_dump(mode="json", exclude_none=True)
        if request.preferences
        else None
    )

    try:
        return await resume_service.tailor_resume(description, preferences=preferences)
    except FileNotFoundError:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "profile_not_found"},
        )
