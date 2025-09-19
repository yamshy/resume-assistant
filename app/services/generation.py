"""Service responsible for generating tailored resumes."""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from app.config import get_settings
from app.models.profile import UserProfile
from app.models.review import ReviewItem
from app.models.resume import ValidationIssue
from app.services.cache import SemanticCache
from app.services.repository import ProfileRepository
from app.services.validation import ReviewService

from app.agents.generator import ResumeGenerator
from app.agents.validator import ClaimValidator


class GenerationService:
    def __init__(
        self,
        profile_repository: ProfileRepository,
        review_service: ReviewService,
    ) -> None:
        self.profile_repository = profile_repository
        self.review_service = review_service
        self.generator = ResumeGenerator()
        self.validator = ClaimValidator()
        self.cache = SemanticCache()
        self.settings = get_settings()

    async def load_profile(self, user_id: str) -> UserProfile:
        profile = await self.profile_repository.load_profile(user_id)
        if profile is None:
            raise HTTPException(status_code=404, detail="Profile not found")
        return profile

    async def generate_resume(self, job_posting: str, user_id: str) -> dict[str, Any]:
        cached = await self.cache.get_similar(job_posting)
        if cached and cached.confidence > 0.9:
            return {
                "resume": cached.resume,
                "confidence": cached.confidence,
                "needs_review": cached.confidence < 0.9,
            }

        profile = await self.load_profile(user_id)
        draft = await self.generator.generate(job_posting, profile)

        validation_result = await self.validator.validate(draft, profile)

        if validation_result.confidence < self.settings.validation_confidence_threshold:
            draft = await self.fix_issues(draft, validation_result.issues)

        review_items: list[ReviewItem] = []
        if validation_result.confidence < 0.9 or validation_result.issues:
            review_items = [
                ReviewItem(
                    user_id=user_id,
                    item_type=issue.section or "resume",
                    content=issue.message,
                    reason="Validation flagged content",
                    confidence=validation_result.confidence,
                )
                for issue in validation_result.issues
            ]
            if review_items:
                await self.review_service.store_pending_items(user_id, review_items)

        await self.cache.store(job_posting, draft, validation_result.confidence)

        return {
            "resume": draft,
            "confidence": validation_result.confidence,
            "needs_review": validation_result.confidence < 0.9 or bool(review_items),
        }

    async def fix_issues(
        self, draft: dict[str, Any], issues: list[ValidationIssue]
    ) -> dict[str, Any]:
        if not issues:
            return draft
        cleaned = draft.copy()
        for issue in issues:
            section = getattr(issue, "section", None)
            if section and section in cleaned and isinstance(cleaned[section], list):
                cleaned[section] = [
                    item
                    for item in cleaned[section]
                    if issue.message.lower() not in str(item).lower()
                ]
        return cleaned
