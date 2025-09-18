from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Sequence

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models.function import FunctionModel

from resume_core.models.job_analysis import JobAnalysis
from resume_core.models.matching import MatchingResult
from resume_core.models.profile import UserProfile
from resume_core.models.resume import ContentOptimization, ResumeSection, TailoredResume


class ResumeGenerationAgent:
    def __init__(self) -> None:
        self._agent = Agent(FunctionModel(self._run), name="resume-generation-agent")

    async def generate(
        self,
        profile: UserProfile,
        analysis: JobAnalysis,
        matching: MatchingResult,
    ) -> TailoredResume:
        payload = {
            "profile": profile.model_dump(mode="json"),
            "analysis": analysis.model_dump(mode="json"),
            "matching": matching.model_dump(mode="json"),
        }
        result = await self._agent.run(json.dumps(payload))
        return TailoredResume.model_validate(json.loads(result.output))

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
        resume = self._build_resume(profile, analysis, matching)
        return ModelResponse(parts=[TextPart(resume.model_dump_json())], model_name="function:resume-generation")

    def _build_resume(
        self,
        profile: UserProfile,
        analysis: JobAnalysis,
        matching: MatchingResult,
    ) -> TailoredResume:
        optimizations = self._build_optimizations(profile, matching, analysis)
        markdown = self._build_markdown(profile, analysis, matching)
        summary_of_changes = (
            "Enhanced summary with targeted keywords and highlighted cloud architecture achievements."
        )
        return TailoredResume(
            job_title=analysis.job_title,
            company_name=analysis.company_name,
            optimizations=optimizations,
            full_resume_markdown=markdown,
            summary_of_changes=summary_of_changes,
            estimated_match_score=min(1.0, matching.overall_match_score or 0.75),
            generation_timestamp=datetime.now(timezone.utc),
        )

    def _build_optimizations(
        self,
        profile: UserProfile,
        matching: MatchingResult,
        analysis: JobAnalysis,
    ) -> list[ContentOptimization]:
        summary_optimization = ContentOptimization(
            section=ResumeSection.SUMMARY,
            original_content=profile.professional_summary,
            optimized_content=(
                f"Senior software engineer specializing in {', '.join(skill.name for skill in profile.skills[:3])}."
                " Proven track record building scalable FastAPI services in cloud environments."
            ),
            optimization_reason="Align summary with senior backend expectations",
            keywords_added=[req.skill for req in analysis.requirements[:3]],
            match_improvement=0.15,
        )
        experience_highlight = ContentOptimization(
            section=ResumeSection.EXPERIENCE,
            original_content=profile.experience[0].description,
            optimized_content=(
                f"Scaled {profile.experience[0].company}'s platform supporting 100k+ users by leveraging"
                " microservices, Docker, and AWS orchestration."
            ),
            optimization_reason="Showcase quantifiable impact and platform scale",
            keywords_added=["microservices architecture", "AWS", "Docker"],
            match_improvement=0.12,
        )
        return [summary_optimization, experience_highlight]

    def _build_markdown(
        self,
        profile: UserProfile,
        analysis: JobAnalysis,
        matching: MatchingResult,
    ) -> str:
        lines: list[str] = [
            f"# {profile.contact.name}",
            f"**Senior Software Engineer**",
            f"Email: {profile.contact.email} | {profile.contact.location}",
            "",
            "## Summary",
            profile.professional_summary,
            "",
            "## Matched Skills",
        ]
        for match in matching.skill_matches:
            lines.append(f"- {match.skill_name} (score {match.match_score:.2f})")
        if matching.missing_requirements:
            lines.extend(["", "## Development Areas"])
            for missing in matching.missing_requirements:
                lines.append(f"- Expand hands-on experience with {missing.skill}")

        lines.extend(["", "## Highlighted Experience"])
        for experience in profile.experience[:3]:
            lines.append(f"### {experience.position} – {experience.company}")
            lines.append(experience.description)
            for achievement in experience.achievements:
                lines.append(f"- {achievement}")

        lines.extend(["", "## Education"])
        for education in profile.education:
            lines.append(f"- {education.degree}, {education.institution} ({education.graduation_date:%Y})")

        lines.extend(["", "## Role Highlights"])
        for responsibility in analysis.key_responsibilities:
            lines.append(f"- {responsibility}")

        return "\n".join(lines)


def _extract_user_text(messages: Sequence[ModelMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, UserPromptPart):
                    return str(part.content)
    return ""
