from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.dependencies import get_resume_service
from resume_core.models import ResumeHistoryItem
from resume_core.services.resume_service import ResumeService

router = APIRouter(tags=["resumes"])


class ResumeHistoryResponse(BaseModel):
    resumes: list[ResumeHistoryItem]
    total: int
    limit: int
    offset: int


@router.get("/resumes/history", response_model=ResumeHistoryResponse)
async def get_resume_history(
    limit: int = Query(10, ge=1, le=100, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    resume_service: ResumeService = Depends(get_resume_service),
) -> ResumeHistoryResponse:
    history, total = await resume_service.get_history(limit=limit, offset=offset)
    return ResumeHistoryResponse(
        resumes=history,
        total=total,
        limit=limit,
        offset=offset,
    )
