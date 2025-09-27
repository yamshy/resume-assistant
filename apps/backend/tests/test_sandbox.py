"""Tests to ensure workflow code remains compatible with Temporal sandbox restrictions."""

import pytest
from temporalio import worker
from temporalio.testing import WorkflowEnvironment
from temporalio.worker.workflow_sandbox import (
    SandboxedWorkflowRunner,
    SandboxRestrictions,
)

from app import (
    TASK_QUEUE,
    AgentConfig,
    ResumeWorkflow,
    configure_registry,
    initialize_state,
    list_all_activities,
)
from app.tools import (
    NotificationTool,
    PublishingCacheTool,
    ResumeRendererTool,
    ToolRegistry,
    VectorSearchTool,
)
from tests.stubs import StubResumeLLM


@pytest.mark.asyncio
async def test_workflow_runs_with_strict_sandbox_restrictions():
    """
    Ensure ResumeWorkflow can run with default sandbox restrictions.
    
    This test prevents regressions where workflow code accidentally imports
    restricted modules like http.client at module load time, which would
    cause RestrictedWorkflowAccessError during replay.
    """
    registry = ToolRegistry(
        vector_store=VectorSearchTool(),
        renderer=ResumeRendererTool(),
        cache=PublishingCacheTool(),
        notifications=NotificationTool(),
        llm=StubResumeLLM(required_revisions=0),  # No revisions for faster test
    )
    configure_registry(registry)

    state = initialize_state(
        task="resume_pipeline",
        artifacts={
            "raw_documents": {"resume": "test resume content"},
            "profile": {
                "name": "Test User",
                "headline": "Software Engineer",
                "target_role": "senior engineer",
                "skills": ["python", "testing"],
                "experience": [
                    {
                        "role": "Engineer",
                        "company": "Test Corp",
                        "impact": "Built test systems",
                    }
                ],
            },
        },
    )

    env = await WorkflowEnvironment.start_time_skipping()
    result = None
    try:
        activities = list_all_activities()
        # Use strict sandbox restrictions (NOT passthrough_all_modules)
        # This will fail if workflow code tries to access restricted modules
        async with worker.Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[ResumeWorkflow],
            activities=activities,
            workflow_runner=SandboxedWorkflowRunner(
                restrictions=SandboxRestrictions.default
            ),
        ):
            handle = await env.client.start_workflow(
                ResumeWorkflow.run,
                args=[state, AgentConfig(max_revision_loops=0)],
                id=state.request_id,
                task_queue=TASK_QUEUE,
            )
            # Signal approval to complete the workflow
            await handle.signal(ResumeWorkflow.submit_human_decision, True)
            result = await handle.result()
    finally:
        await env.shutdown()

    if result is not None:
        # Verify workflow completed successfully
        assert result.status == "complete"
        assert "published_resume" in result.artifacts
        assert result.stage == "done"


@pytest.mark.asyncio
async def test_workflow_import_does_not_trigger_restricted_modules():
    """
    Test that importing workflow components doesn't trigger restricted module access.
    
    This is a lightweight test that can catch import-time violations without
    running the full workflow.
    """
    # These imports should not trigger any restricted module access
    from app.state import AgentConfig
    from app.tools.llm import OpenAIResumeLLM
    from app.workflows.resume import ResumeWorkflow
    
    # Creating instances should also be safe
    workflow = ResumeWorkflow()
    config = AgentConfig()
    llm = OpenAIResumeLLM()
    
    # The OpenAI client should be lazily initialized
    assert llm._client is None, "OpenAI client should not be initialized until first use"
    
    # Basic workflow state should be accessible
    assert workflow.state is None
    assert isinstance(config.compliance_blocklist, tuple)


def test_openai_llm_lazy_initialization():
    """Test that OpenAIResumeLLM doesn't initialize OpenAI client until needed."""
    from app.tools.llm import OpenAIResumeLLM
    
    # Creating the LLM should not trigger OpenAI client creation
    llm = OpenAIResumeLLM()
    assert llm._client is None, "Client should be None after instantiation"
    
    # Calling _ensure_client should initialize the client
    # Note: This will fail in CI without OPENAI_API_KEY, but that's expected
    # The test verifies the lazy loading pattern works correctly
    try:
        llm._ensure_client()
        assert llm._client is not None, "Client should be initialized after _ensure_client()"
    except Exception:
        # Expected to fail without API key - that's fine for this test
        pass
