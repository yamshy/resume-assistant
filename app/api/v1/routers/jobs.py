from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_tailoring_service
from resume_core.models import JobAnalysis
from resume_core.services import ResumeTailoringService


class JobAnalysisRequest(BaseModel):
    job_description: str = Field(..., description="Raw job posting text")


router = APIRouter(tags=["jobs"])


@router.post("/jobs/analyze", response_model=JobAnalysis)
async def analyze_job(
    request: JobAnalysisRequest,
    service: ResumeTailoringService = Depends(get_tailoring_service),
) -> JobAnalysis:
    description = request.job_description.strip()
    if not description:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job description is required")
    return await service.analyze_job(description)

