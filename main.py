"""Developer CLI that exercises the Temporal workflow using the test environment."""

from __future__ import annotations

import asyncio
import json
from pprint import pprint

from temporalio import worker
from temporalio.client import Client
from temporalio.testing import WorkflowEnvironment

from app import (
    TASK_QUEUE,
    AgentConfig,
    ResumeWorkflow,
    build_default_registry,
    configure_registry,
    initialize_state,
    list_all_activities,
    summarize_state,
)


def build_sample_state():
    return initialize_state(
        task="resume_pipeline",
        artifacts={
            "raw_documents": {
                "resume": "Principal engineer with deep Temporal expertise.",
                "job": "Architect resilient workflow systems for AI orchestration.",
            },
            "profile": {
                "name": "Sample Candidate",
                "headline": "Principal Workflow Engineer",
                "summary": "Over a decade building production orchestration systems.",
                "skills": ["Temporal", "Python", "LLM orchestration"],
                "experience": [
                    {
                        "role": "Lead Engineer",
                        "company": "Resume Assistant",
                        "impact": "Delivered the Temporal switchover in record time.",
                    }
                ],
                "target_role": "Workflow Engineer",
            },
        },
    )


async def run_demo() -> None:
    registry = configure_registry(build_default_registry())
    state = build_sample_state()
    async with WorkflowEnvironment.start_time_skipping() as env:
        client: Client = env.client
        activities = list_all_activities()
        async with worker.Worker(
            client,
            task_queue=TASK_QUEUE,
            workflows=[ResumeWorkflow],
            activities=activities,
        ):
            handle = await client.start_workflow(
                ResumeWorkflow.run,
                args=[state, AgentConfig()],
                id=state.request_id,
                task_queue=TASK_QUEUE,
            )
            await handle.signal(ResumeWorkflow.submit_human_decision, True)
            result = await handle.result()

    print("\nWorkflow run summary:")
    pprint(summarize_state(result))
    print("\nPublished resume preview:\n")
    print(result.artifacts["published_resume"]["content"])
    print("\nCache entry:")
    print(json.dumps(registry.cache.fetch(result.request_id), indent=2))
    print("\nNotifications:")
    print(json.dumps(registry.notifications.events, indent=2))


if __name__ == "__main__":
    asyncio.run(run_demo())
