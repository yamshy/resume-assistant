from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class ApprovalDecisionType(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class ApprovalWorkflow(BaseModel):
    requires_human_review: bool
    review_reasons: list[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.5, ge=0.0, le=1.0)
    auto_approve_eligible: bool = False


class ApprovalDecision(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    decision: ApprovalDecisionType
    feedback: str | None = None
    reviewer: str | None = None
    approved_sections: list[str] = Field(default_factory=list)
    rejected_sections: list[str] = Field(default_factory=list)
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ApprovalOutcome(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    status: ApprovalDecisionType
    final_resume_url: str | None
    revision_needed: bool
    next_steps: list[str] = Field(default_factory=list)
