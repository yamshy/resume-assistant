"""Persistence helpers built on top of SQLAlchemy."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import NoResultFound

from app.core.database import (
    GeneratedResumeRecord,
    ProfileRecord,
    ReviewRecord,
    get_sessionmaker,
)
from app.models.profile import UserProfile
from app.models.resume import CachedResume
from app.models.review import ReviewItem


class ProfileRepository:
    """Read/write access to stored user profiles."""

    async def upsert_profile(self, user_id: str, profile: UserProfile) -> None:
        sessionmaker = get_sessionmaker()
        async with sessionmaker() as session:
            record = await session.get(ProfileRecord, user_id)
            payload = profile.model_dump(mode="json")
            if record is None:
                session.add(ProfileRecord(user_id=user_id, data=payload))
            else:
                record.data = payload
                record.updated_at = datetime.now(timezone.utc)
            await session.commit()

    async def load_profile(self, user_id: str) -> UserProfile | None:
        sessionmaker = get_sessionmaker()
        async with sessionmaker() as session:
            record = await session.get(ProfileRecord, user_id)
            if record is None:
                return None
            return UserProfile.model_validate(record.data)


class ReviewRepository:
    """Persistence utilities for review items and their status."""

    async def store_items(self, user_id: str, items: Iterable[ReviewItem]) -> None:
        sessionmaker = get_sessionmaker()
        async with sessionmaker() as session:
            for item in items:
                payload = item.model_dump(mode="json")
                await session.merge(
                    ReviewRecord(
                        id=str(item.id),
                        user_id=user_id,
                        payload=payload,
                        status=item.status,
                    )
                )
            await session.commit()

    async def get_pending(self, user_id: str) -> list[ReviewItem]:
        sessionmaker = get_sessionmaker()
        async with sessionmaker() as session:
            stmt = select(ReviewRecord).where(
                ReviewRecord.user_id == user_id, ReviewRecord.status == "pending"
            )
            results = await session.execute(stmt)
            items = []
            for record in results.scalars().all():
                payload = record.payload
                payload["status"] = record.status
                items.append(ReviewItem.model_validate(payload))
            return items

    async def update_status(
        self, item_id: UUID, status: str, new_content: str | None = None
    ) -> None:
        sessionmaker = get_sessionmaker()
        async with sessionmaker() as session:
            record = await session.get(ReviewRecord, str(item_id))
            if record is None:
                raise NoResultFound(f"Review item {item_id} not found")
            record.status = status
            payload = record.payload
            payload["status"] = status
            if new_content is not None:
                payload["content"] = new_content
            record.payload = payload
            record.updated_at = datetime.now(timezone.utc)
            await session.commit()

    async def clear_user(self, user_id: str) -> None:
        sessionmaker = get_sessionmaker()
        async with sessionmaker() as session:
            stmt = select(ReviewRecord).where(ReviewRecord.user_id == user_id)
            results = await session.execute(stmt)
            for record in results.scalars().all():
                await session.delete(record)
            await session.commit()


class GeneratedResumeRepository:
    """Store generated resumes for historical lookup."""

    async def store(self, cache: CachedResume, user_id: str) -> None:
        sessionmaker = get_sessionmaker()
        async with sessionmaker() as session:
            await session.merge(
                GeneratedResumeRecord(
                    id=str(cache.job_hash),
                    user_id=user_id,
                    job_hash=cache.job_hash,
                    job_posting=cache.job_posting,
                    payload=cache.resume,
                    confidence=cache.confidence,
                )
            )
            await session.commit()

    async def get(self, job_hash: str) -> CachedResume | None:
        sessionmaker = get_sessionmaker()
        async with sessionmaker() as session:
            record = await session.get(GeneratedResumeRecord, job_hash)
            if record is None:
                return None
            return CachedResume(
                job_hash=record.job_hash,
                job_posting=record.job_posting,
                resume=record.payload,
                confidence=record.confidence,
                created_at=record.created_at,
            )


__all__ = [
    "ProfileRepository",
    "ReviewRepository",
    "GeneratedResumeRepository",
]
