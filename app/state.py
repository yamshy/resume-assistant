from __future__ import annotations

from dataclasses import dataclass, field
from typing import Annotated, Any, Dict, List, Literal, Optional, TypedDict
from uuid import uuid4

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.graph.message import add_messages


def _merge_dict(existing: Optional[Dict[str, Any]], new: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    base: Dict[str, Any] = dict(existing or {})
    for key, value in (new or {}).items():
        base[key] = value
    return base


def _extend_list(existing: Optional[List[str]], new: Optional[List[str]]) -> List[str]:
    return list(existing or []) + list(new or [])


def _merge_metrics(existing: Optional[Dict[str, float]], new: Optional[Dict[str, float]]) -> Dict[str, float]:
    base: Dict[str, float] = dict(existing or {})
    for key, value in (new or {}).items():
        base[key] = float(value)
    return base


PipelineStage = Literal[
    "route",
    "ingestion",
    "drafting",
    "critique",
    "revision",
    "compliance",
    "publishing",
    "done",
]

TaskType = Literal[
    "ingest",
    "draft",
    "revise",
    "resume_pipeline",
    "compliance_only",
    "publish",
]


class ResumeGraphState(TypedDict, total=False):
    """LangGraph-compatible state shared across subgraphs."""

    messages: Annotated[List[BaseMessage], add_messages]
    artifacts: Annotated[Dict[str, Any], _merge_dict]
    audit_trail: Annotated[List[str], _extend_list]
    metrics: Annotated[Dict[str, float], _merge_metrics]
    task: TaskType
    stage: PipelineStage
    status: Literal["pending", "in_progress", "complete", "error"]
    request_id: str
    flags: Annotated[Dict[str, Any], _merge_dict]


@dataclass(slots=True)
class AgentConfig:
    """Configuration shared across graphs and tools."""

    default_model: str = "gpt-4o-mini"
    max_revision_loops: int = 2
    compliance_blocklist: tuple[str, ...] = ("confidential", "proprietary")


DEFAULT_AUDIT_EVENT = "graph_initialized"


def initialize_state(
    *,
    task: TaskType,
    messages: Optional[List[BaseMessage]] = None,
    request_id: Optional[str] = None,
    artifacts: Optional[Dict[str, Any]] = None,
    flags: Optional[Dict[str, Any]] = None,
) -> ResumeGraphState:
    """Create a fully-populated state payload for a new graph invocation."""

    resolved_request_id = request_id or str(uuid4())
    initial_messages: List[BaseMessage] = list(messages or [])
    if not initial_messages:
        initial_messages.append(HumanMessage(content="Resume request created."))
    return ResumeGraphState(
        task=task,
        stage="route",
        status="pending",
        request_id=resolved_request_id,
        messages=initial_messages,
        artifacts=dict(artifacts or {}),
        audit_trail=[DEFAULT_AUDIT_EVENT],
        metrics={"revisions": 0.0},
        flags=dict(flags or {}),
    )


def summarize_state(state: ResumeGraphState) -> Dict[str, Any]:
    """Produce a lightweight dict for logging/telemetry in tests."""

    return {
        "task": state.get("task"),
        "stage": state.get("stage"),
        "status": state.get("status"),
        "artifacts": sorted(state.get("artifacts", {}).keys()),
        "metrics": dict(state.get("metrics", {})),
        "audit": list(state.get("audit_trail", [])),
    }


__all__ = [
    "AgentConfig",
    "PipelineStage",
    "ResumeGraphState",
    "TaskType",
    "DEFAULT_AUDIT_EVENT",
    "initialize_state",
    "summarize_state",
]
