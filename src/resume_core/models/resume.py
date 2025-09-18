from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ResumeSection(BaseModel):
    title: str
    content: str


class ContentOptimization(BaseModel):
    focus_keywords: list[str] = Field(default_factory=list)
    readability_score: float = 0.0
    action_verbs_used: list[str] = Field(default_factory=list)


class TailoredResume(BaseModel):
    resume_id: str
    job_title: str
    summary: str
    sections: list[ResumeSection]
    markdown: str
    created_at: datetime
    optimization: ContentOptimization = Field(default_factory=ContentOptimization)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_download_payload(self) -> dict[str, Any]:
        return {
            "resume_id": self.resume_id,
            "content_type": "text/markdown",
            "content": self.markdown,
        }
