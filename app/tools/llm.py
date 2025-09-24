from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Protocol

from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

from .errors import ToolInvocationError


class PlanResponse(BaseModel):
    summary: str
    skills: List[str] = Field(default_factory=list)
    experience: List[Dict[str, Any]] = Field(default_factory=list)


class CritiqueResponse(BaseModel):
    needs_revision: bool
    issues: List[str] = Field(default_factory=list)


class ComplianceResponse(BaseModel):
    status: Literal["approved", "rejected"]
    violations: List[str] = Field(default_factory=list)



class ResumeLLM(Protocol):
    """Interface for LLM-powered resume operations."""

    def plan_resume(self, profile: Dict[str, Any], knowledge_hits: List[Dict[str, Any]]) -> Dict[str, Any]:
        ...

    def draft_resume(self, plan: Dict[str, Any], profile: Dict[str, Any], knowledge_hits: List[Dict[str, Any]]) -> str:
        ...

    def critique_resume(self, resume_text: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        ...

    def compliance_review(self, resume_text: str, policy: Dict[str, Any]) -> Dict[str, Any]:
        ...


@dataclass(slots=True)
class OpenAIResumeLLM:
    """LLM implementation backed by OpenAI chat completions via LangChain."""

    model: str = "gpt-4o-mini"
    temperature: float = 0.2

    _client: ChatOpenAI = field(init=False)
    _plan_prompt: ChatPromptTemplate = field(init=False)
    _draft_prompt: ChatPromptTemplate = field(init=False)
    _critique_prompt: ChatPromptTemplate = field(init=False)
    _compliance_prompt: ChatPromptTemplate = field(init=False)
    _plan_chain: Any = field(init=False)
    _critique_chain: Any = field(init=False)
    _compliance_chain: Any = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_client", ChatOpenAI(model=self.model, temperature=self.temperature))
        object.__setattr__(
            self,
            "_plan_prompt",
            ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are an expert resume strategist. "
                        "Given a candidate profile and relevant knowledge snippets, respond with JSON containing "
                        "'summary', 'skills', and 'experience' fields. Each experience item must include 'role', 'company', and 'impact'.",
                    ),
                    (
                        "human",
                        "Profile JSON: {profile_json}\nKnowledge snippets: {knowledge_json}\n"
                        "Return JSON only with keys summary, skills, experience.",
                    ),
                ]
            ),
        )
        object.__setattr__(
            self,
            "_draft_prompt",
            ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are a resume authoring assistant. Format resumes in GitHub-flavored Markdown with sections "
                        "'Summary', 'Skills', and 'Experience'. Keep tone professional and concise.",
                    ),
                    (
                        "human",
                        "Use this structured plan to produce the resume. Plan JSON: {plan_json}. "
                        "Ensure every skill and experience item from the plan appears in the final markdown.",
                    ),
                ]
            ),
        )
        object.__setattr__(
            self,
            "_critique_prompt",
            ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You review resumes for quality issues. Return JSON with keys 'needs_revision' (boolean) and 'issues' (list of strings).",
                    ),
                    (
                        "human",
                        ("Resume markdown:```\n{resume_text}\n```\nCandidate profile: {profile_json}\n"
                         "Identify gaps, placeholders, or missing impact. If the resume is acceptable, return needs_revision=false with an empty issues list."),
                    ),
                ]
            ),
        )
        object.__setattr__(
            self,
            "_compliance_prompt",
            ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You enforce compliance and redaction policies. Respond with JSON containing 'status' ('approved' or 'rejected') and 'violations' (list of strings).",
                    ),
                    (
                        "human",
                        ("Resume markdown:```\n{resume_text}\n```\nPolicy guidance: {policy_json}\n"
                         "If any policy rule is violated, set status to 'rejected' and list the violations."),
                    ),
                ]
            ),
        )
        object.__setattr__(
            self,
            "_plan_chain",
            self._plan_prompt | self._client.with_structured_output(PlanResponse),
        )
        object.__setattr__(
            self,
            "_critique_chain",
            self._critique_prompt | self._client.with_structured_output(CritiqueResponse),
        )
        object.__setattr__(
            self,
            "_compliance_chain",
            self._compliance_prompt | self._client.with_structured_output(ComplianceResponse),
        )

    def plan_resume(self, profile: Dict[str, Any], knowledge_hits: List[Dict[str, Any]]) -> Dict[str, Any]:
        plan: PlanResponse = self._plan_chain.invoke(
            {"profile_json": json.dumps(profile), "knowledge_json": json.dumps(knowledge_hits)}
        )
        return {
            "summary": plan.summary,
            "skills": plan.skills,
            "experience": plan.experience,
        }

    def draft_resume(self, plan: Dict[str, Any], profile: Dict[str, Any], knowledge_hits: List[Dict[str, Any]]) -> str:
        messages: List[BaseMessage] = self._draft_prompt.format_messages(
            plan_json=json.dumps({"plan": plan, "profile": profile, "knowledge": knowledge_hits})
        )
        response = self._client.invoke(messages)
        content = response.content
        if isinstance(content, list):
            content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
        if not isinstance(content, str) or not content.strip():
            raise ToolInvocationError("LLM returned empty resume content")
        return content

    def critique_resume(self, resume_text: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        critique: CritiqueResponse = self._critique_chain.invoke(
            {"resume_text": resume_text, "profile_json": json.dumps(profile)}
        )
        return {"needs_revision": critique.needs_revision, "issues": critique.issues}

    def compliance_review(self, resume_text: str, policy: Dict[str, Any]) -> Dict[str, Any]:
        review: ComplianceResponse = self._compliance_chain.invoke(
            {"resume_text": resume_text, "policy_json": json.dumps(policy)}
        )
        return {"status": review.status, "violations": review.violations}


__all__ = ["ResumeLLM", "OpenAIResumeLLM"]
