"""Endpoints that support human-in-the-loop verification."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Body, Depends

from app.api.deps import get_review_service
from app.models.review import ReviewDecision, ReviewItem
from app.services.validation import ReviewService

router = APIRouter()


@router.get("/pending", response_model=list[ReviewItem])
async def get_pending_reviews(
    user_id: UUID,
    review_service: ReviewService = Depends(get_review_service),
) -> list[ReviewItem]:
    return await review_service.get_pending(str(user_id))


@router.post("/submit")
async def submit_review(
    user_id: UUID,
    decisions: list[ReviewDecision] = Body(...),
    review_service: ReviewService = Depends(get_review_service),
) -> dict[str, str]:
    await review_service.process_decisions(str(user_id), decisions)
    return {"status": "reviews_processed"}
