"""Data structures describing human review workflow."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ReviewItem(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    item_type: str
    content: str
    reason: str
    confidence: float = Field(ge=0, le=1, default=0.5)
    status: str = "pending"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def mark(self, status: str) -> None:
        self.status = status
        self.updated_at = utc_now()


class ReviewDecision(BaseModel):
    item_id: UUID
    action: str
    new_content: str | None = None


__all__ = ["ReviewItem", "ReviewDecision"]
