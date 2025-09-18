"""
Approval workflow data models.

Pydantic models for human-in-the-loop approval process as specified in data-model.md.
"""

from enum import Enum

from pydantic import BaseModel, Field


class ResumeSection(str, Enum):
    """Resume sections that can be optimized."""
    SUMMARY = "summary"
    EXPERIENCE = "experience"
    SKILLS = "skills"
    EDUCATION = "education"
    PROJECTS = "projects"
    ACHIEVEMENTS = "achievements"


class ApprovalStatus(str, Enum):
    """Status of approval workflow."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class ReviewDecision(BaseModel):
    """User approval decision with feedback."""
    decision: ApprovalStatus = Field(description="User's decision")
    feedback: str | None = Field(default=None, description="User feedback on changes")
    requested_modifications: list[str] = Field(default=[], description="Specific changes requested")
    approved_sections: list[ResumeSection] = Field(default=[], description="Sections user approved")
    rejected_sections: list[ResumeSection] = Field(default=[], description="Sections user rejected")


class ApprovalRequest(BaseModel):
    """Request for human review."""
    resume_id: str = Field(description="Unique identifier for this resume version")
    requires_human_review: bool = Field(description="Whether human review is required")
    review_reasons: list[str] = Field(description="Why human review is needed")
    confidence_score: float = Field(ge=0, le=1, description="AI confidence in generated resume")
    risk_factors: list[str] = Field(description="Potential issues identified")
    auto_approve_eligible: bool = Field(description="Whether auto-approval is possible")
    review_deadline: str | None = Field(default=None, description="When review expires")


class ApprovalWorkflow(BaseModel):
    """Complete approval workflow state."""
    request: ApprovalRequest = Field(description="Initial approval request")
    decision: ReviewDecision | None = Field(default=None, description="User decision")
    iterations: int = Field(default=1, description="Number of revision cycles")
    final_resume: str | None = Field(default=None, description="Final approved resume markdown")
    workflow_status: ApprovalStatus = Field(default=ApprovalStatus.PENDING)
    created_at: str = Field(description="Workflow creation timestamp")
    completed_at: str | None = Field(default=None, description="Workflow completion timestamp")


__all__ = [
    "ResumeSection",
    "ApprovalStatus",
    "ReviewDecision",
    "ApprovalRequest",
    "ApprovalWorkflow",
]
