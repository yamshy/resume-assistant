"""Models representing resume parsing and generation artifacts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.models.profile import Experience, Skill


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ParsedResume(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID | None = None
    experiences: list[Experience] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
    education: list[dict[str, Any]] = Field(default_factory=list)
    projects: list[dict[str, Any]] = Field(default_factory=list)
    source_name: str | None = None
    parsed_at: datetime = Field(default_factory=utc_now)


class GeneratedResume(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: UUID
    job_posting: str
    sections: dict[str, Any]
    created_at: datetime = Field(default_factory=utc_now)


class ValidationIssue(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    message: str
    section: str | None = None
    severity: str = "medium"


class ValidationResult(BaseModel):
    confidence: float
    issues: list[ValidationIssue] = Field(default_factory=list)


class CachedResume(BaseModel):
    job_hash: str
    job_posting: str
    resume: dict[str, Any]
    confidence: float
    created_at: datetime = Field(default_factory=utc_now)


__all__ = [
    "ParsedResume",
    "GeneratedResume",
    "ValidationIssue",
    "ValidationResult",
    "CachedResume",
]
