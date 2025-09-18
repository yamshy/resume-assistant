from __future__ import annotations

from pathlib import Path
from typing import Any

from resume_core.agents.human_interface_agent import HumanInterfaceAgent
from resume_core.agents.job_analysis_agent import JobAnalysisAgent
from resume_core.agents.profile_matching_agent import ProfileMatchingAgent
from resume_core.agents.resume_generation_agent import ResumeGenerationAgent
from resume_core.agents.validation_agent import ValidationAgent
from resume_core.models import (
    ApprovalDecision,
    ApprovalOutcome,
    ApprovalWorkflow,
    TailoringRecord,
    TailoringResult,
    UserProfile,
)
from resume_core.models.matching import MatchingResult
from resume_core.models.validation import ValidationResult
from .profile_service import ProfileService
from .storage_service import StorageService


class ResumeService:
    def __init__(
        self,
        profile_service: ProfileService,
        storage_service: StorageService,
        resumes_dir: Path | None = None,
        job_analysis_agent: JobAnalysisAgent | None = None,
        profile_matching_agent: ProfileMatchingAgent | None = None,
        resume_generation_agent: ResumeGenerationAgent | None = None,
        validation_agent: ValidationAgent | None = None,
        human_interface_agent: HumanInterfaceAgent | None = None,
    ) -> None:
        self.profile_service = profile_service
        self.storage = storage_service
        self.resumes_dir = resumes_dir or Path("resumes")
        self.job_analysis_agent = job_analysis_agent or JobAnalysisAgent()
        self.profile_matching_agent = profile_matching_agent or ProfileMatchingAgent()
        self.resume_generation_agent = resume_generation_agent or ResumeGenerationAgent()
        self.validation_agent = validation_agent or ValidationAgent()
        self.human_interface_agent = human_interface_agent or HumanInterfaceAgent()

    async def tailor_resume(
        self,
        job_description: str,
        preferences: dict[str, Any] | None = None,
    ) -> TailoringResult:
        profile = await self._require_profile()
        analysis = await self.job_analysis_agent.analyze(job_description)
        matching = await self.profile_matching_agent.match(profile, analysis)
        if preferences and preferences.get("emphasis_areas"):
            emphasis = ", ".join(preferences["emphasis_areas"])
            matching.recommendations.append(f"Emphasize emphasis areas: {emphasis}")
        resume = await self.resume_generation_agent.generate(profile, analysis, matching)
        validation = await self.validation_agent.validate(profile, analysis, matching, resume)
        workflow = self._build_workflow(matching, validation)

        record = TailoringRecord.create(
            job_analysis=analysis,
            matching_result=matching,
            tailored_resume=resume,
            validation_result=validation,
            approval_workflow=workflow,
        )
        await self._persist_record(record)
        return record.to_result()

    async def get_resume(self, resume_id: str) -> TailoringRecord | None:
        record_path = self.resumes_dir / f"{resume_id}.json"
        data = await self.storage.read_json(record_path)
        if data is None:
            return None
        return TailoringRecord.model_validate(data)

    async def approve_resume(
        self,
        resume_id: str,
        decision: str,
        feedback: str | None = None,
        reviewer: str | None = None,
        approved_sections: list[str] | None = None,
        rejected_sections: list[str] | None = None,
    ) -> ApprovalOutcome:
        record = await self.get_resume(resume_id)
        if record is None:
            raise FileNotFoundError("Resume not found")

        approval_decision: ApprovalDecision = await self.human_interface_agent.review(
            record.tailored_resume,
            decision=decision,
            feedback=feedback,
            reviewer=reviewer,
            approved_sections=approved_sections,
            rejected_sections=rejected_sections,
        )
        record.apply_decision(approval_decision)
        await self._persist_record(record)
        download_url = f"/resumes/{resume_id}/download?format=markdown"
        return record.approval_outcome(download_url)

    async def download_markdown(self, resume_id: str) -> str | None:
        markdown_path = self.resumes_dir / f"{resume_id}.md"
        return await self.storage.read_text(markdown_path)

    async def list_resumes(self) -> list[TailoringResult]:
        files = await self.storage.list_files(self.resumes_dir)
        results: list[TailoringResult] = []
        for file in files:
            if file.suffix != ".json":
                continue
            data = await self.storage.read_json(file.relative_to(self.storage.base_path))
            if data is None:
                continue
            record = TailoringRecord.model_validate(data)
            results.append(record.to_result())
        return results

    async def _persist_record(self, record: TailoringRecord) -> None:
        json_path = self.resumes_dir / f"{record.resume_id}.json"
        markdown_path = self.resumes_dir / f"{record.resume_id}.md"
        await self.storage.write_json(json_path, record.model_dump(mode="json"))
        await self.storage.write_text(markdown_path, record.tailored_resume.full_resume_markdown)

    async def _require_profile(self) -> UserProfile:
        profile = await self.profile_service.load_profile()
        if profile is None:
            raise FileNotFoundError("Profile not found")
        return profile

    def _build_workflow(
        self, matching: MatchingResult, validation: ValidationResult
    ) -> ApprovalWorkflow:
        requires_review = validation.is_valid is False or matching.overall_match_score < 0.85
        confidence = min(1.0, 0.75 + matching.overall_match_score / 4)
        return ApprovalWorkflow(
            requires_human_review=requires_review,
            review_reasons=(
                ["Match score below 0.85"] if requires_review and matching.overall_match_score < 0.85 else []
            ),
            confidence_score=round(confidence, 2),
            auto_approve_eligible=not requires_review
            and validation.is_valid
            and matching.overall_match_score >= 0.9,
        )
