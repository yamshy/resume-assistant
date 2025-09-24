from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Mapping, Protocol, Sequence

import instructor
from openai import OpenAI
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .errors import ToolInvocationError


class PlanResponse(BaseModel):
    """Schema describing the expected resume planning payload."""

    model_config = ConfigDict(extra="ignore")

    summary: str
    skills: List[str] = Field(default_factory=list)
    experience: Sequence[Mapping[str, Any]] = Field(default_factory=list)


class CritiqueResponse(BaseModel):
    """Schema describing critique decisions emitted by the LLM."""

    model_config = ConfigDict(extra="ignore")

    needs_revision: bool
    issues: List[str] = Field(default_factory=list)


class ComplianceResponse(BaseModel):
    """Schema representing the compliance verdict returned by the LLM."""

    model_config = ConfigDict(extra="ignore")

    status: Literal["approved", "rejected"]
    violations: List[str] = Field(default_factory=list)


class DraftResponse(BaseModel):
    """Schema ensuring resume drafts include non-empty markdown content."""

    model_config = ConfigDict(extra="ignore")

    resume_markdown: str

    @field_validator("resume_markdown")
    @classmethod
    def validate_resume_markdown(cls, value: str) -> str:
        if not value or not value.strip():
            msg = "resume_markdown must not be empty"
            raise ValueError(msg)
        return value


PLAN_SYSTEM_PROMPT = (
    "You are an expert resume strategist. "
    "Given a candidate profile and relevant knowledge snippets, respond with JSON containing "
    "'summary', 'skills', and 'experience' fields. Each experience item must include 'role', 'company', and 'impact'."
)
PLAN_USER_PROMPT = (
    "Profile JSON: {profile_json}\n"
    "Knowledge snippets: {knowledge_json}\n"
    "Return JSON only with keys summary, skills, experience."
)

DRAFT_SYSTEM_PROMPT = (
    "You are a resume authoring assistant. Format resumes in GitHub-flavored Markdown with sections "
    "'Summary', 'Skills', and 'Experience'. Keep tone professional and concise."
)
DRAFT_USER_PROMPT = (
    "Use this structured plan to produce the resume. Plan JSON: {plan_json}. "
    "Ensure every skill and experience item from the plan appears in the final markdown."
)

CRITIQUE_SYSTEM_PROMPT = (
    "You review resumes for quality issues. Return JSON with keys 'needs_revision' (boolean) and 'issues' (list of strings)."
)
CRITIQUE_USER_PROMPT = (
    "Resume markdown:```\n{resume_text}\n```\n"
    "Candidate profile: {profile_json}\n"
    "Identify gaps, placeholders, or missing impact. If the resume is acceptable, return needs_revision=false with an empty issues list."
)

COMPLIANCE_SYSTEM_PROMPT = (
    "You enforce compliance and redaction policies. Respond with JSON containing 'status' ('approved' or 'rejected') and 'violations' (list of strings)."
)
COMPLIANCE_USER_PROMPT = (
    "Resume markdown:```\n{resume_text}\n```\n"
    "Policy guidance: {policy_json}\n"
    "If any policy rule is violated, set status to 'rejected' and list the violations."
)


