from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from resume_core.agents.human_interface_agent import HumanInterfaceAgent
from resume_core.agents.job_analysis_agent import JobAnalysisAgent
from resume_core.agents.profile_matching_agent import ProfileMatchingAgent
from resume_core.agents.resume_generation_agent import ResumeGenerationAgent
from resume_core.agents.validation_agent import ValidationAgent
from resume_core.models.approval import ApprovalWorkflow, ReviewDecision
from resume_core.models.job_analysis import JobAnalysis
from resume_core.models.matching import MatchingResult
from resume_core.models.profile import UserProfile
from resume_core.models.resume import TailoredResume
from resume_core.models.validation import ValidationResult
from resume_core.services.profile_service import ProfileService
from resume_core.services.storage_service import StorageService
from resume_core.utils.validation import ensure_decision_value


class TailoringResult(BaseModel):
    resume: TailoredResume
    analysis: JobAnalysis
    matching: MatchingResult
    validation: ValidationResult
    recommendation: ReviewDecision
    status: str = Field(default="draft")


class ResumeTailoringService:
    def __init__(
        self,
        profile_service: ProfileService | None = None,
        storage_service: StorageService | None = None,
        *,
        base_path: str | None = None,
    ) -> None:
        if storage_service is not None:
            self.storage = storage_service
        elif profile_service is not None:
            self.storage = profile_service.storage
        else:
            self.storage = StorageService(base_path=base_path)

        self.profile_service = profile_service or ProfileService(storage_service=self.storage)
        self.job_analysis_agent = JobAnalysisAgent()
        self.profile_matching_agent = ProfileMatchingAgent()
        self.resume_generation_agent = ResumeGenerationAgent()
        self.validation_agent = ValidationAgent()
        self.human_interface_agent = HumanInterfaceAgent()

    async def tailor_resume(
        self,
        *,
        job_posting: str,
        profile_overrides: dict[str, Any] | None = None,
    ) -> TailoringResult:
        stored_profile: UserProfile = self.profile_service.load_profile()
        profile: UserProfile = (
            stored_profile.merge_overrides(profile_overrides)
            if profile_overrides
            else stored_profile
        )

        analysis = await self.job_analysis_agent.analyze(job_posting=job_posting)
        matching = await self.profile_matching_agent.match(profile=profile, analysis=analysis)
        resume = await self.resume_generation_agent.generate(
            profile=profile,
            analysis=analysis,
            matching=matching,
        )
        validation = await self.validation_agent.evaluate(
            resume=resume,
            matching=matching,
            analysis=analysis,
        )
        recommendation = await self.human_interface_agent.review(
            resume=resume,
            validation=validation,
        )
        record = {
            "resume": resume.model_dump(),
            "analysis": analysis.model_dump(),
            "matching": matching.model_dump(),
            "validation": validation.model_dump(),
            "recommendation": recommendation.model_dump(),
            "status": "draft",
        }
        self.storage.save_resume_snapshot(resume.resume_id, record)
        return TailoringResult(
            resume=resume,
            analysis=analysis,
            matching=matching,
            validation=validation,
            recommendation=recommendation,
            status="draft",
        )

    async def approve_resume(
        self,
        *,
        resume_id: str,
        decision: str,
        comments: str | None = None,
    ) -> ApprovalWorkflow:
        normalized_decision = ensure_decision_value(decision)
        record = self.storage.load_resume(resume_id)
        workflow = ApprovalWorkflow(
            resume_id=resume_id,
            status=record.get("status", "draft"),
            history=[ReviewDecision.model_validate(item) for item in record.get("history", [])],
        )
        review = ReviewDecision(decision=normalized_decision, comments=comments)
        workflow.record(review)
        record.update(
            {
                "status": workflow.status,
                "history": [item.model_dump() for item in workflow.history],
                "decision": review.model_dump(),
            }
        )
        self.storage.update_resume(resume_id, record)
        return workflow

    def load_resume(self, resume_id: str) -> TailoringResult:
        record = self.storage.load_resume(resume_id)
        return TailoringResult(
            resume=TailoredResume.model_validate(record["resume"]),
            analysis=JobAnalysis.model_validate(record["analysis"]),
            matching=MatchingResult.model_validate(record["matching"]),
            validation=ValidationResult.model_validate(record["validation"]),
            recommendation=ReviewDecision.model_validate(record["recommendation"]),
            status=record.get("status", "draft"),
        )

    def list_history(self) -> list[dict[str, Any]]:
        return self.storage.list_resume_metadata()

    def download_resume(self, resume_id: str) -> dict[str, Any]:
        resume = self.load_resume(resume_id).resume
        return resume.to_download_payload()
