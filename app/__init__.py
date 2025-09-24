from __future__ import annotations

from langgraph.checkpoint.base import BaseCheckpointSaver

from .graphs.supervisor import compile_supervisor_graph
from .state import AgentConfig, ResumeGraphState, initialize_state, summarize_state
from .tools import ToolRegistry, build_default_registry


def build_supervisor(
    *,
    registry: ToolRegistry | None = None,
    config: AgentConfig | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
):
    """Return a compiled LangGraph supervisor runnable for external callers."""

    return compile_supervisor_graph(registry, config=config, checkpointer=checkpointer)


__all__ = [
    "AgentConfig",
    "ResumeGraphState",
    "ToolRegistry",
    "build_default_registry",
    "build_supervisor",
    "initialize_state",
    "summarize_state",
]
