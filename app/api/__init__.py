from __future__ import annotations

import asyncio
import os
from typing import Any, Dict, Optional

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from temporalio.client import Client, WorkflowHandle
from temporalio.common import WorkflowIDReusePolicy

from .. import (
    TASK_QUEUE,
    AgentConfig,
    ResumeWorkflow,
    ResumeWorkflowState,
    initialize_state,
)
from ..state import TaskType

TEMPORAL_HOST = os.getenv("TEMPORAL_HOST", "127.0.0.1:7233")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE", "default")


class StartWorkflowRequest(BaseModel):
    task: TaskType = "resume_pipeline"
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    flags: Dict[str, Any] = Field(default_factory=dict)
    request_id: Optional[str] = None


class StartWorkflowResponse(BaseModel):
    workflow_id: str
    run_id: Optional[str]


class ApprovalRequest(BaseModel):
    approved: bool
    notes: Optional[str] = None


class WorkflowStateResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    state: ResumeWorkflowState


class WorkflowResultResponse(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    state: ResumeWorkflowState


_client_lock = asyncio.Lock()
_cached_client: Client | None = None


async def get_temporal_client() -> Client:
    global _cached_client
    if _cached_client is not None:
        return _cached_client
    async with _client_lock:
        if _cached_client is None:
            _cached_client = await Client.connect(
                TEMPORAL_HOST,
                namespace=TEMPORAL_NAMESPACE,
            )
        return _cached_client


async def get_workflow_handle(workflow_id: str, client: Client) -> WorkflowHandle[Any, ResumeWorkflowState]:
    try:
        return client.get_workflow_handle(workflow_id)
    except Exception as exc:  # pragma: no cover - pass through as HTTP 404
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


app = FastAPI(title="Resume Assistant API")


@app.post("/workflows/resume", response_model=StartWorkflowResponse)
async def start_resume_workflow(
    payload: StartWorkflowRequest,
    client: Client = Depends(get_temporal_client),
) -> StartWorkflowResponse:
    state = initialize_state(
        task=payload.task, request_id=payload.request_id, artifacts=payload.artifacts, flags=payload.flags
    )
    handle = await client.start_workflow(
        ResumeWorkflow.run,
        args=[state, AgentConfig()],
        id=state.request_id,
        task_queue=TASK_QUEUE,
        id_reuse_policy=WorkflowIDReusePolicy.TERMINATE_IF_RUNNING,
    )
    return StartWorkflowResponse(workflow_id=handle.id, run_id=handle.run_id)


@app.get("/workflows/{workflow_id}", response_model=WorkflowStateResponse)
async def get_resume_state(workflow_id: str, client: Client = Depends(get_temporal_client)) -> WorkflowStateResponse:
    handle = await get_workflow_handle(workflow_id, client)
    state = await handle.query(ResumeWorkflow.current_state)
    return WorkflowStateResponse(state=state)


@app.post("/workflows/{workflow_id}/approval", status_code=status.HTTP_202_ACCEPTED)
async def submit_human_approval(
    workflow_id: str,
    payload: ApprovalRequest,
    client: Client = Depends(get_temporal_client),
) -> None:
    handle = await get_workflow_handle(workflow_id, client)
    await handle.signal(
        ResumeWorkflow.submit_human_decision,
        args=[payload.approved, payload.notes],
    )


@app.get("/workflows/{workflow_id}/result", response_model=WorkflowResultResponse)
async def get_workflow_result(workflow_id: str, client: Client = Depends(get_temporal_client)) -> WorkflowResultResponse:
    handle = await get_workflow_handle(workflow_id, client)
    try:
        state = await handle.result()
    except Exception as exc:  # pragma: no cover - propagate failure reason
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    return WorkflowResultResponse(state=state)


__all__ = ["app", "get_temporal_client"]
