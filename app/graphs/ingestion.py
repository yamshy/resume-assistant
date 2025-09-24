from __future__ import annotations

from typing import Dict

from langgraph.graph import END, StateGraph

from ..state import PipelineStage, ResumeGraphState
from ..tools import ToolInvocationError, ToolRegistry


def build_ingestion_graph(registry: ToolRegistry):
    """Compile the ingestion subgraph responsible for data normalization and indexing."""

    graph = StateGraph(ResumeGraphState)

    def normalize_documents(state: ResumeGraphState) -> ResumeGraphState:
        raw_docs: Dict[str, str] = state.get("artifacts", {}).get("raw_documents", {})  # type: ignore[assignment]
        if not raw_docs:
            raise ToolInvocationError("raw_documents missing from state.artifacts")
        normalized = {key: " ".join(value.strip().split()) for key, value in raw_docs.items() if value}
        if not normalized:
            raise ToolInvocationError("No documents contained usable content after normalization")
        audit_label = f"ingestion.normalized:{','.join(sorted(normalized))}"
        return ResumeGraphState(
            artifacts={"normalized_documents": normalized},
            audit_trail=[audit_label],
            metrics={"documents": float(len(normalized))},
            status="in_progress",
        )

    def index_documents(state: ResumeGraphState) -> ResumeGraphState:
        normalized: Dict[str, str] = state.get("artifacts", {}).get("normalized_documents", {})  # type: ignore[assignment]
        if not normalized:
            raise ToolInvocationError("normalized_documents missing prior to indexing")
        result = registry.vector_store.upsert(normalized)
        audit_label = f"ingestion.indexed:{result['upserted']}"
        return ResumeGraphState(
            artifacts={"vector_index": {"count": result["count"]}},
            audit_trail=[audit_label],
            metrics={"indexed": float(result["upserted"])}
            if result["upserted"]
            else {},
        )

    def finalize_ingestion(state: ResumeGraphState) -> ResumeGraphState:
        next_stage: PipelineStage = "drafting" if state.get("task") in {"resume_pipeline", "draft", "revise"} else "done"
        return ResumeGraphState(audit_trail=["ingestion.completed"], stage=next_stage)

    graph.add_node("normalize", normalize_documents)
    graph.add_node("index", index_documents)
    graph.add_node("finalize", finalize_ingestion)

    graph.set_entry_point("normalize")
    graph.add_edge("normalize", "index")
    graph.add_edge("index", "finalize")
    graph.add_edge("finalize", END)

    return graph


__all__ = ["build_ingestion_graph"]
