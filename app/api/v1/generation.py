"""Endpoints for tailored resume generation."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_generation_service
from app.services.generation import GenerationService

router = APIRouter()


class GenerationRequest(BaseModel):
    user_id: UUID
    job_posting: str = Field(..., min_length=10)


class GenerationResponse(BaseModel):
    resume: dict
    confidence: float
    needs_review: bool


@router.post("/resume", response_model=GenerationResponse)
async def generate_resume(
    payload: GenerationRequest,
    service: GenerationService = Depends(get_generation_service),
) -> GenerationResponse:
    if not payload.job_posting.strip():
        raise HTTPException(status_code=400, detail="Job posting cannot be empty")
    result = await service.generate_resume(payload.job_posting, str(payload.user_id))
    return GenerationResponse(**result)
