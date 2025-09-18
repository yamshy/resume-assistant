from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api.dependencies import get_resume_service
from resume_core.models.job_analysis import JobAnalysis
from resume_core.services.resume_service import ResumeService

router = APIRouter(tags=["jobs"])


class JobAnalysisRequest(BaseModel):
    job_description: str = Field(description="Raw job posting text to analyze")


@router.post("/jobs/analyze", response_model=JobAnalysis, status_code=status.HTTP_200_OK)
async def analyze_job(
    request: JobAnalysisRequest,
    resume_service: ResumeService = Depends(get_resume_service),
) -> JobAnalysis:
    description = request.job_description.strip()
    if not description:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "invalid_job_description"},
        )

    analysis = await resume_service.job_analysis_agent.analyze(description)
    return analysis
