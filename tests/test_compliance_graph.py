from __future__ import annotations

from app.graphs.compliance import build_compliance_graph
from app.state import AgentConfig, initialize_state
from app.tools import NotificationTool, PublishingCacheTool, ResumeRendererTool, ToolRegistry, VectorSearchTool
from tests.stubs import StubResumeLLM


def build_registry() -> ToolRegistry:
    return ToolRegistry(
        vector_store=VectorSearchTool(),
        renderer=ResumeRendererTool(),
        cache=PublishingCacheTool(),
        notifications=NotificationTool(),
        llm=StubResumeLLM(),
    )


def test_compliance_rejects_blocked_terms():
    registry = build_registry()
    config = AgentConfig(compliance_blocklist=("restricted",))
    graph = build_compliance_graph(registry, config).compile()
    state = initialize_state(
        task="compliance_only",
        artifacts={"draft_resume": "This resume contains restricted data."},
    )
    result = graph.invoke(state)
    assert result["status"] == "error"
    assert result["stage"] == "done"
    assert result["artifacts"]["compliance_report"]["status"] == "rejected"


def test_compliance_allows_clean_resumes():
    registry = build_registry()
    config = AgentConfig(compliance_blocklist=("restricted",))
    graph = build_compliance_graph(registry, config).compile()
    state = initialize_state(
        task="compliance_only",
        artifacts={"draft_resume": "Clean resume with compliant content."},
    )
    result = graph.invoke(state)
    assert result["stage"] == "publishing"
    assert result["artifacts"]["compliance_report"]["status"] == "approved"
