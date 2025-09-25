from __future__ import annotations

import hashlib
from typing import Dict

from pydantic import BaseModel
from temporalio import activity

from . import get_registry


class PersistResumeInput(BaseModel):
    resume_markdown: str
    request_id: str


class PersistResumeResult(BaseModel):
    artifact: Dict[str, str]
    audit_event: str


class NotifyInput(BaseModel):
    request_id: str


class NotifyResult(BaseModel):
    audit_event: str


@activity.defn
async def persist_resume(payload: PersistResumeInput) -> PersistResumeResult:
    if not payload.resume_markdown:
        raise ValueError("draft_resume missing before publishing")
    registry = get_registry()
    checksum = hashlib.sha256(payload.resume_markdown.encode("utf-8")).hexdigest()
    registry.cache.store(payload.request_id, resume=payload.resume_markdown, checksum=checksum)
    artifact = {"checksum": checksum, "content": payload.resume_markdown}
    return PersistResumeResult(artifact=artifact, audit_event="publishing.stored")


@activity.defn
async def notify_operations(payload: NotifyInput) -> NotifyResult:
    registry = get_registry()
    registry.notifications.publish(
        {
            "status": "delivered",
            "recipient": "operations",
            "message": f"Resume delivery completed for {payload.request_id}",
        }
    )
    return NotifyResult(audit_event="publishing.notified")


__all__ = [
    "NotifyInput",
    "NotifyResult",
    "PersistResumeInput",
    "PersistResumeResult",
    "notify_operations",
    "persist_resume",
]
