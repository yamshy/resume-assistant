"""Pydantic schemas for the resume memory service."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    job_posting: str = Field(..., description="Raw job description text")


class MemoryApprovalRequest(BaseModel):
    item_type: Literal["skill", "experience", "achievement"]
    item_id: str


class TeachInfo(BaseModel):
    type: Literal["skill", "experience", "preference"]
    data: dict[str, Any]
    category: str | None = None


class ReviewDecision(BaseModel):
    id: str
    original: str | None = None
    edited: str | None = None
    context: str | None = None


class ReviewSubmitRequest(BaseModel):
    decisions: list[ReviewDecision] = Field(default_factory=list)


class StatusResponse(BaseModel):
    status: str
