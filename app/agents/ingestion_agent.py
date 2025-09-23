"""Agent orchestrating resume ingestion via multi-step LLM planning."""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Iterable, Sequence, TypeVar

from pydantic import BaseModel, Field, ValidationError

from ..ingestion import ParsedExperience, ParsedResume
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


class ResumeIngestionError(RuntimeError):
    """Base error for ingestion agent failures."""


class MissingIngestionLLMError(ResumeIngestionError):
    """Raised when the ingestion agent cannot access an OpenAI compatible client."""


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
        self._client = self._ensure_client(self._llm)
        self.model = model or os.getenv("INGESTION_AGENT_MODEL", "gpt-4o-mini")
        default_temp = float(os.getenv("INGESTION_AGENT_TEMPERATURE", "0.1"))
        default_retries = int(os.getenv("INGESTION_AGENT_MAX_RETRIES", "1"))
        self.temperature = temperature if temperature is not None else default_temp
        self.max_retries = max_retries if max_retries is not None else default_retries
        registry = tool_registry or {}
        self.tools: ToolRegistry = {name: tool for name, tool in registry.items()}

    async def ingest(self, source: str, text: str, notes: str | None = None) -> ParsedResume:
        plan = await self._plan(text, notes)
        extraction = await self._extract(plan, text, notes)
        parsed = await self._verify(source, text, extraction, notes)
        return parsed

    def _ensure_client(self, llm: Any) -> Any:
        client = getattr(llm, "client", None)
        if client is None:
            raise MissingIngestionLLMError("OpenAI API key required for resume ingestion")
        return client

    async def _plan(self, text: str, notes: str | None) -> PlanModel:
        payload = {
            "resume_excerpt": text[:2000],
            "notes": notes or "",
            "tools": [
                {"name": tool.name, "description": tool.description}
                for tool in self.tools.values()
            ],
        }
        return await self._call_llm("plan", payload, PlanModel)

    async def _extract(self, plan: PlanModel, text: str, notes: str | None) -> ExtractionModel:
        payload = {
            "plan": plan.model_dump(),
            "resume_excerpt": text[:3000],
            "notes": notes or "",
            "available_tools": list(self.tools),
        }
        return await self._call_llm("extract", payload, ExtractionModel)

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
        for field, value in feedback.corrections.items():
            if hasattr(extraction, field) and value:
                setattr(extraction, field, value)
        experiences = self._ensure_model_experiences(extraction.experiences)
        return self._to_parsed_resume(source, extraction, experiences)

    def _ensure_model_experiences(
        self, experiences: Iterable[Any] | None,
    ) -> list[ExtractionExperienceModel]:
        if not experiences:
            return []
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
        return normalised

    def _to_parsed_resume(
        self,
        source: str,
        extraction: ExtractionModel,
        experiences: Sequence[ExtractionExperienceModel],
    ) -> ParsedResume:
        parsed_experiences: list[ParsedExperience] = []
        for experience in experiences:
            achievements = [
                achievement.strip()
                for achievement in experience.achievements
                if achievement and achievement.strip()
            ]
            parsed_experiences.append(
                ParsedExperience(
                    company=experience.company or "Experience",
                    role=experience.role or "Professional",
                    achievements=achievements,
                    start_date=experience.start_date,
                    end_date=experience.end_date,
                    location=experience.location,
                )
            )
        skills = self._dedupe_skills(extraction.skills)
        return ParsedResume(
            source=source,
            full_name=extraction.full_name,
            email=extraction.email,
            phone=extraction.phone,
            skills=skills,
            experiences=parsed_experiences,
        )

    def _dedupe_skills(self, skills: Iterable[str]) -> list[str]:
        deduped: list[str] = []
        seen: set[str] = set()
        for skill in skills:
            cleaned = skill.strip() if isinstance(skill, str) else str(skill).strip()
            if not cleaned:
                continue
            key = cleaned.lower()
            if key not in seen:
                seen.add(key)
                deduped.append(cleaned)
        return deduped

    async def _call_llm(
        self,
        stage: str,
        payload: dict[str, Any],
        response_model: type[TModel],
    ) -> TModel:
        client = getattr(self, "_client", None)
        if client is None:
            raise MissingIngestionLLMError("OpenAI API key required for resume ingestion")
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
        except Exception as exc:
            LOGGER.debug("LLM call for stage %s failed: %s", stage, exc)
            raise MissingIngestionLLMError(
                "OpenAI API key required for resume ingestion"
            ) from exc
        if isinstance(response, response_model):
            return response
        try:
            return response_model.model_validate(response)
        except ValidationError as exc:  # pragma: no cover - defensive parsing
            LOGGER.debug("Failed to validate %s response: %s", stage, exc)
            raise ResumeIngestionError(f"Failed to parse {stage} response") from exc
