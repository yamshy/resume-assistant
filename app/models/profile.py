"""Pydantic models describing a verified user profile."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Experience(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    company: str
    role: str
    start_date: datetime
    end_date: datetime | None = None
    description: str = ""
    achievements: list[str] = Field(default_factory=list)
    skills_used: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1, default=0.8)
    embedding: list[float] | None = None


class Skill(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    category: str = "general"
    proficiency: str = "intermediate"
    years: int = 0
    evidence: list[UUID] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1, default=0.8)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UserProfile(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    experiences: list[Experience] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
    education: list[dict[str, Any]] = Field(default_factory=list)
    projects: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    def touch(self) -> None:
        self.updated_at = utc_now()


__all__ = ["Experience", "Skill", "UserProfile"]
