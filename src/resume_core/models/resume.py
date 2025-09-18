from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from .approval import ApprovalDecision, ApprovalDecisionType, ApprovalOutcome, ApprovalWorkflow
from .job_analysis import JobAnalysis
from .matching import MatchingResult
from .validation import ValidationResult


class ResumeSection(str, Enum):
    SUMMARY = "summary"
    EXPERIENCE = "experience"
    SKILLS = "skills"
    EDUCATION = "education"
    PROJECTS = "projects"
    ACHIEVEMENTS = "achievements"


class ContentOptimization(BaseModel):
    section: ResumeSection
    original_content: str
    optimized_content: str
    optimization_reason: str
    keywords_added: list[str] = Field(default_factory=list)
    match_improvement: float = Field(ge=0.0, le=1.0)


class TailoredResume(BaseModel):
    job_title: str
    company_name: str
    optimizations: list[ContentOptimization] = Field(default_factory=list)
    full_resume_markdown: str
    summary_of_changes: str
    estimated_match_score: float = Field(ge=0.0, le=1.0)
    generation_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TailoringResult(BaseModel):
    resume_id: UUID
    job_analysis: JobAnalysis
    matching_result: MatchingResult
    tailored_resume: TailoredResume
    validation_result: ValidationResult
    approval_workflow: ApprovalWorkflow


class TailoringRecord(TailoringResult):
    decision: ApprovalDecision | None = None

    @classmethod
    def create(
        cls,
        job_analysis: JobAnalysis,
        matching_result: MatchingResult,
        tailored_resume: TailoredResume,
        validation_result: ValidationResult,
        approval_workflow: ApprovalWorkflow,
    ) -> TailoringRecord:
        return cls(
            resume_id=uuid4(),
            job_analysis=job_analysis,
            matching_result=matching_result,
            tailored_resume=tailored_resume,
            validation_result=validation_result,
            approval_workflow=approval_workflow,
        )

    def to_result(self) -> TailoringResult:
        return TailoringResult(
            resume_id=self.resume_id,
            job_analysis=self.job_analysis,
            matching_result=self.matching_result,
            tailored_resume=self.tailored_resume,
            validation_result=self.validation_result,
            approval_workflow=self.approval_workflow,
        )

    def apply_decision(self, decision: ApprovalDecision) -> None:
        self.decision = decision

    def approval_outcome(self, download_url: str) -> ApprovalOutcome:
        status = self.decision.decision if self.decision else ApprovalDecisionType.PENDING
        revision_needed = status in {ApprovalDecisionType.REJECTED, ApprovalDecisionType.NEEDS_REVISION}
        if status == ApprovalDecisionType.APPROVED:
            next_steps = [
                "Download your tailored resume",
                "Review final formatting",
                f"Submit your application to {self.job_analysis.company_name}",
            ]
        elif revision_needed:
            next_steps = [
                "Review feedback and update resume",
                "Request another tailoring run",
            ]
        else:
            next_steps = ["Awaiting reviewer decision"]
        return ApprovalOutcome(
            status=status,
            final_resume_url=download_url if status == ApprovalDecisionType.APPROVED else None,
            revision_needed=revision_needed,
            next_steps=next_steps,
        )
