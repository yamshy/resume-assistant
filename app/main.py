"""FastAPI application for the personal resume service with memory."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException

from app.agents import MemoryAgent, ResumeOrchestrator
from app.models import (
    GenerateRequest,
    MemoryApprovalRequest,
    ReviewSubmitRequest,
    StatusResponse,
    TeachInfo,
)
from app.storage import MemoryStorage

app = FastAPI(title="Personal Resume Service with Memory")

storage = MemoryStorage()
memory_agent = MemoryAgent(storage=storage)
orchestrator = ResumeOrchestrator(storage=storage)


@app.post("/generate")
async def generate_resume(payload: GenerateRequest) -> dict[str, Any]:
    """Generate a resume using profile data plus remembered information."""

    profile = storage.load_profile()
    discovered = storage.get_discovered_items()
    preferences = storage.get_preferences()

    result = await orchestrator.generate_with_memory(
        payload.job_posting,
        profile,
        discovered,
        preferences,
    )

    resume_text = result.get("resume_text")
    if resume_text:
        personalized = await memory_agent.apply_learned_preferences(resume_text)
        result["personalized_resume"] = personalized

    conversation = result.get("conversation")
    if conversation:
        discoveries = await memory_agent.analyze_conversation(
            conversation,
            {"profile": profile, "preferences": preferences},
        )
        if discoveries:
            result["new_discoveries"] = discoveries

    return result


@app.get("/memory/discovered")
async def get_discovered_items() -> dict[str, Any]:
    """Return discoveries waiting for approval."""

    return storage.get_discovered_items()


@app.post("/memory/approve")
async def approve_discovered_item(payload: MemoryApprovalRequest) -> dict[str, str]:
    """Promote a discovered item into the permanent profile."""

    try:
        storage.promote_to_profile(payload.item_type, payload.item_id)
    except ValueError as exc:  # pragma: no cover - defensive programming
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"status": f"{payload.item_type} added to profile"}


@app.post("/memory/teach")
async def teach_new_info(payload: TeachInfo) -> dict[str, str]:
    """Allow the user to explicitly teach the system new information."""

    if payload.type == "skill":
        storage.remember_skill(payload.data, "Explicitly taught by user")
    elif payload.type == "experience":
        storage.remember_experience(payload.data, "Explicitly taught by user")
    elif payload.type == "preference":
        if not payload.category:
            raise HTTPException(status_code=422, detail="Preference category is required")
        storage.remember_preference(payload.category, payload.data)
    else:  # pragma: no cover - validated by Pydantic
        raise HTTPException(status_code=400, detail="Unsupported info type")
    return {"status": "learned"}


@app.get("/memory/preferences")
async def get_preferences() -> dict[str, Any]:
    """Expose learned preferences."""

    return storage.get_preferences()


@app.post("/review/submit")
async def submit_review(payload: ReviewSubmitRequest) -> dict[str, Any]:
    """Process review decisions and update memories accordingly."""

    learned = []
    for decision in payload.decisions:
        if decision.original and decision.edited:
            storage.remember_correction(decision.original, decision.edited, decision.context or "Review")
        learning = await memory_agent.learn_from_decision(decision.model_dump())
        learned.append(learning)

    return {"status": "processed", "learned": learned}


@app.get("/export/complete")
async def export_complete_profile() -> dict[str, Any]:
    """Export the full knowledge base including discoveries."""

    return {
        "profile": storage.load_profile(),
        "discovered": storage.get_discovered_items(),
        "preferences": storage.get_preferences(),
        "corrections": storage.get_corrections(),
    }


@app.get("/health", response_model=StatusResponse)
async def health() -> StatusResponse:
    """Primary health-check endpoint for internal tests."""

    return StatusResponse(status="healthy")


@app.get("/api/v1/health", response_model=StatusResponse, include_in_schema=False)
async def legacy_health() -> StatusResponse:
    """Backward-compatible health-check for legacy automation."""

    return StatusResponse(status="healthy")


__all__ = ["app", "storage", "memory_agent", "orchestrator"]
