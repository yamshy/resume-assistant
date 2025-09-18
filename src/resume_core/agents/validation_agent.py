from __future__ import annotations

from typing import Any

from resume_core.agents.base_agent import FunctionBackedAgent
from resume_core.models.job_analysis import JobAnalysis
from resume_core.models.matching import MatchingResult
from resume_core.models.resume import TailoredResume
from resume_core.models.validation import ValidationIssue, ValidationResult


class ValidationAgent(FunctionBackedAgent[ValidationResult]):
    def __init__(self) -> None:
        super().__init__(
            name="validation-agent",
            instructions="Validate tailored resumes for completeness, alignment, and data quality.",
            output_model=ValidationResult,
        )

    def build_output(self, payload: dict[str, Any]) -> ValidationResult:
        resume = TailoredResume.model_validate(payload.get("resume") or {})
        matching = MatchingResult.model_validate(payload.get("matching") or {})
        analysis = JobAnalysis.model_validate(payload.get("analysis") or {})

        issues: list[ValidationIssue] = []
        score = 0.0

        if resume.summary.strip():
            score += 0.35
        else:
            issues.append(
                ValidationIssue(
                    code="missing_summary",
                    field="summary",
                    message="Resume summary is empty",
                    severity="error",
                )
            )

        if resume.sections and all(section.content.strip() for section in resume.sections):
            score += 0.25
        else:
            issues.append(
                ValidationIssue(
                    code="empty_sections",
                    field="sections",
                    message="One or more sections require additional detail",
                    severity="warning",
                )
            )

        if matching.overall_score >= 0.3:
            score += 0.3
        else:
            issues.append(
                ValidationIssue(
                    code="low_alignment",
                    field="matching.overall_score",
                    message="Profile alignment with requirements is low",
                    severity="warning",
                )
            )

        if analysis.requirements and not matching.matched_skills:
            issues.append(
                ValidationIssue(
                    code="missing_matches",
                    field="matching.matched_skills",
                    message="No skills matched the role requirements",
                    severity="error",
                )
            )
        else:
            score += 0.1

        passed = all(issue.severity != "error" for issue in issues)
        final_score = round(min(1.0, max(score, matching.overall_score)), 2)
        if not issues:
            final_score = round(min(1.0, matching.overall_score + 0.2), 2)
        return ValidationResult(passed=passed, issues=issues, score=final_score)

    async def evaluate(
        self,
        *,
        resume: TailoredResume,
        matching: MatchingResult,
        analysis: JobAnalysis,
    ) -> ValidationResult:
        payload = {
            "resume": resume.model_dump(),
            "matching": matching.model_dump(),
            "analysis": analysis.model_dump(),
        }
        return await self.run(payload)
