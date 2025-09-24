import pytest
from temporalio import worker
from temporalio.worker.workflow_sandbox import SandboxedWorkflowRunner, SandboxRestrictions
from temporalio.testing import WorkflowEnvironment

from app import (
    ResumeWorkflow,
    TASK_QUEUE,
    AgentConfig,
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
async def test_resume_workflow_completes():
    registry = ToolRegistry(
        vector_store=VectorSearchTool(),
        renderer=ResumeRendererTool(),
        cache=PublishingCacheTool(),
        notifications=NotificationTool(),
        llm=StubResumeLLM(required_revisions=1),
    )
    configure_registry(registry)

    state = initialize_state(
        task="resume_pipeline",
        artifacts={
            "raw_documents": {"resume": "engineer resume"},
            "profile": {
                "name": "Case",
                "headline": "Developer",
                "target_role": "engineer",
                "skills": ["python"],
                "experience": [
                    {"role": "Developer", "company": "Example", "impact": "Shipped"}
                ],
            },
        },
    )

    env = await WorkflowEnvironment.start_time_skipping()
    try:
        activities = list_all_activities()
        async with worker.Worker(
            env.client,
            task_queue=TASK_QUEUE,
            workflows=[ResumeWorkflow],
            activities=activities,
            workflow_runner=SandboxedWorkflowRunner(
                restrictions=SandboxRestrictions.default.with_passthrough_all_modules()
            ),
        ):
            handle = await env.client.start_workflow(
                ResumeWorkflow.run,
                args=[state, AgentConfig(max_revision_loops=2)],
                id=state.request_id,
                task_queue=TASK_QUEUE,
            )
            await handle.signal(ResumeWorkflow.submit_human_decision, True)
            result = await handle.result()
    finally:
        await env.shutdown()

    assert result.status == "complete"
    assert "published_resume" in result.artifacts
    assert result.flags.get("awaiting_human") is False
