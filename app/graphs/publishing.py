from __future__ import annotations

import hashlib

from langgraph.graph import END, StateGraph

from ..state import ResumeGraphState
from ..tools import ToolRegistry


def build_publishing_graph(registry: ToolRegistry) -> StateGraph:
    """Compile publishing logic that stores resumes and emits notifications."""

    graph = StateGraph(ResumeGraphState)

    def persist_resume(state: ResumeGraphState) -> ResumeGraphState:
        resume_text: str = state.get("artifacts", {}).get("draft_resume", "")  # type: ignore[assignment]
        if not resume_text:
            raise ValueError("draft_resume missing before publishing")
        request_id = state.get("request_id", "unknown")
        checksum = hashlib.sha256(resume_text.encode("utf-8")).hexdigest()
        registry.cache.store(request_id, resume=resume_text, checksum=checksum)
        return ResumeGraphState(
            artifacts={"published_resume": {"checksum": checksum, "content": resume_text}},
            audit_trail=["publishing.stored"],
        )

    def notify(state: ResumeGraphState) -> ResumeGraphState:
        request_id = state.get("request_id", "unknown")
        registry.notifications.publish(
            {
                "status": "delivered",
                "recipient": "operations",
                "message": f"Resume delivery completed for {request_id}",
            }
        )
        return ResumeGraphState(audit_trail=["publishing.notified"], stage="done", status="complete")

    graph.add_node("persist", persist_resume)
    graph.add_node("notify", notify)

    graph.set_entry_point("persist")
    graph.add_edge("persist", "notify")
    graph.add_edge("notify", END)

    return graph


__all__ = ["build_publishing_graph"]
