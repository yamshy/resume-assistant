from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Protocol

from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from .errors import ToolInvocationError


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

    def __post_init__(self) -> None:
        self._client = ChatOpenAI(model=self.model, temperature=self.temperature)
        self._plan_prompt = ChatPromptTemplate.from_messages(
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
        )
        self._draft_prompt = ChatPromptTemplate.from_messages(
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
        )
        self._critique_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You review resumes for quality issues. Return JSON with keys 'needs_revision' (boolean) and 'issues' (list of strings).",
                ),
                (
                    "human",
                    "Resume markdown:```\n{resume_text}\n```\nCandidate profile: {profile_json}\n"
                    "Identify gaps, placeholders, or missing impact. If the resume is acceptable, return needs_revision=false with an empty issues list.",
                ),
            ]
        )
        self._compliance_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You enforce compliance and redaction policies. Respond with JSON containing 'status' ('approved' or 'rejected') and 'violations' (list of strings).",
                ),
                (
                    "human",
                    "Resume markdown:```\n{resume_text}\n```\nPolicy guidance: {policy_json}\n"
                    "If any policy rule is violated, set status to 'rejected' and list the violations.",
                ),
            ]
        )

    def plan_resume(self, profile: Dict[str, Any], knowledge_hits: List[Dict[str, Any]]) -> Dict[str, Any]:
        response = self._invoke_json(
            self._plan_prompt,
            profile_json=json.dumps(profile),
            knowledge_json=json.dumps(knowledge_hits),
        )
        summary = response.get("summary")
        skills = response.get("skills")
        experience = response.get("experience")
        if not isinstance(summary, str) or not isinstance(skills, list) or not isinstance(experience, list):
            raise ToolInvocationError("LLM plan response missing required fields")
        return {
            "summary": summary,
            "skills": skills,
            "experience": experience,
        }

    def draft_resume(self, plan: Dict[str, Any], profile: Dict[str, Any], knowledge_hits: List[Dict[str, Any]]) -> str:
        content = self._invoke_text(
            self._draft_prompt,
            plan_json=json.dumps({"plan": plan, "profile": profile, "knowledge": knowledge_hits}),
        )
        if not isinstance(content, str) or not content.strip():
            raise ToolInvocationError("LLM returned empty resume content")
        return content

    def critique_resume(self, resume_text: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        response = self._invoke_json(
            self._critique_prompt,
            resume_text=resume_text,
            profile_json=json.dumps(profile),
        )
        needs_revision = bool(response.get("needs_revision"))
        issues = response.get("issues", [])
        if not isinstance(issues, list):
            raise ToolInvocationError("LLM critique response must include list of issues")
        return {"needs_revision": needs_revision, "issues": issues}

    def compliance_review(self, resume_text: str, policy: Dict[str, Any]) -> Dict[str, Any]:
        response = self._invoke_json(
            self._compliance_prompt,
            resume_text=resume_text,
            policy_json=json.dumps(policy),
        )
        status = response.get("status")
        violations = response.get("violations", [])
        if status not in {"approved", "rejected"}:
            raise ToolInvocationError("LLM compliance response must set status to approved or rejected")
        if not isinstance(violations, list):
            raise ToolInvocationError("LLM compliance response must provide violations list")
        return {"status": status, "violations": violations}

    def _invoke_json(self, prompt: ChatPromptTemplate, **kwargs: Any) -> Dict[str, Any]:
        content = self._invoke_text(prompt, **kwargs)
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive branch
            raise ToolInvocationError("LLM response was not valid JSON") from exc

    def _invoke_text(self, prompt: ChatPromptTemplate, **kwargs: Any) -> str:
        messages: List[BaseMessage] = prompt.format_messages(**kwargs)
        response = self._client.invoke(messages)
        content = response.content
        if isinstance(content, list):
            return "".join(part.get("text", "") for part in content if isinstance(part, dict))
        if not isinstance(content, str):
            raise ToolInvocationError("Unexpected LLM content type")
        return content


__all__ = ["ResumeLLM", "OpenAIResumeLLM"]
