"""Resume ingestion pipeline implementation."""

from __future__ import annotations

import asyncio
from typing import Iterable

from app.config import get_settings
from app.models.profile import UserProfile
from app.models.review import ReviewItem
from app.services.repository import ProfileRepository
from app.services.validation import ReviewService

from app.agents.deduplicator import Deduplicator
from app.agents.parser import ResumeParser


class IngestionService:
    def __init__(
        self,
        profile_repository: ProfileRepository,
        review_service: ReviewService,
    ) -> None:
        self.profile_repository = profile_repository
        self.review_service = review_service
        self.parser = ResumeParser()
        self.deduplicator = Deduplicator()
        self.settings = get_settings()

    async def ingest_resumes(
        self,
        resumes: Iterable[bytes],
        user_id: str,
    ) -> tuple[UserProfile, list[ReviewItem]]:
        parsed_data = await asyncio.gather(
            *[self.parser.parse(resume) for resume in resumes]
        )
        merged_profile = await self.deduplicator.merge(parsed_data)
        merged_profile.touch()
        await self.profile_repository.upsert_profile(user_id, merged_profile)
        review_items = self.identify_ambiguities(user_id, merged_profile)
        if review_items:
            await self.review_service.store_pending_items(user_id, review_items)
        return merged_profile, review_items

    def identify_ambiguities(
        self, user_id: str, profile: UserProfile
    ) -> list[ReviewItem]:
        threshold = self.settings.review_confidence_threshold
        pending: list[ReviewItem] = []
        for experience in profile.experiences:
            if experience.confidence < threshold:
                pending.append(
                    ReviewItem(
                        user_id=user_id,
                        item_type="experience",
                        content=experience.description or f"{experience.role} at {experience.company}",
                        reason="Low confidence in parsed experience",
                        confidence=experience.confidence,
                    )
                )
        for skill in profile.skills:
            if skill.confidence < threshold:
                pending.append(
                    ReviewItem(
                        user_id=user_id,
                        item_type="skill",
                        content=skill.name,
                        reason="Skill requires verification",
                        confidence=skill.confidence,
                    )
                )
        return pending

    async def load_profile(self, user_id: str) -> UserProfile | None:
        return await self.profile_repository.load_profile(user_id)
