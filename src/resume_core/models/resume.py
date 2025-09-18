from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from .job import JobAnalysis
from .matching import MatchingResult


class ResumeOptimization(BaseModel):
    model_config = ConfigDict(extra="ignore")

    section: str
    original_content: str
    optimized_content: str
    optimization_reason: str
    keywords_added: List[str] = Field(default_factory=list)
    match_improvement: float = Field(default=0.0, ge=0.0, le=1.0)


class TailoredResume(BaseModel):
    model_config = ConfigDict(extra="ignore")

    job_title: str
    company_name: str
    optimizations: List[ResumeOptimization] = Field(default_factory=list)
    full_resume_markdown: str
    summary_of_changes: str
    estimated_match_score: float = Field(ge=0.0, le=1.0)
    generation_timestamp: datetime


class ValidationResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    is_valid: bool
    accuracy_score: float = Field(ge=0.0, le=1.0)
    readability_score: float = Field(ge=0.0, le=1.0)
    keyword_optimization_score: float = Field(ge=0.0, le=1.0)
    issues: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    overall_quality_score: float = Field(ge=0.0, le=1.0)
    validation_timestamp: datetime


class ApprovalWorkflow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    requires_human_review: bool
    review_reasons: List[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0)
    auto_approve_eligible: bool


class TailoringResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    resume_id: UUID
    job_analysis: JobAnalysis
    matching_result: MatchingResult
    tailored_resume: TailoredResume
    validation_result: ValidationResult
    approval_workflow: ApprovalWorkflow


class ReviewDecision(BaseModel):
    model_config = ConfigDict(extra="ignore")

    decision: str = Field(pattern="^(pending|approved|rejected|needs_revision)$")
    feedback: Optional[str] = None
    requested_modifications: List[str] = Field(default_factory=list)
    approved_sections: List[str] = Field(default_factory=list)
    rejected_sections: List[str] = Field(default_factory=list)


class ApprovalResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: str
    final_resume_url: Optional[HttpUrl] = None
    revision_needed: bool
    next_steps: List[str] = Field(default_factory=list)


class ResumeHistoryItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    resume_id: UUID
    job_title: str
    company_name: str
    created_at: datetime
    status: str
    match_score: float = Field(ge=0.0, le=1.0)

