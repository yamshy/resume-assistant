from __future__ import annotations

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


def test_vector_search_upsert_and_similarity():
    registry = build_registry()
    registry.vector_store.upsert({"doc1": "Python developer with API experience"})
    registry.vector_store.upsert({"doc2": "Project manager with agile delivery"})

    results = registry.vector_store.similarity_search("Python API engineer")
    assert results
    assert results[0]["id"] == "doc1"


def test_resume_renderer_formats_sections():
    registry = build_registry()
    resume = registry.renderer.render(
        {
            "name": "Ada Lovelace",
            "headline": "Computing Pioneer",
            "summary": "Inventive technologist and analyst.",
            "skills": ["Python", "LangGraph"],
            "experience": [
                {"role": "Researcher", "company": "Analytical Engines", "impact": "Built prototypes."}
            ],
        }
    )
    assert "Ada Lovelace" in resume
    assert "LangGraph" in resume
    assert "Analytical Engines" in resume


def test_publishing_cache_store_and_fetch():
    registry = build_registry()
    saved = registry.cache.store("req-1", resume="resume text", checksum="abc123")
    assert saved == {"resume": "resume text", "checksum": "abc123"}
    fetched = registry.cache.fetch("req-1")
    assert fetched == saved


def test_notification_tool_collects_events():
    registry = build_registry()
    registry.notifications.publish({"status": "delivered", "recipient": "qa", "message": "All done"})
    events = registry.notifications.events
    assert events == [
        {"status": "delivered", "recipient": "qa", "message": "All done"}
    ]
