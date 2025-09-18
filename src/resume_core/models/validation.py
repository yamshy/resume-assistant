from __future__ import annotations

from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    code: str
    field: str
    message: str
    severity: str = "warning"


class ValidationResult(BaseModel):
    passed: bool
    issues: list[ValidationIssue] = Field(default_factory=list)
    score: float = 0.0
