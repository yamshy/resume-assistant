from __future__ import annotations

from typing import Dict, List

from langchain_core.messages import AIMessage
from langgraph.graph import END, StateGraph

from ..state import AgentConfig, ResumeGraphState
from ..tools import ToolInvocationError, ToolRegistry


def build_drafting_graph(registry: ToolRegistry, config: AgentConfig) -> StateGraph:
    """Compile the drafting subgraph responsible for creating resume drafts."""

    graph = StateGraph(ResumeGraphState)

    def plan_resume(state: ResumeGraphState) -> ResumeGraphState:
        profile: Dict[str, object] = state.get("artifacts", {}).get("profile", {})  # type: ignore[assignment]
        if not profile:
            raise ToolInvocationError("profile artifact required before drafting")
        target = str(profile.get("target_role", ""))
        knowledge_hits = registry.vector_store.similarity_search(target) if target else []
        llm_plan = registry.llm.plan_resume(profile, knowledge_hits)
        drafted_plan = {
            "profile_name": profile.get("name", "Candidate"),
            "headline": profile.get("headline", target or "Professional"),
            "summary": llm_plan["summary"],
            "skills": llm_plan["skills"],
            "experience": llm_plan["experience"],
        }
        artifacts = {
            "draft_plan": drafted_plan,
            "profile": profile,
            "knowledge_hits": knowledge_hits,
        }
        return ResumeGraphState(
            artifacts=artifacts,
            audit_trail=["drafting.outline_prepared"],
            status="in_progress",
        )

    def render_resume(state: ResumeGraphState) -> ResumeGraphState:
        plan: Dict[str, object] = state.get("artifacts", {}).get("draft_plan", {})  # type: ignore[assignment]
        profile: Dict[str, object] = state.get("artifacts", {}).get("profile", {})  # type: ignore[assignment]
        knowledge_hits: List[Dict[str, object]] = state.get("artifacts", {}).get("knowledge_hits", [])  # type: ignore[assignment]
        if not plan or not profile:
            raise ToolInvocationError("draft_plan and profile required before rendering")
        resume_text = registry.llm.draft_resume(plan, profile, knowledge_hits)
        ai_message = AIMessage(content=resume_text, name=config.default_model)
        previous_drafts = float(state.get("metrics", {}).get("drafts", 0.0))
        next_draft_total = previous_drafts + 1.0
        return ResumeGraphState(
            artifacts={"draft_resume": resume_text},
            messages=[ai_message],
            audit_trail=["drafting.resume_rendered"],
            metrics={"drafts": next_draft_total},
        )

    def determine_next_stage(state: ResumeGraphState) -> ResumeGraphState:
        skip_critique = state.get("flags", {}).get("skip_critique", False)
        next_stage = "compliance" if skip_critique else "critique"
        return ResumeGraphState(audit_trail=["drafting.completed"], stage=next_stage)

    graph.add_node("plan", plan_resume)
    graph.add_node("render", render_resume)
    graph.add_node("finalize", determine_next_stage)

    graph.set_entry_point("plan")
    graph.add_edge("plan", "render")
    graph.add_edge("render", "finalize")
    graph.add_edge("finalize", END)

    return graph


__all__ = ["build_drafting_graph"]
