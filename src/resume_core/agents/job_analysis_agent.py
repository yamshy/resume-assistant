from __future__ import annotations

import json
import re
from typing import Sequence

from pydantic_ai import Agent
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models.function import FunctionModel

from resume_core.models.job_analysis import JobAnalysis, JobRequirement, RoleLevel
from resume_core.models.profile import SkillCategory

_SKILL_HINTS: dict[str, tuple[str, int]] = {
    "Python": ("python", 5),
    "FastAPI": ("fastapi", 4),
    "PostgreSQL": ("postgresql", 4),
    "AWS": ("aws", 3),
    "Docker": ("docker", 3),
    "Kubernetes": ("kubernetes", 3),
}

_RESPONSIBILITY_PATTERNS: dict[str, str] = {
    "build": "Building scalable web applications",
    "microservices": "Designing and maintaining microservices architecture",
    "cloud": "Working with cloud technologies",
    "team": "Collaborating closely with cross-functional teams",
}


class JobAnalysisAgent:
    """Deterministic job analysis aligned with quickstart contract."""

    def __init__(self) -> None:
        self._agent = Agent(FunctionModel(self._run), name="job-analysis-agent")

    async def analyze(self, job_posting: str) -> JobAnalysis:
        result = await self._agent.run(job_posting)
        payload = json.loads(result.output)
        return JobAnalysis.model_validate(payload)

    async def _run(
        self,
        messages: Sequence[ModelMessage],
        agent_info,  # noqa: ANN001 - required by pydanticAI
    ) -> ModelResponse:
        text = _extract_user_text(messages)
        analysis = self._analyze_text(text)
        return ModelResponse(parts=[TextPart(analysis.model_dump_json())], model_name="function:job-analysis")

    def _analyze_text(self, text: str) -> JobAnalysis:
        lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
        job_title = lines[0] if lines else "Software Engineer"
        company_name = lines[1] if len(lines) > 1 else "Unknown Company"
        lowered = text.lower()

        requirements: list[JobRequirement] = []
        for skill, (hint, importance) in _SKILL_HINTS.items():
            if hint in lowered:
                context = _find_line_containing(text, hint)
                requirements.append(
                    JobRequirement(
                        skill=skill,
                        importance=importance,
                        category=SkillCategory.TECHNICAL,
                        is_required=True,
                        context=context,
                    )
                )

        key_responsibilities = _collect_responsibilities(text)
        preferred = _collect_preferred(text)

        return JobAnalysis(
            company_name=company_name,
            job_title=job_title,
            location=_extract_location(text) or "Not specified",
            requirements=requirements,
            key_responsibilities=key_responsibilities,
            company_culture="collaborative environment",
            role_level=_infer_role_level(job_title),
            industry="technology",
            benefits=["Competitive salary", "Health benefits", "Flexible work"],
            preferred_qualifications=preferred,
        )


def _extract_user_text(messages: Sequence[ModelMessage]) -> str:
    for message in reversed(messages):
        if isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, UserPromptPart):
                    return str(part.content)
    return ""


def _find_line_containing(text: str, fragment: str) -> str:
    for line in text.splitlines():
        if fragment in line.lower():
            return line.strip()
    return ""


def _collect_responsibilities(text: str) -> list[str]:
    responsibilities: set[str] = set()
    lowered = text.lower()
    for needle, description in _RESPONSIBILITY_PATTERNS.items():
        if needle in lowered:
            responsibilities.add(description)
    if not responsibilities:
        responsibilities.add("Deliver high-quality backend services")
    return sorted(responsibilities)


def _collect_preferred(text: str) -> list[str]:
    preferred: list[str] = []
    pattern = re.compile(r"preferred qualifications:\s*(.*)", re.IGNORECASE)
    match = pattern.search(text)
    if match:
        remainder = text[match.end():]
        for line in remainder.splitlines():
            line = line.strip("- ")
            if not line:
                continue
            if line.lower().startswith("we offer"):
                break
            preferred.append(line)
    return preferred


def _extract_location(text: str) -> str | None:
    match = re.search(r"based in ([A-Za-z, ]+)", text)
    if match:
        return match.group(1).strip()
    return None


def _infer_role_level(job_title: str) -> RoleLevel:
    lowered = job_title.lower()
    if "lead" in lowered:
        return RoleLevel.LEAD
    if "principal" in lowered:
        return RoleLevel.EXECUTIVE
    if "senior" in lowered:
        return RoleLevel.SENIOR
    if "junior" in lowered:
        return RoleLevel.JUNIOR
    return RoleLevel.MID
