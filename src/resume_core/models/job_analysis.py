from __future__ import annotations

from pydantic import BaseModel, Field


class JobRequirement(BaseModel):
    name: str
    importance: str = "medium"
    keywords: list[str] = Field(default_factory=list)
    description: str | None = None


class JobContext(BaseModel):
    role: str | None = None
    company: str | None = None
    seniority: str | None = None
    raw_text: str


class JobAnalysis(BaseModel):
    summary: str
    requirements: list[JobRequirement]
    keywords: list[str]
    context: JobContext
