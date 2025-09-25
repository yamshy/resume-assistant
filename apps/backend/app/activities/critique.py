from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field
from temporalio import activity

from ..state import AgentConfig
from . import get_registry


class CritiqueInput(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    resume_markdown: str
    profile: Dict[str, Any] = Field(default_factory=dict)
    revision_count: int = 0
    config: AgentConfig


class CritiqueResult(BaseModel):
    critique: Dict[str, Any] = Field(default_factory=dict)
    audit_event: str
    needs_revision: bool
    revision_count: int
    metrics: Dict[str, float] = Field(default_factory=dict)


@activity.defn
async def run_critique(payload: CritiqueInput) -> CritiqueResult:
    """Run LLM-powered critique and determine if revisions are required."""

    if not payload.resume_markdown or not payload.profile:
        raise ValueError("draft_resume and profile required before critique")
    registry = get_registry()
    critique = registry.llm.critique_resume(payload.resume_markdown, payload.profile)
    needs_revision = bool(critique.get("needs_revision")) and payload.revision_count < payload.config.max_revision_loops
    revision_total = payload.revision_count + 1 if needs_revision else payload.revision_count
    metrics = {"revisions": float(revision_total)} if needs_revision else {}
    audit_label = "critique.changes_requested" if needs_revision else "critique.approved"
    return CritiqueResult(
        critique={"issues": critique.get("issues", [])},
        audit_event=audit_label,
        needs_revision=needs_revision,
        revision_count=revision_total,
        metrics=metrics,
    )


__all__ = ["CritiqueInput", "CritiqueResult", "run_critique"]
