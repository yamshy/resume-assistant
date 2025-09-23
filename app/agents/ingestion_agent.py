"""Agent orchestrating resume ingestion via multi-step LLM planning."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, TypeVar, cast

from instructor import AsyncInstructor, from_openai
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, Field, ValidationError

from ..ingestion import ParsedResume
from ..ingestion_utils import coerce_experiences, dedupe_skills
from ..llm import resolve_ingestion_client

LOGGER = logging.getLogger(__name__)


class IngestionAgentError(RuntimeError):
    """Base exception for resume ingestion agent failures."""


class MissingIngestionLLMError(IngestionAgentError):
    """Raised when no LLM client is available for resume ingestion."""


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
        client: AsyncInstructor | AsyncOpenAI | None = None,
        model: str | None = None,
        temperature: float | None = None,
        max_retries: int | None = None,
    ) -> None:
        self._client: AsyncInstructor = self._prepare_client(client)
        self.model = model or os.getenv("INGESTION_AGENT_MODEL", "gpt-4o-mini")
        default_temp = float(os.getenv("INGESTION_AGENT_TEMPERATURE", "0.1"))
        default_retries = int(os.getenv("INGESTION_AGENT_MAX_RETRIES", "1"))
        self.temperature = temperature if temperature is not None else default_temp
        self.max_retries = max_retries if max_retries is not None else default_retries

    def _prepare_client(
        self, client: AsyncInstructor | AsyncOpenAI | None
    ) -> AsyncInstructor:
        resolved = client if client is not None else resolve_ingestion_client()
        if resolved is None:
            raise MissingIngestionLLMError(
                "OpenAI API key required for resume ingestion",
            )
        if isinstance(resolved, AsyncOpenAI):
            return from_openai(resolved)
        if isinstance(resolved, AsyncInstructor):
            return resolved
        if hasattr(resolved, "chat"):
            return cast(AsyncInstructor, resolved)
        raise TypeError("Unsupported ingestion client type")

    async def ingest(self, source: str, text: str, notes: str | None = None) -> ParsedResume:
        plan = await self._plan(text, notes)
        extraction = await self._extract(plan, text, notes)
        parsed = await self._verify(source, text, extraction, notes)
        return parsed

    async def _plan(self, text: str, notes: str | None) -> PlanModel:
        payload = {
            "resume_excerpt": text[:2000],
            "notes": notes or "",
        }
        return await self._call_llm("plan", payload, PlanModel)

    async def _extract(self, plan: PlanModel, text: str, notes: str | None) -> ExtractionModel:
        payload = {
            "plan": plan.model_dump(),
            "resume_excerpt": text[:3000],
            "notes": notes or "",
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
        if feedback:
            for field, value in feedback.corrections.items():
                if hasattr(extraction, field) and value:
                    setattr(extraction, field, value)
        experiences = coerce_experiences(extraction.experiences, text)
        skills = dedupe_skills(extraction.skills)
        return ParsedResume(
            source=source,
            full_name=extraction.full_name,
            email=extraction.email,
            phone=extraction.phone,
            skills=skills,
            experiences=experiences,
        )

    async def _call_llm(
        self,
        stage: str,
        payload: dict[str, Any],
        response_model: type[TModel],
    ) -> TModel:
        client = self._client
        if client is None:
            raise MissingIngestionLLMError(
                "OpenAI API key required for resume ingestion",
            )
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "You are a resume ingestion agent performing the stage: "
                    f"{stage}. Use the provided plan and notes to return structured "
                    "JSON."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(payload, ensure_ascii=False, indent=2),
            },
        ]
        typed_messages = cast(list[ChatCompletionMessageParam], messages)
        try:
            response = await client.chat.completions.create(
                model=self.model,
                response_model=response_model,
                messages=typed_messages,
                temperature=self.temperature,
                max_retries=self.max_retries,
            )
        except Exception as exc:  # pragma: no cover - network failures handled in caller
            LOGGER.debug("LLM call for stage %s failed: %s", stage, exc)
            raise MissingIngestionLLMError(
                "OpenAI API key required for resume ingestion",
            ) from exc
        if isinstance(response, response_model):
            return response
        try:
            return response_model.model_validate(response)
        except ValidationError as exc:
            LOGGER.debug("Failed to validate %s response: %s", stage, exc)
            raise IngestionAgentError(
                f"LLM returned invalid payload for {stage} stage",
            ) from exc
