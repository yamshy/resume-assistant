"""Routes related to resume generation and validation."""

from __future__ import annotations

import re
from typing import Any, Dict, Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel, Field

from app.models import Resume

router = APIRouter()


class GenerateRequest(BaseModel):
    job_posting: str = Field(..., min_length=10)
    profile: Dict[str, Any] | None = None


class ValidateRequest(BaseModel):
    resume_text: str = Field(..., min_length=50)


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(..., min_length=1)
    metadata: Dict[str, Any] | None = None


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(..., min_length=1)
    session: Dict[str, Any] | None = None


class ChatResponse(BaseModel):
    reply: ChatMessage
    session: Dict[str, Any]


@router.post("/chat", response_model=ChatResponse)
async def chat_turn(payload: ChatRequest, request: Request) -> ChatResponse:
    """Return a grounded chat response using the resume generator."""

    generator = request.app.state.generator
    reply_payload, session_state = await generator.chat(
        [message.model_dump() for message in payload.messages],
        payload.session,
    )
    reply = ChatMessage(**reply_payload)
    return ChatResponse(reply=reply, session=session_state)


@router.post("/generate", response_model=Resume)
async def generate_resume(
    payload: GenerateRequest,
    background_tasks: BackgroundTasks,
    request: Request,
) -> Resume:
    """Generate a resume tailored to a job posting."""

    generator = request.app.state.generator
    knowledge_store = request.app.state.knowledge_store

    profile = payload.profile or knowledge_store.aggregated_profile()
    if not profile:
        raise HTTPException(
            status_code=400,
            detail=(
                "Profile data is required. Upload resumes to the knowledge base or "
                "include a profile payload with the request."
            ),
        )

    resume = await generator.generate(payload.job_posting, profile)
    resume.metadata.setdefault(
        "profile_source",
        "payload" if payload.profile else "knowledge-base",
    )
    tokens_value = resume.metadata.get("tokens", 0)
    tokens = int(tokens_value) if isinstance(tokens_value, (int, float)) else 0
    latency = float(resume.metadata.get("latency", 0) or 0)
    background_tasks.add_task(
        generator.monitor.track_generation,
        model=resume.metadata.get("model", "unknown"),
        tokens_used=tokens,
        generation_time=latency,
        confidence=resume.confidence_scores.get("overall", 0.0),
        cache_hit=bool(resume.metadata.get("cached")),
    )
    return resume


@router.post("/validate")
async def validate_resume(payload: ValidateRequest) -> Dict[str, float]:
    """Return heuristic quality scores for a resume."""

    text = payload.resume_text
    return {
        "ats_compatibility": check_ats_parsing(text),
        "keyword_density": calculate_keyword_density(text),
        "readability": calculate_readability_score(text),
    }


def check_ats_parsing(resume_text: str) -> float:
    """Estimate whether a resume will parse correctly in common ATS systems."""

    email = bool(re.search(r"[\w\.-]+@[\w\.-]+", resume_text))
    phone = bool(re.search(r"\+?\d[\d\s\-]{6,}\d", resume_text))
    sections = len(re.findall(r"(?im)^(summary|skills|education|experience)", resume_text))
    achievements = len(re.findall(r"(?m)^(?:- |•)", resume_text))
    signals = [email, phone, sections >= 3, achievements >= 3]
    return sum(signals) / len(signals)


def calculate_keyword_density(text: str) -> float:
    """Calculate how many unique keywords appear in the resume."""

    words = [word.lower() for word in re.findall(r"[A-Za-z]+", text)]
    if not words:
        return 0.0
    unique = set(words)
    return len(unique) / len(words)


def calculate_readability_score(text: str) -> float:
    """Return a Flesch-style readability score for the resume text."""

    sentences = max(1, len(re.findall(r"[.!?]", text)))
    words = re.findall(r"[A-Za-z]+", text)
    if not words:
        return 0.0
    syllables = sum(_estimate_syllables(word) for word in words)
    words_count = len(words)
    return 206.835 - 1.015 * (words_count / sentences) - 84.6 * (syllables / words_count)


def _estimate_syllables(word: str) -> int:
    vowels = "aeiouy"
    lowered = word.lower()
    count = 0
    prev_char_was_vowel = False
    for char in lowered:
        is_vowel = char in vowels
        if is_vowel and not prev_char_was_vowel:
            count += 1
        prev_char_was_vowel = is_vowel
    if lowered.endswith("e") and count > 1:
        count -= 1
    return max(1, count)