class ResumeLLM(Protocol):
    """Interface for LLM-powered resume operations."""

    def plan_resume(
        self, profile: Dict[str, Any], knowledge_hits: Sequence[Mapping[str, Any]]
    ) -> Dict[str, Any]:
        ...

    def draft_resume(
        self,
        plan: Dict[str, Any],
        profile: Dict[str, Any],
        knowledge_hits: Sequence[Mapping[str, Any]],
    ) -> str:
        ...

    def critique_resume(self, resume_text: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        ...

    def compliance_review(self, resume_text: str, policy: Dict[str, Any]) -> Dict[str, Any]:
        ...


@dataclass(slots=True)
class OpenAIResumeLLM:
    """LLM implementation backed by Instructor-wrapped OpenAI chat completions."""

    model: str = "gpt-4o-mini"
    temperature: float = 0.2
    max_retries: int = 3

    _client: Any = field(init=False)

    def __post_init__(self) -> None:
        base_client = OpenAI()
        preferred_modes = [
            getattr(instructor.Mode, "JSON_SCHEMA", None),
            getattr(instructor.Mode, "JSON", None),
            instructor.Mode.TOOLS,
        ]
        last_error: Exception | None = None

        for mode in preferred_modes:
            if mode is None:
                continue

            try:
                wrapped_client = instructor.from_openai(base_client, mode=mode)
            except AssertionError as error:  # pragma: no cover - relies on instructor internals
                last_error = error
                continue

            object.__setattr__(self, "_client", wrapped_client)
            return

        raise RuntimeError("No compatible Instructor mode found for OpenAI client") from last_error

    def _plan_messages(
        self, profile: Mapping[str, Any], knowledge_hits: Sequence[Mapping[str, Any]]
    ) -> List[Dict[str, str]]:
        return [
            {"role": "system", "content": PLAN_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": PLAN_USER_PROMPT.format(
                    profile_json=json.dumps(profile),
                    knowledge_json=json.dumps(list(knowledge_hits)),
                ),
            },
        ]

    def _draft_messages(
        self,
        plan: Mapping[str, Any],
        profile: Mapping[str, Any],
        knowledge_hits: Sequence[Mapping[str, Any]],
    ) -> List[Dict[str, str]]:
        payload = {
            "plan": plan,
            "profile": profile,
            "knowledge": list(knowledge_hits),
        }
        return [
            {"role": "system", "content": DRAFT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": DRAFT_USER_PROMPT.format(
                    plan_json=json.dumps(payload),
                ),
            },
        ]

    def _critique_messages(
        self, resume_text: str, profile: Mapping[str, Any]
    ) -> List[Dict[str, str]]:
        return [
            {"role": "system", "content": CRITIQUE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": CRITIQUE_USER_PROMPT.format(
                    resume_text=resume_text,
                    profile_json=json.dumps(profile),
                ),
            },
        ]

    def _compliance_messages(
        self, resume_text: str, policy: Mapping[str, Any]
    ) -> List[Dict[str, str]]:
        return [
            {"role": "system", "content": COMPLIANCE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": COMPLIANCE_USER_PROMPT.format(
                    resume_text=resume_text,
                    policy_json=json.dumps(policy),
                ),
            },
        ]

    def plan_resume(
        self, profile: Dict[str, Any], knowledge_hits: Sequence[Mapping[str, Any]]
    ) -> Dict[str, Any]:
        try:
            plan: PlanResponse = self._client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                response_model=PlanResponse,
                messages=self._plan_messages(profile, knowledge_hits),
                max_retries=self.max_retries,
            )
        except Exception as exc:  # pragma: no cover - relies on external API
            raise ToolInvocationError("LLM failed to generate resume plan") from exc
        return {
            "summary": plan.summary,
            "skills": plan.skills,
            "experience": plan.experience,
        }

    def draft_resume(
        self,
        plan: Dict[str, Any],
        profile: Dict[str, Any],
        knowledge_hits: Sequence[Mapping[str, Any]],
    ) -> str:
        try:
            draft: DraftResponse = self._client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                response_model=DraftResponse,
                messages=self._draft_messages(plan, profile, knowledge_hits),
                max_retries=self.max_retries,
            )
        except Exception as exc:  # pragma: no cover - relies on external API
            raise ToolInvocationError("LLM failed to draft resume") from exc
        return draft.resume_markdown

    def critique_resume(
        self, resume_text: str, profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            critique: CritiqueResponse = self._client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                response_model=CritiqueResponse,
                messages=self._critique_messages(resume_text, profile),
                max_retries=self.max_retries,
            )
        except Exception as exc:  # pragma: no cover - relies on external API
            raise ToolInvocationError("LLM failed to critique resume") from exc
        return {"needs_revision": critique.needs_revision, "issues": critique.issues}

    def compliance_review(
        self, resume_text: str, policy: Dict[str, Any]
    ) -> Dict[str, Any]:
        try:
            review: ComplianceResponse = self._client.chat.completions.create(
                model=self.model,
                temperature=self.temperature,
                response_model=ComplianceResponse,
                messages=self._compliance_messages(resume_text, policy),
                max_retries=self.max_retries,
            )
        except Exception as exc:  # pragma: no cover - relies on external API
            raise ToolInvocationError("LLM failed to run compliance review") from exc
        return {"status": review.status, "violations": review.violations}


__all__ = ["ResumeLLM", "OpenAIResumeLLM"]
