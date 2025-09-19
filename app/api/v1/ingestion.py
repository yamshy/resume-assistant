"""Endpoints for resume ingestion."""

from __future__ import annotations

import base64
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_ingestion_service
from app.models.profile import UserProfile
from app.models.review import ReviewItem
from app.services.ingestion import IngestionService

router = APIRouter()


from pydantic import BaseModel, Field


class ResumeDocument(BaseModel):
    filename: str | None = None
    content: str = Field(..., description="Base64 encoded resume document")


class IngestionRequest(BaseModel):
    user_id: UUID
    resumes: list[ResumeDocument]


class IngestionResponse(BaseModel):
    profile: UserProfile
    pending_reviews: list[ReviewItem]


class ProfileResponse(BaseModel):
    profile: UserProfile | None


def _decode_resumes(documents: list[ResumeDocument]) -> list[bytes]:
    decoded: list[bytes] = []
    for document in documents:
        try:
            decoded.append(base64.b64decode(document.content))
        except Exception as exc:  # pragma: no cover - validation should prevent
            raise HTTPException(status_code=400, detail="Invalid resume encoding") from exc
    return decoded


@router.post("/", response_model=IngestionResponse)
async def ingest_resumes(
    payload: IngestionRequest,
    service: IngestionService = Depends(get_ingestion_service),
) -> IngestionResponse:
    resumes = _decode_resumes(payload.resumes)
    profile, review_items = await service.ingest_resumes(resumes, str(payload.user_id))
    return IngestionResponse(profile=profile, pending_reviews=review_items)


@router.get("/profile/{user_id}", response_model=ProfileResponse)
async def get_profile(
    user_id: UUID,
    service: IngestionService = Depends(get_ingestion_service),
) -> ProfileResponse:
    profile = await service.load_profile(str(user_id))
    return ProfileResponse(profile=profile)
