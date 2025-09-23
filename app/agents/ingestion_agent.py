"""Agent orchestrating resume ingestion via multi-step LLM planning."""

from __future__ import annotations

import inspect
import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Iterable, TypeVar

from pydantic import BaseModel, Field, ValidationError

from ..ingestion import ParsedExperience, ParsedResume
from ..ingestion_utils import coerce_experiences, dedupe_skills
from ..llm import resolve_llm

LOGGER = logging.getLogger(__name__)


ToolCallable = Callable[[str], Awaitable[Any] | Any]


@dataclass
class AgentTool:
    """Descriptor for a callable heuristic that the agent can invoke."""

    name: str
    description: str
    func: ToolCallable


ToolRegistry = Dict[str, AgentTool]


def _merge_and_dedupe_skills(
    existing: Iterable[Any], additional: Iterable[Any] | str | None,
) -> list[str]:
    """Combine skill sources while removing duplicates."""

    combined: list[Any] = list(existing)
    if additional:
        if isinstance(additional, str):
            combined.append(additional)
        else:
            combined.extend(list(additional))
    return dedupe_skills(combined)


class PlanStepModel(BaseModel):
    name: str
    description: str
    tool: str | None = None


class PlanModel(BaseModel):
    steps: list[PlanStepModel] = Field(default_factory=list)
    goal: str | None = None


class ExtractionExperienceModel(BaseModel):
    company: str | None = None
    role: str | None = None
    achievements: list[str] = Field(default_factory=list)
    start_date: str | None = None
    end_date: str | None = None
    location: str | None = None


class ExtractionModel(BaseModel):
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    skills: list[str] = Field(default_factory=list)
    experiences: list[ExtractionExperienceModel] = Field(default_factory=list)


class VerificationFeedback(BaseModel):
    corrections: dict[str, str] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0, le=1)


TModel = TypeVar("TModel", bound=BaseModel)


EMAIL_PATTERN = re.compile(r"[\w.+-]+@[\w.-]+")
PHONE_PATTERN = re.compile(r"\+?\d[\d\s().-]{6,}\d")
SKILL_HEADINGS = ("skill", "technology", "stack", "tool", "competenc")
ROLE_KEYWORDS = (
    "engineer",
    "developer",
    "manager",
    "lead",
    "director",
    "architect",
    "consultant",
    "specialist",
    "analyst",
    "scientist",
    "designer",
)


