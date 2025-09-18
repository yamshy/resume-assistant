from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    severity: str = Field(pattern=r"^(low|medium|high|critical)$")
    category: str = Field(pattern=r"^(accuracy|consistency|formatting|content)$")
    description: str
    location: str | None = None
    suggestion: str | None = None


class ValidationResult(BaseModel):
    is_valid: bool
    accuracy_score: float = Field(ge=0.0, le=1.0)
    readability_score: float = Field(ge=0.0, le=1.0)
    keyword_optimization_score: float = Field(ge=0.0, le=1.0)
    issues: list[ValidationIssue] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    overall_quality_score: float = Field(ge=0.0, le=1.0)
    validation_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
