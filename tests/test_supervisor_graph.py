from __future__ import annotations

from app import AgentConfig, build_supervisor, initialize_state
from app.tools import (
    NotificationTool,
    PublishingCacheTool,
    ResumeRendererTool,
    ToolRegistry,
    VectorSearchTool,
)
from tests.stubs import StubResumeLLM


def build_initial_artifacts(summary: str) -> dict:
    return {
        "raw_documents": {
            "resume": "Experienced engineer skilled in Python and LangGraph.",
            "job": "Seeking LangGraph expert to build reliable agents.",
        },
        "profile": {
            "name": "Jordan Applicant",
            "headline": "Senior AI Engineer",
            "summary": summary,
            "skills": ["Python", "LangGraph", "FastAPI"],
            "experience": [
                {
                    "role": "Lead Engineer",
                    "company": "Resume Assistant",
                    "impact": "Delivered agentic workflow improvements",
                }
            ],
            "target_role": "LangGraph Engineer",
        },
    }


def build_registry(required_revisions: int = 0) -> ToolRegistry:
    return ToolRegistry(
        vector_store=VectorSearchTool(),
        renderer=ResumeRendererTool(),
        cache=PublishingCacheTool(),
        notifications=NotificationTool(),
        llm=StubResumeLLM(required_revisions=required_revisions),
    )


def test_supervisor_pipeline_completes_and_publishes():
    registry = build_registry()
    config = AgentConfig()
    supervisor = build_supervisor(registry=registry, config=config)
    initial_state = initialize_state(
        task="resume_pipeline",
        artifacts=build_initial_artifacts(
            "Shipped production-grade AI resume assistants leveraging LangGraph orchestration."
        ),
    )
    result = supervisor.invoke(initial_state, config={"configurable": {"thread_id": initial_state["request_id"]}})

    assert result["status"] == "complete"
    assert "published_resume" in result["artifacts"]
    cached = registry.cache.fetch(result["request_id"])
    assert cached["checksum"] == result["artifacts"]["published_resume"]["checksum"]
    assert registry.notifications.events[-1]["status"] == "delivered"
    assert result["metrics"]["drafts"] == 1.0


def test_supervisor_respects_revision_limits():
    registry = build_registry(required_revisions=1)
    config = AgentConfig(max_revision_loops=1)
    supervisor = build_supervisor(registry=registry, config=config)
    initial_state = initialize_state(
        task="resume_pipeline",
        artifacts=build_initial_artifacts("Short summary"),
    )
    result = supervisor.invoke(initial_state, config={"configurable": {"thread_id": initial_state["request_id"]}})

    assert result["metrics"]["revisions"] == 1.0
    assert result["metrics"]["drafts"] == 2.0
    assert result["stage"] == "done"
    assert result["status"] == "complete"
