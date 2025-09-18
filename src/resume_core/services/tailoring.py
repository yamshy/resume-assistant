from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, List, Tuple
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ValidationError

from resume_core.agents.tailoring import TailoringAgents
from resume_core.models import (
    ApprovalResult,
    ApprovalWorkflow,
    JobAnalysis,
    ResumeHistoryItem,
    ReviewDecision,
    TailoringResult,
    ValidationResult,
)
from resume_core.services.profile import ProfileStore


class TailoringPreferences(BaseModel):
    emphasis_areas: List[str] = Field(default_factory=list)
    excluded_sections: List[str] = Field(default_factory=list)


class ProfileNotFoundError(RuntimeError):
    """Raised when the profile has not been configured yet."""


class ResumeNotFoundError(RuntimeError):
    """Raised when a resume identifier cannot be located."""


class UnsupportedFormatError(RuntimeError):
    """Raised when a download format is not implemented."""


class JobAnalysisNotFoundError(RuntimeError):
    """Raised when a supplied job analysis identifier is unknown."""


class ResumeNotApprovedError(RuntimeError):
    """Raised when attempting to download a resume before approval."""


@dataclass
class ResumeRecord:
    result: TailoringResult
    status: str


class ResumeTailoringService:
    def __init__(
        self,
        profile_store: ProfileStore | None = None,
        *,
        agents: TailoringAgents | None = None,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self.profile_store = profile_store or ProfileStore()
        self.agents = agents or TailoringAgents.default()
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._resumes: Dict[UUID, ResumeRecord] = {}
        self._history: List[ResumeHistoryItem] = []
        self._history_index: Dict[UUID, int] = {}
        self._job_analyses: Dict[UUID, JobAnalysis] = {}

    async def analyze_job(self, job_description: str) -> JobAnalysis:
        if not job_description or not job_description.strip():
            raise ValueError("Job description cannot be empty")
        analysis = await self.agents.job_analysis.analyze(job_description)
        analysis_id = uuid4()
        analysis_with_id = analysis.model_copy(update={"analysis_id": analysis_id})
        self._job_analyses[analysis_id] = analysis_with_id
        return analysis_with_id

    async def tailor_resume(
        self,
        *,
        job_description: str,
        job_analysis_id: UUID | None = None,
        preferences: TailoringPreferences | None = None,
    ) -> TailoringResult:
        profile = self.profile_store.get_profile()
        if profile is None:
            raise ProfileNotFoundError("User profile not configured")

        if job_analysis_id is not None:
            analysis = self._get_stored_analysis(job_analysis_id)
        else:
            analysis = await self.analyze_job(job_description)
        matching = await self.agents.profile_matching.match(analysis, profile)
        preferences_dict = (preferences or TailoringPreferences()).model_dump()
        timestamp = self._clock()
        resume = await self.agents.resume_generation.generate(
            analysis=analysis,
            matching=matching,
            profile=profile,
            preferences=preferences_dict,
            timestamp=timestamp,
        )
        validation = await self.agents.validation.validate(analysis, matching, resume)
        workflow = await self.agents.human_interface.evaluate(matching, validation)

        resume_id = uuid4()
        result = TailoringResult(
            resume_id=resume_id,
            job_analysis=analysis,
            matching_result=matching,
            tailored_resume=resume,
            validation_result=validation,
            approval_workflow=workflow,
        )

        status = self._initial_status(workflow)
        record = ResumeRecord(result=result, status=status)
        self._resumes[resume_id] = record
        history_item = ResumeHistoryItem(
            resume_id=resume_id,
            job_title=analysis.job_title,
            company_name=analysis.company_name,
            created_at=timestamp,
            status=status,
            match_score=matching.overall_match_score,
        )
        self._history_index[resume_id] = len(self._history)
        self._history.append(history_item)
        return result

    async def approve_resume(self, resume_id: UUID, decision: ReviewDecision) -> ApprovalResult:
        record = self._resumes.get(resume_id)
        if record is None:
            raise ResumeNotFoundError(f"Resume {resume_id} not found")

        decision_value = decision.decision
        status = decision_value
        revision_needed = decision_value in {"needs_revision", "rejected"}
        final_url = None
        if decision_value == "approved":
            final_url = f"http://localhost:8000/resumes/{resume_id}/download"
            revision_needed = False

        next_steps = self._determine_next_steps(decision_value, decision, record.result)
        approval = ApprovalResult(
            status=decision_value,
            final_resume_url=final_url,
            revision_needed=revision_needed,
            next_steps=next_steps,
        )

        record.status = status
        history_index = self._history_index.get(resume_id)
        if history_index is not None:
            self._history[history_index] = self._history[history_index].model_copy(update={"status": status})

        return approval

    def get_history(self, *, limit: int, offset: int) -> Tuple[List[ResumeHistoryItem], int]:
        total = len(self._history)
        start = min(offset, total)
        end = min(start + max(limit, 1), total)
        return self._history[start:end], total

    def get_result(self, resume_id: UUID) -> TailoringResult:
        record = self._resumes.get(resume_id)
        if record is None:
            raise ResumeNotFoundError(f"Resume {resume_id} not found")
        return record.result

    def get_resume_markdown(self, resume_id: UUID) -> str:
        result = self.get_result(resume_id)
        return result.tailored_resume.full_resume_markdown

    def download_resume(self, resume_id: UUID, format_: str) -> str:
        record = self._resumes.get(resume_id)
        if record is None:
            raise ResumeNotFoundError(f"Resume {resume_id} not found")
        if record.status != "approved":
            raise ResumeNotApprovedError(
                f"Resume {resume_id} is not approved for download"
            )
        if format_ != "markdown":
            raise UnsupportedFormatError(f"Format '{format_}' is not supported")
        return record.result.tailored_resume.full_resume_markdown

    def _initial_status(self, workflow: ApprovalWorkflow) -> str:
        if workflow.auto_approve_eligible and not workflow.requires_human_review:
            return "approved"
        return "pending"

    def _determine_next_steps(
        self,
        decision: str,
        payload: ReviewDecision,
        result: TailoringResult,
    ) -> List[str]:
        company = result.job_analysis.company_name or "the target company"
        if decision == "approved":
            return [
                "Download your tailored resume",
                "Review final formatting",
                f"Submit your application to {company}",
            ]
        if decision == "needs_revision":
            return payload.requested_modifications or [
                "Provide additional details for missing requirements",
                "Clarify achievements for highlighted sections",
            ]
        if decision == "rejected":
            return ["Review feedback and consider generating a new version"]
        return ["Awaiting further review"]

    def _get_stored_analysis(self, analysis_id: UUID) -> JobAnalysis:
        analysis = self._job_analyses.get(analysis_id)
        if analysis is None:
            raise JobAnalysisNotFoundError(f"Job analysis {analysis_id} not found")
        return analysis.model_copy(deep=True)


def validate_preferences(data: dict | None) -> TailoringPreferences:
    if data is None:
        return TailoringPreferences()
    try:
        return TailoringPreferences.model_validate(data)
    except ValidationError as exc:  # pragma: no cover - FastAPI surfaces the error
        raise exc