class ResumeIngestionAgent:
    """Agent that coordinates plan → extract → verify loops for resume ingestion."""

    def __init__(
        self,
        *,
        llm: Any | None = None,
        tool_registry: ToolRegistry | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_retries: int | None = None,
    ) -> None:
        self._llm = llm or resolve_llm()
        self.model = model or os.getenv("INGESTION_AGENT_MODEL", "gpt-4o-mini")
        default_temp = float(os.getenv("INGESTION_AGENT_TEMPERATURE", "0.1"))
        default_retries = int(os.getenv("INGESTION_AGENT_MAX_RETRIES", "1"))
        self.temperature = temperature if temperature is not None else default_temp
        self.max_retries = max_retries if max_retries is not None else default_retries
        registry = tool_registry or default_tool_registry()
        self.tools: ToolRegistry = {name: tool for name, tool in registry.items()}

    async def ingest(self, source: str, text: str, notes: str | None = None) -> ParsedResume:
        plan = await self._plan(text, notes)
        extraction = await self._extract(plan, text, notes)
        parsed = await self._verify(source, text, extraction, notes)
        return parsed

    async def _plan(self, text: str, notes: str | None) -> PlanModel:
        payload = {
            "resume_excerpt": text[:2000],
            "notes": notes or "",
            "tools": [
                {"name": tool.name, "description": tool.description}
                for tool in self.tools.values()
            ],
        }
        response = await self._call_llm("plan", payload, PlanModel)
        if response:
            return response
        return PlanModel(
            goal="Extract contact, skills, and achievements",
            steps=[
                PlanStepModel(
                    name="identify_contacts",
                    description="Use regex tools to pull email and phone numbers",
                    tool="extract_email",
                ),
                PlanStepModel(
                    name="collect_skills",
                    description="Scan skill headings and split tokens",
                    tool="extract_skills",
                ),
                PlanStepModel(
                    name="capture_experience",
                    description="Group bullet points under roles using heading heuristics",
                    tool="extract_experiences",
                ),
            ],
        )

    async def _extract(self, plan: PlanModel, text: str, notes: str | None) -> ExtractionModel:
        payload = {
            "plan": plan.model_dump(),
            "resume_excerpt": text[:3000],
            "notes": notes or "",
            "available_tools": list(self.tools),
        }
        response = await self._call_llm("extract", payload, ExtractionModel)
        if response is None:
            response = ExtractionModel()
        filled = await self._apply_heuristics(text, response)
        return filled

    async def _verify(
        self,
        source: str,
        text: str,
        extraction: ExtractionModel,
        notes: str | None,
    ) -> ParsedResume:
        payload = {
            "extraction": extraction.model_dump(),
            "resume_excerpt": text[:2000],
            "notes": notes or "",
        }
        feedback = await self._call_llm("verify", payload, VerificationFeedback)
        if feedback:
            for field, value in feedback.corrections.items():
                if hasattr(extraction, field) and value:
                    setattr(extraction, field, value)
            for field in feedback.missing_fields:
                await self._recover_field(field, extraction, text)
        experiences = coerce_experiences(extraction.experiences, text)
        fallback_skills = await self._maybe_invoke("extract_skills", text)
        skills = _merge_and_dedupe_skills(extraction.skills, fallback_skills)
        return ParsedResume(
            source=source,
            full_name=extraction.full_name or infer_full_name(text),
            email=extraction.email or find_email(text),
            phone=extraction.phone or find_phone(text),
            skills=skills,
            experiences=experiences,
        )

    async def _recover_field(
        self, field: str, extraction: ExtractionModel, text: str,
    ) -> None:
        if field == "email" and not extraction.email:
            extraction.email = await self._maybe_invoke("extract_email", text)
        if field == "phone" and not extraction.phone:
            extraction.phone = await self._maybe_invoke("extract_phone", text)
        if field == "full_name" and not extraction.full_name:
            extraction.full_name = await self._maybe_invoke("infer_full_name", text)

    async def _apply_heuristics(
        self, text: str, extraction: ExtractionModel,
    ) -> ExtractionModel:
        if not extraction.full_name:
            extraction.full_name = await self._maybe_invoke("infer_full_name", text)
        if not extraction.email:
            extraction.email = await self._maybe_invoke("extract_email", text)
        if not extraction.phone:
            extraction.phone = await self._maybe_invoke("extract_phone", text)
        heuristic_skills = await self._maybe_invoke("extract_skills", text)
        extraction.skills = _merge_and_dedupe_skills(extraction.skills, heuristic_skills)
        if not extraction.experiences:
            heuristic_experiences = await self._maybe_invoke("extract_experiences", text) or []
            extraction.experiences = [
                ExtractionExperienceModel(**experience.model_dump())
                for experience in self._ensure_model_experiences(heuristic_experiences)
            ]
        else:
            extraction.experiences = [
                ExtractionExperienceModel(**experience.model_dump())
                for experience in self._ensure_model_experiences(extraction.experiences)
            ]
        return extraction

    async def _maybe_invoke(self, tool_name: str, text: str) -> Any:
        tool = self.tools.get(tool_name)
        if not tool:
            return None
        result = tool.func(text)
        if inspect.isawaitable(result):
            return await result
        return result

    def _ensure_model_experiences(
        self, experiences: Iterable[Any],
    ) -> list[ExtractionExperienceModel]:
        normalised: list[ExtractionExperienceModel] = []
        for experience in experiences:
            if isinstance(experience, ExtractionExperienceModel):
                normalised.append(experience)
                continue
            if isinstance(experience, ParsedExperience):
                normalised.append(
                    ExtractionExperienceModel(
                        company=experience.company,
                        role=experience.role,
                        achievements=list(experience.achievements),
                        start_date=experience.start_date,
                        end_date=experience.end_date,
                        location=experience.location,
                    )
                )
                continue
            if isinstance(experience, dict):
                normalised.append(ExtractionExperienceModel(**experience))
                continue
        return normalised

    async def _call_llm(
        self,
        stage: str,
        payload: dict[str, Any],
        response_model: type[TModel],
    ) -> TModel | None:
        client = getattr(self._llm, "client", None)
        if client is None:
            return None
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a resume ingestion agent performing the stage: "
                    f"{stage}. Use the provided plan, tools, and notes to return "
                    "structured JSON."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(payload, ensure_ascii=False, indent=2),
            },
        ]
        try:
            response = await client.chat.completions.create(
                model=self.model,
                response_model=response_model,
                messages=messages,
                temperature=self.temperature,
                max_retries=self.max_retries,
            )
        except Exception as exc:  # pragma: no cover - network failures handled via fallback
            LOGGER.debug("LLM call for stage %s failed: %s", stage, exc)
            return None
        if isinstance(response, response_model):
            return response
        try:
            return response_model.model_validate(response)
        except ValidationError as exc:  # pragma: no cover - defensive parsing
            LOGGER.debug("Failed to validate %s response: %s", stage, exc)
            return None


