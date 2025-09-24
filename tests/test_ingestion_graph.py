from __future__ import annotations

import pytest

from app.graphs.ingestion import build_ingestion_graph
from app.tools import NotificationTool, PublishingCacheTool, ResumeRendererTool, ToolRegistry, VectorSearchTool
from tests.stubs import StubResumeLLM
from app.state import initialize_state
from app.tools import ToolInvocationError


@pytest.fixture()
def ingestion_runner():
    registry = ToolRegistry(
        vector_store=VectorSearchTool(),
        renderer=ResumeRendererTool(),
        cache=PublishingCacheTool(),
        notifications=NotificationTool(),
        llm=StubResumeLLM(),
    )
    graph = build_ingestion_graph(registry)
    return graph.compile()


def test_ingestion_normalizes_and_indexes(ingestion_runner):
    state = initialize_state(
        task="ingest",
        artifacts={"raw_documents": {"resume": " Data Scientist  ", "job": "AI experience "}},
    )
    result = ingestion_runner.invoke(state)
    normalized = result["artifacts"]["normalized_documents"]
    assert normalized["resume"] == "Data Scientist"
    assert result["artifacts"]["vector_index"]["count"] == 2
    assert "ingestion.completed" in result["audit_trail"]


def test_ingestion_requires_documents(ingestion_runner):
    state = initialize_state(task="ingest")
    with pytest.raises(ToolInvocationError):
        ingestion_runner.invoke(state)
