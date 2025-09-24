import pytest

from app.activities import configure_registry
from app.activities.compliance import ComplianceInput, run_compliance_check
from app.activities.critique import CritiqueInput, run_critique
from app.activities.drafting import (
    PlanResumeInput,
    RenderResumeInput,
    plan_resume,
    render_resume,
)
from app.activities.ingestion import (
    IndexDocumentsInput,
    NormalizeDocumentsInput,
    index_documents,
    normalize_documents,
)
from app.activities.publishing import (
    NotifyInput,
    PersistResumeInput,
    notify_operations,
    persist_resume,
)
from app.state import AgentConfig
from app.tools import (
    NotificationTool,
    PublishingCacheTool,
    ResumeRendererTool,
    ToolRegistry,
    VectorSearchTool,
)
from tests.stubs import StubResumeLLM


@pytest.fixture(autouse=True)
def configure_stub_registry():
    registry = ToolRegistry(
        vector_store=VectorSearchTool(),
        renderer=ResumeRendererTool(),
        cache=PublishingCacheTool(),
        notifications=NotificationTool(),
        llm=StubResumeLLM(required_revisions=1),
    )
    configure_registry(registry)
    return registry


@pytest.mark.asyncio
async def test_ingestion_flow(configure_stub_registry):
    normalize_result = await normalize_documents(
        NormalizeDocumentsInput(raw_documents={"resume": " First  value ", "job": " value"})
    )
    assert normalize_result.normalized_documents["resume"] == "First value"
    assert normalize_result.metrics == {"documents": 2.0}

    index_result = await index_documents(
        IndexDocumentsInput(
            normalized_documents=normalize_result.normalized_documents,
            request_id="req-123",
        )
    )
    assert index_result.vector_index["count"] == 2
    assert index_result.metrics == {"indexed": 2.0}


@pytest.mark.asyncio
async def test_drafting_and_render(configure_stub_registry):
    await normalize_documents(NormalizeDocumentsInput(raw_documents={"resume": "engineer"}))
    await index_documents(
        IndexDocumentsInput(
            normalized_documents={"resume": "engineer"},
            request_id="req-1",
        )
    )
    profile = {"name": "Case", "headline": "Developer", "target_role": "engineer"}
    plan = await plan_resume(PlanResumeInput(profile=profile, request_id="req-1", config=AgentConfig()))
    assert plan.draft_plan["headline"] == "Developer"

    render = await render_resume(
        RenderResumeInput(
            plan=plan.draft_plan,
            profile=profile,
            knowledge_hits=plan.knowledge_hits,
            config=AgentConfig(),
            previous_drafts=0.0,
        )
    )
    assert "# Case" in render.resume_markdown
    assert render.metrics["drafts"] == 1.0


@pytest.mark.asyncio
async def test_critique_requests_revision(configure_stub_registry):
    result = await run_critique(
        CritiqueInput(
            resume_markdown="content",
            profile={"name": "Case"},
            revision_count=0,
            config=AgentConfig(max_revision_loops=2),
        )
    )
    assert result.needs_revision is True
    assert result.revision_count == 1


@pytest.mark.asyncio
async def test_compliance_allows_resume(configure_stub_registry):
    result = await run_compliance_check(
        ComplianceInput(
            resume_markdown="This text is clean",
            profile={"name": "Case"},
            config=AgentConfig(),
        )
    )
    assert result.status == "approved"


@pytest.mark.asyncio
async def test_publishing_persists_and_notifies(configure_stub_registry):
    persist = await persist_resume(
        PersistResumeInput(resume_markdown="content", request_id="abc")
    )
    assert persist.artifact["checksum"]

    await notify_operations(NotifyInput(request_id="abc"))
    assert configure_stub_registry.notifications.events