def default_tool_registry() -> ToolRegistry:
    """Return the default set of heuristics tools the agent can use."""

    return {
        "infer_full_name": AgentTool(
            name="infer_full_name",
            description="Guess the candidate full name from resume headers.",
            func=infer_full_name,
        ),
        "extract_email": AgentTool(
            name="extract_email",
            description="Locate email addresses via regex heuristics.",
            func=find_email,
        ),
        "extract_phone": AgentTool(
            name="extract_phone",
            description="Find phone numbers via regex heuristics.",
            func=find_phone,
        ),
        "extract_skills": AgentTool(
            name="extract_skills",
            description="Split skills from headings and deduplicate tokens.",
            func=extract_skills,
        ),
        "extract_experiences": AgentTool(
            name="extract_experiences",
            description="Infer experience blocks and bullet achievements.",
            func=extract_experiences,
        ),
    }


def infer_full_name(text: str) -> str | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines:
        if "@" in line or line.lower().startswith("linkedin"):
            continue
        words = line.split()
        if 1 < len(words) <= 5:
            capitalised = sum(1 for word in words if word and word[0].isupper())
            if capitalised >= max(2, len(words) - 1):
                return line
    return lines[0] if lines else None


def find_email(text: str) -> str | None:
    match = EMAIL_PATTERN.search(text)
    return match.group(0) if match else None


def find_phone(text: str) -> str | None:
    match = PHONE_PATTERN.search(text)
    return match.group(0) if match else None


def extract_skills(text: str) -> list[str]:
    skills: list[str] = []
    lines = text.splitlines()
    for line in lines:
        lower = line.lower()
        if any(heading in lower for heading in SKILL_HEADINGS):
            _, _, trailing = line.partition(":")
            candidates = trailing if trailing else line
            skills.extend(_split_skills(candidates))
    if not skills:
        tokens = re.findall(r"[A-Z]{2,}(?:[+#0-9]*)", text)
        skills.extend(token.strip() for token in tokens if len(token) > 2)
    normalised: list[str] = []
    seen: set[str] = set()
    for skill in skills:
        cleaned = skill.strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key not in seen:
            seen.add(key)
            normalised.append(cleaned)
    return normalised


def extract_experiences(text: str) -> list[ParsedExperience]:
    experiences: list[ParsedExperience] = []
    current: ParsedExperience | None = None
    lines = text.splitlines()
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if _looks_like_role_heading(stripped):
            if current:
                experiences.append(current)
            company, role = _split_heading(stripped)
            current = ParsedExperience(company=company, role=role, achievements=[])
            continue
        bullet_match = re.match(r"^[•\-*]+\s*(.+)", stripped)
        if bullet_match:
            achievement = bullet_match.group(1).strip()
            if not achievement:
                continue
            if current is None:
                current = ParsedExperience(
                    company="Experience",
                    role="Professional",
                    achievements=[achievement],
                )
            else:
                current.achievements.append(achievement)
            continue
        if re.search(r"\b(improv|reduc|increas|launch|deliver|own|build|design)\w*", stripped, re.I):
            if current is None:
                current = ParsedExperience(
                    company="Experience",
                    role="Professional",
                    achievements=[],
                )
            current.achievements.append(stripped)
    if current:
        experiences.append(current)
    if not experiences:
        summary = " ".join(line.strip() for line in lines if line.strip())
        achievements = [summary[:240]] if summary else []
        experiences.append(
            ParsedExperience(
                company="Uploaded Resume",
                role="Professional",
                achievements=achievements,
            )
        )
    return experiences


def _split_skills(text: str) -> list[str]:
    return [token.strip() for token in re.split(r"[,/|•]\s*", text) if token.strip()]


def _looks_like_role_heading(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in ROLE_KEYWORDS)


def _split_heading(text: str) -> tuple[str, str]:
    separators = [" at ", " - ", " | "]
    for separator in separators:
        if separator in text:
            company, role = text.split(separator, 1)
            return company.strip(), role.strip()
    parts = text.split()
    if len(parts) >= 2:
        return " ".join(parts[-1:]), " ".join(parts[:-1])
    return "Experience", text.strip()
