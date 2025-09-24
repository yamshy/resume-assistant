from __future__ import annotations

from typing import Dict

from langgraph.graph import END, StateGraph

from ..state import AgentConfig, ResumeGraphState
from ..tools import ToolRegistry


def build_critique_graph(registry: ToolRegistry, config: AgentConfig) -> StateGraph:
    """Compile critique logic that can trigger revision loops when necessary."""

    graph = StateGraph(ResumeGraphState)

    def inspect_resume(state: ResumeGraphState) -> ResumeGraphState:
        resume_text: str = state.get("artifacts", {}).get("draft_resume", "")  # type: ignore[assignment]
        profile: Dict[str, object] = state.get("artifacts", {}).get("profile", {})  # type: ignore[assignment]
        if not resume_text or not profile:
            raise ValueError("draft_resume and profile required before critique")
        critique = registry.llm.critique_resume(resume_text, profile)
        prior_revisions = int(state.get("flags", {}).get("revision_count", 0))
        needs_revision = bool(critique.get("needs_revision")) and prior_revisions < config.max_revision_loops
        revision_count = prior_revisions + 1 if needs_revision else prior_revisions
        issues = critique.get("issues", [])
        audit_label = "critique.changes_requested" if needs_revision else "critique.approved"
        next_stage = "drafting" if needs_revision else "compliance"
        metrics = {"revisions": float(revision_count)} if needs_revision else {}
        flags = {"needs_revision": needs_revision, "revision_count": revision_count}
        return ResumeGraphState(
            artifacts={"critique": {"issues": issues}},
            audit_trail=[audit_label],
            stage=next_stage,
            metrics=metrics,
            flags=flags,
        )

    graph.add_node("critique", inspect_resume)
    graph.set_entry_point("critique")
    graph.add_edge("critique", END)

    return graph


__all__ = ["build_critique_graph"]
