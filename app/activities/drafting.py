from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field
from temporalio import activity

from ..state import AgentConfig, ResumeMessage
from . import get_registry


class PlanResumeInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    profile: Dict[str, Any] = Field(default_factory=dict)
    request_id: str
    config: AgentConfig


class PlanResumeResult(BaseModel):
    draft_plan: Dict[str, Any]
    knowledge_hits: List[Dict[str, Any]] = Field(default_factory=list)
    audit_event: str


class RenderResumeInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    plan: Dict[str, Any]
    profile: Dict[str, Any]
    knowledge_hits: List[Dict[str, Any]] = Field(default_factory=list)
    config: AgentConfig
    previous_drafts: float = 0.0


class RenderResumeResult(BaseModel):
    resume_markdown: str
    message: ResumeMessage
    audit_event: str
    metrics: Dict[str, float] = Field(default_factory=dict)


@activity.defn
async def plan_resume(payload: PlanResumeInput) -> PlanResumeResult:
    """Produce a structured resume plan using the LLM."""

    profile = payload.profile
    if not profile:
        raise ValueError("profile artifact required before drafting")
    registry = get_registry()
    target = str(profile.get("target_role", ""))
    knowledge_hits = registry.vector_store.similarity_search(target) if target else []
    llm_plan = registry.llm.plan_resume(profile, knowledge_hits)
    drafted_plan = {
        "profile_name": profile.get("name", "Candidate"),
        "headline": profile.get("headline", target or "Professional"),
        "summary": llm_plan["summary"],
        "skills": llm_plan.get("skills", []),
        "experience": llm_plan.get("experience", []),
    }
    audit_label = "drafting.outline_prepared"
    return PlanResumeResult(
        draft_plan=drafted_plan,
        knowledge_hits=knowledge_hits,
        audit_event=audit_label,
    )


@activity.defn
async def render_resume(payload: RenderResumeInput) -> RenderResumeResult:
    """Render resume markdown from a plan using the LLM."""

    if not payload.plan or not payload.profile:
        raise ValueError("draft_plan and profile required before rendering")
    registry = get_registry()
    resume_text = registry.llm.draft_resume(payload.plan, payload.profile, payload.knowledge_hits)
    message = ResumeMessage(role="assistant", content=resume_text, model=payload.config.default_model)
    next_draft_total = payload.previous_drafts + 1.0
    metrics = {"drafts": next_draft_total}
    return RenderResumeResult(
        resume_markdown=resume_text,
        message=message,
        audit_event="drafting.resume_rendered",
        metrics=metrics,
    )


__all__ = [
    "PlanResumeInput",
    "PlanResumeResult",
    "RenderResumeInput",
    "RenderResumeResult",
    "plan_resume",
    "render_resume",
]
