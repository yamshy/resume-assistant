from __future__ import annotations

from typing import Dict, Optional

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, StateGraph

from ..state import AgentConfig, ResumeGraphState, TaskType
from ..tools import ToolRegistry, build_default_registry
from .compliance import build_compliance_graph
from .critique import build_critique_graph
from .drafting import build_drafting_graph
from .ingestion import build_ingestion_graph
from .publishing import build_publishing_graph


def _initial_stage(task: Optional[TaskType]) -> str:
    mapping: Dict[Optional[TaskType], str] = {
        "ingest": "ingestion",
        "draft": "drafting",
        "revise": "drafting",
        "resume_pipeline": "ingestion",
        "compliance_only": "compliance",
        "publish": "publishing",
    }
    return mapping.get(task, "ingestion")


def build_supervisor_graph(registry: ToolRegistry, config: AgentConfig) -> StateGraph:
    """Create the supervisor graph that orchestrates all subgraphs."""

    ingestion_graph = build_ingestion_graph(registry).compile()
    drafting_graph = build_drafting_graph(registry, config).compile()
    critique_graph = build_critique_graph(registry, config).compile()
    compliance_graph = build_compliance_graph(registry, config).compile()
    publishing_graph = build_publishing_graph(registry).compile()

    graph = StateGraph(ResumeGraphState)

    def bootstrap(state: ResumeGraphState) -> ResumeGraphState:
        stage = _initial_stage(state.get("task"))
        audit_label = f"supervisor.bootstrap:{stage}"
        return ResumeGraphState(stage=stage, status="in_progress", audit_trail=[audit_label])

    def finalize(state: ResumeGraphState) -> ResumeGraphState:
        status = state.get("status")
        if status not in {"complete", "error"}:
            status = "complete"
        audit_label = "supervisor.completed" if status == "complete" else "supervisor.terminated"
        return ResumeGraphState(stage="done", status=status, audit_trail=[audit_label])

    graph.add_node("bootstrap", bootstrap)
    graph.add_node("ingestion", ingestion_graph)
    graph.add_node("drafting", drafting_graph)
    graph.add_node("critique", critique_graph)
    graph.add_node("compliance", compliance_graph)
    graph.add_node("publishing", publishing_graph)
    graph.add_node("finalize", finalize)

    graph.set_entry_point("bootstrap")
    graph.add_conditional_edges(
        "bootstrap",
        lambda state: state.get("stage", "ingestion"),
        {
            "ingestion": "ingestion",
            "drafting": "drafting",
            "critique": "critique",
            "compliance": "compliance",
            "publishing": "publishing",
            "done": "finalize",
        },
    )
    graph.add_conditional_edges(
        "ingestion",
        lambda state: state.get("stage", "drafting"),
        {
            "drafting": "drafting",
            "done": "finalize",
        },
    )
    graph.add_conditional_edges(
        "drafting",
        lambda state: state.get("stage", "critique"),
        {
            "critique": "critique",
            "compliance": "compliance",
            "publishing": "publishing",
            "done": "finalize",
        },
    )
    graph.add_conditional_edges(
        "critique",
        lambda state: state.get("stage", "compliance"),
        {
            "drafting": "drafting",
            "compliance": "compliance",
        },
    )
    graph.add_conditional_edges(
        "compliance",
        lambda state: state.get("stage", "publishing"),
        {
            "publishing": "publishing",
            "done": "finalize",
        },
    )
    graph.add_edge("publishing", "finalize")
    graph.add_edge("finalize", END)

    return graph


def compile_supervisor_graph(
    registry: Optional[ToolRegistry] = None,
    *,
    config: Optional[AgentConfig] = None,
    checkpointer: Optional[BaseCheckpointSaver] = None,
):
    """Compile the supervisor graph with sensible defaults for registry and config."""

    resolved_registry = registry or build_default_registry()
    resolved_config = config or AgentConfig()
    resolved_checkpointer = checkpointer
    graph = build_supervisor_graph(resolved_registry, resolved_config)
    return graph.compile(checkpointer=resolved_checkpointer)


__all__ = ["build_supervisor_graph", "compile_supervisor_graph"]
