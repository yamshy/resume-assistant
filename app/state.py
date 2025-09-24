from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

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


class ResumeMessage(BaseModel):
    """Normalized chat message stored inside the workflow state."""

    role: Literal["human", "assistant", "system"]
    content: str
    model: Optional[str] = None


class ResumeWorkflowState(BaseModel):
    """Serializable workflow state tracked across Temporal executions."""

    task: TaskType
    stage: PipelineStage = "route"
    status: Literal["pending", "in_progress", "complete", "error"] = "pending"
    request_id: str
    messages: List[ResumeMessage] = Field(default_factory=list)
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    audit_trail: List[str] = Field(default_factory=list)
    metrics: Dict[str, float] = Field(default_factory=dict)
    flags: Dict[str, Any] = Field(default_factory=dict)


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
    messages: Optional[List[ResumeMessage]] = None,
    request_id: Optional[str] = None,
    artifacts: Optional[Dict[str, Any]] = None,
    flags: Optional[Dict[str, Any]] = None,
) -> ResumeWorkflowState:
    """Create a fully-populated state payload for a new graph invocation."""

    resolved_request_id = request_id or str(uuid4())
    initial_messages: List[ResumeMessage] = list(messages or [])
    if not initial_messages:
        initial_messages.append(ResumeMessage(role="human", content="Resume request created."))
    return ResumeWorkflowState(
        task=task,
        request_id=resolved_request_id,
        messages=initial_messages,
        artifacts=dict(artifacts or {}),
        audit_trail=[DEFAULT_AUDIT_EVENT],
        metrics={"revisions": 0.0},
        flags=dict(flags or {}),
    )


def summarize_state(state: ResumeWorkflowState) -> Dict[str, Any]:
    """Produce a lightweight dict for logging/telemetry in tests."""

    return {
        "task": state.task,
        "stage": state.stage,
        "status": state.status,
        "artifacts": sorted(state.artifacts.keys()),
        "metrics": dict(state.metrics),
        "audit": list(state.audit_trail),
    }


__all__ = [
    "AgentConfig",
    "PipelineStage",
    "ResumeMessage",
    "ResumeWorkflowState",
    "TaskType",
    "DEFAULT_AUDIT_EVENT",
    "initialize_state",
    "summarize_state",
]
