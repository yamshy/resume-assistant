from __future__ import annotations

import json
from typing import Sequence

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models.function import FunctionModel

from resume_core.models.job_analysis import JobAnalysis
from resume_core.models.matching import MatchingResult
from resume_core.models.profile import UserProfile
from resume_core.models.resume import TailoredResume
from resume_core.models.validation import ValidationIssue, ValidationResult


class ValidationAgent:
    def __init__(self) -> None:
        self._agent = Agent(FunctionModel(self._run), name="validation-agent")

    async def validate(
        self,
        profile: UserProfile,
        analysis: JobAnalysis,
        matching: MatchingResult,
        resume: TailoredResume,
    ) -> ValidationResult:
        payload = {
            "profile": profile.model_dump(mode="json"),
            "analysis": analysis.model_dump(mode="json"),
            "matching": matching.model_dump(mode="json"),
            "resume": resume.model_dump(mode="json"),
        }
        result = await self._agent.run(json.dumps(payload))
        return ValidationResult.model_validate(json.loads(result.output))

    async def _run(
        self,
        messages: Sequence[ModelMessage],
        agent_info,  # noqa: ANN001
    ) -> ModelResponse:
        text = _extract_user_text(messages)
        payload = json.loads(text)
        profile = UserProfile.model_validate(payload["profile"])
        analysis = JobAnalysis.model_validate(payload["analysis"])
        matching = MatchingResult.model_validate(payload["matching"])
        resume = TailoredResume.model_validate(payload["resume"])
        validation = self._validate(profile, analysis, matching, resume)
        return ModelResponse(parts=[TextPart(validation.model_dump_json())], model_name="function:validation")

    def _validate(
        self,
        profile: UserProfile,
        analysis: JobAnalysis,
        matching: MatchingResult,
        resume: TailoredResume,
    ) -> ValidationResult:
        issues: list[ValidationIssue] = []

        matched_skills = {match.skill_name.lower() for match in matching.skill_matches}
        missing_requirements = [
            req for req in analysis.requirements if req.skill.lower() not in matched_skills
        ]

        accuracy_score = 0.95 if not missing_requirements else 0.9
        readability_score = 0.9
        keyword_score = min(1.0, accuracy_score - 0.03 + len(matching.skill_matches) * 0.02)

        if missing_requirements:
            issues.append(
                ValidationIssue(
                    severity="medium",
                    category="accuracy",
                    description=f"Missing alignment for {len(missing_requirements)} required skills",
                    location="matching_result",
                    suggestion="Add concrete examples covering the listed skills",
                )
            )

        markdown = resume.full_resume_markdown.strip()
        if not markdown:
            issues.append(
                ValidationIssue(
                    severity="critical",
                    category="content",
                    description="Generated resume content is empty",
                    location="tailored_resume.full_resume_markdown",
                    suggestion="Ensure resume generator populates markdown sections",
                )
            )
        elif markdown.count("##") < 2:
            issues.append(
                ValidationIssue(
                    severity="high",
                    category="content",
                    description="Resume is missing key sections",
                    location="tailored_resume.full_resume_markdown",
                    suggestion="Include summary, experience, and skills sections in the output",
                )
            )

        if not profile.skills:
            issues.append(
                ValidationIssue(
                    severity="medium",
                    category="consistency",
                    description="Profile lacks baseline skills for comparison",
                    location="profile.skills",
                    suggestion="Add at least five core skills to the profile",
                )
            )

        is_valid = not any(issue.severity in {"high", "critical"} for issue in issues)
        overall_quality = round((accuracy_score + readability_score + keyword_score) / 3, 2)

        return ValidationResult(
            is_valid=is_valid,
            accuracy_score=round(accuracy_score, 2),
            readability_score=round(readability_score, 2),
            keyword_optimization_score=round(keyword_score, 2),
            issues=issues,
            strengths=[
                "Strong keyword alignment with job requirements",
                "Quantified achievements preserved",
                "Clear narrative for backend leadership",
            ],
            overall_quality_score=overall_quality,
        )


def _extract_user_text(messages: Sequence[ModelMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, UserPromptPart):
                    return str(part.content)
    return ""
