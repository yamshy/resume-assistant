from __future__ import annotations

import asyncio
import os

from temporalio import worker
from temporalio.client import Client

from app import (
    ResumeWorkflow,
    TASK_QUEUE,
    build_default_registry,
    configure_registry,
    list_all_activities,
)


async def main() -> None:
    configure_registry(build_default_registry())
    client = await Client.connect(
        os.getenv("TEMPORAL_HOST", "127.0.0.1:7233"),
        namespace=os.getenv("TEMPORAL_NAMESPACE", "default"),
    )
    activities = list_all_activities()
    async with worker.Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[ResumeWorkflow],
        activities=activities,
    ):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
