from __future__ import annotations

from typing import Dict

from pydantic import BaseModel, Field
from temporalio import activity

from ..tools import ToolInvocationError
from . import get_registry


class NormalizeDocumentsInput(BaseModel):
    raw_documents: Dict[str, str] = Field(default_factory=dict)


class NormalizeDocumentsResult(BaseModel):
    normalized_documents: Dict[str, str]
    audit_event: str
    metrics: Dict[str, float] = Field(default_factory=dict)
    metadata: Dict[str, object] = Field(default_factory=dict)


class IndexDocumentsInput(BaseModel):
    normalized_documents: Dict[str, str] = Field(default_factory=dict)
    request_id: str


class IndexDocumentsResult(BaseModel):
    vector_index: Dict[str, int | str]
    audit_event: str
    metrics: Dict[str, float] = Field(default_factory=dict)


@activity.defn
async def normalize_documents(payload: NormalizeDocumentsInput) -> NormalizeDocumentsResult:
    """Normalize raw documents prior to ingestion."""

    documents = {key: value for key, value in payload.raw_documents.items() if value}
    if not documents:
        raise ToolInvocationError("raw_documents missing from ingestion payload")
    registry = get_registry()
    try:
        llm_result = registry.llm.ingest_documents(documents)
    except ToolInvocationError:
        raise
    except Exception as exc:  # pragma: no cover - defensive guard around arbitrary tools
        raise ToolInvocationError("Failed to ingest documents with LLM") from exc

    llm_documents = llm_result.get("normalized_documents", {}) if isinstance(llm_result, dict) else {}
    metadata = llm_result.get("metadata", {}) if isinstance(llm_result, dict) else {}
    normalized = {
        key: " ".join(value.strip().split())
        for key, value in llm_documents.items()
        if isinstance(value, str) and value.strip()
    }
    if not normalized:
        raise ToolInvocationError("No documents contained usable content after normalization")
    audit_label = f"ingestion.analyzed:{','.join(sorted(normalized))}"
    metrics = {"documents": float(len(normalized))}
    return NormalizeDocumentsResult(
        normalized_documents=normalized,
        audit_event=audit_label,
        metrics=metrics,
        metadata=metadata if isinstance(metadata, dict) else {},
    )


@activity.defn
async def index_documents(payload: IndexDocumentsInput) -> IndexDocumentsResult:
    """Store normalized documents inside the shared vector index."""

    if not payload.normalized_documents:
        raise ToolInvocationError("normalized_documents missing prior to indexing")
    registry = get_registry()
    result = registry.vector_store.upsert(payload.normalized_documents)
    audit_label = f"ingestion.indexed:{result['upserted']}"
    metrics = {"indexed": float(result["upserted"])} if result["upserted"] else {}
    vector_index: Dict[str, int | str] = {
        "count": int(result["count"]),
        "request_id": payload.request_id,
    }
    return IndexDocumentsResult(
        vector_index=vector_index,
        audit_event=audit_label,
        metrics=metrics,
    )


__all__ = [
    "IndexDocumentsInput",
    "IndexDocumentsResult",
    "NormalizeDocumentsInput",
    "NormalizeDocumentsResult",
    "index_documents",
    "normalize_documents",
]
