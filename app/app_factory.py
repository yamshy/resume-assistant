"""FastAPI application factory for the resume service."""

from __future__ import annotations

import os
import re
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Literal, Sequence

from fastapi import BackgroundTasks, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

redis_async: ModuleType | None

try:  # pragma: no cover - optional for tests
    import redis.asyncio as redis_async_module
except Exception:  # pragma: no cover
    redis_async = None
else:
    redis_async = redis_async_module

from .cache import SemanticCache
from .embeddings import SemanticEmbedder
from .generator import ResumeGenerator
from .llm import resolve_llm
from .memory import InMemoryRedis
from .models import Resume
from .monitoring import ResumeMonitor
from .router import ModelRouter
from .validator import ClaimValidator
from .vectorstore import VectorDocument, VectorStore


class GenerateRequest(BaseModel):
    job_posting: str = Field(..., min_length=10)
    profile: Dict[str, Any]


class ValidateRequest(BaseModel):
    resume_text: str = Field(..., min_length=50)


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str = Field(..., min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    history: list[ChatMessage]


class KnowledgeDocument(BaseModel):
    content: str = Field(..., min_length=10, max_length=4000)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeIngestRequest(BaseModel):
    documents: list[KnowledgeDocument] = Field(..., min_length=1, max_length=50)


def create_app() -> FastAPI:
    app = FastAPI(title="AI Resume Service", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    frontend_dir = Path(__file__).resolve().parent / "frontend"
    if frontend_dir.exists():
        app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

        @app.get("/", include_in_schema=False)
        async def serve_frontend() -> FileResponse:
            return FileResponse(frontend_dir / "index.html")

    embedder = SemanticEmbedder()
    vector_store = VectorStore(embedder)
    vector_store.add_documents(
        [
            VectorDocument(
                content="Emphasise measurable achievements, cloud infrastructure and leadership in resumes.",
                metadata={"source": "playbook"},
            ),
            VectorDocument(
                content="Tailor the professional summary to the job posting while staying truthful to the profile.",
                metadata={"source": "guidelines"},
            ),
            VectorDocument(
                content=(
                    "Reference process improvements such as adopting Conventional Commits and automated releases "
                    "when they demonstrate engineering rigor."
                ),
                metadata={"source": "workflow"},
            ),
        ]
    )

    redis_client = _create_redis()
    cache = SemanticCache(redis_client, embedder) if redis_client else None

    router = ModelRouter()
    validator = ClaimValidator(embedder)
    monitor = ResumeMonitor()
    generator = ResumeGenerator(
        cache=cache,
        vector_store=vector_store,
        llm=resolve_llm(),
        router=router,
        validator=validator,
        monitor=monitor,
    )
    app.state.generator = generator
    app.state.vector_store = vector_store

    @app.post("/generate", response_model=Resume)
    async def generate_resume(request: GenerateRequest, background_tasks: BackgroundTasks) -> Resume:
        resume = await generator.generate(request.job_posting, request.profile)
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

    @app.post("/validate")
    async def validate_resume(request: ValidateRequest) -> Dict[str, float]:
        text = request.resume_text
        return {
            "ats_compatibility": check_ats_parsing(text),
            "keyword_density": calculate_keyword_density(text),
            "readability": calculate_readability_score(text),
        }

    @app.post("/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest) -> ChatResponse:
        conversation = list(request.history)
        conversation.append(ChatMessage(role="user", content=request.message))
        reply = build_chat_reply(request.message, conversation)
        conversation.append(ChatMessage(role="assistant", content=reply))
        return ChatResponse(reply=reply, history=conversation)

    @app.post("/knowledge", status_code=201)
    async def ingest_knowledge(request: KnowledgeIngestRequest) -> Dict[str, int]:
        documents = [
            VectorDocument(content=doc.content, metadata=dict(doc.metadata))
            for doc in request.documents
        ]
        vector_store.add_documents(documents)
        return {"ingested": len(documents)}

    @app.get("/health")
    async def healthcheck() -> Dict[str, str]:
        return {"status": "ok"}

    return app


def _create_redis():
    url = os.getenv("REDIS_URL")
    if url and redis_async is not None:
        return redis_async.from_url(url, decode_responses=True)
    return InMemoryRedis()


def check_ats_parsing(resume_text: str) -> float:
    email = bool(re.search(r"[\w\.-]+@[\w\.-]+", resume_text))
    phone = bool(re.search(r"\+?\d[\d\s\-]{6,}\d", resume_text))
    sections = len(re.findall(r"(?im)^(summary|skills|education|experience)", resume_text))
    achievements = len(re.findall(r"(?m)^(?:- |•)", resume_text))
    signals = [email, phone, sections >= 3, achievements >= 3]
    return sum(signals) / len(signals)


def calculate_keyword_density(text: str) -> float:
    words = [word.lower() for word in re.findall(r"[A-Za-z]+", text)]
    if not words:
        return 0.0
    unique = set(words)
    return len(unique) / len(words)


def calculate_readability_score(text: str) -> float:
    sentences = max(1, len(re.findall(r"[.!?]", text)))
    words = re.findall(r"[A-Za-z]+", text)
    if not words:
        return 0.0
    syllables = sum(_estimate_syllables(word) for word in words)
    words_count = len(words)
    return 206.835 - 1.015 * (words_count / sentences) - 84.6 * (syllables / words_count)


def _estimate_syllables(word: str) -> int:
    vowels = "aeiouy"
    word = word.lower()
    count = 0
    prev_char_was_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_char_was_vowel:
            count += 1
        prev_char_was_vowel = is_vowel
    if word.endswith("e") and count > 1:
        count -= 1
    return max(1, count)


def build_chat_reply(message: str, history: Sequence[ChatMessage]) -> str:
    message_lower = message.lower()
    suggestions: list[str] = []

    if "summary" in message_lower:
        suggestions.append(
            "Open with a two sentence summary that mirrors the title and two top requirements from the job posting."
        )
    if "skill" in message_lower or "technology" in message_lower:
        suggestions.append("Group skills by theme (cloud, programming, tooling) and emphasise those asked for in the role.")
    if "experience" in message_lower or "achievement" in message_lower:
        suggestions.append(
            "Frame each achievement around impact: start with the action you took, quantify the result, and mention the platform."
        )
    if "job" in message_lower or "posting" in message_lower or len(message.split()) > 80:
        suggestions.append(
            "Highlight the three most important responsibilities from the posting and echo them in your summary and top bullets."
        )
    if "thank" in message_lower:
        suggestions.append("Happy to help! Feel free to share another role or ask for validation tips whenever you need them.")

    if not suggestions:
        suggestions.extend(
            [
                "Share the job posting plus a quick summary of your experience and I'll outline how to position the resume.",
                "When you're ready for a draft, call the /generate endpoint with your profile details for a structured resume.",
                "Use /validate to score an existing resume for ATS compatibility, keyword coverage, and readability before submitting.",
            ]
        )

    bullet_lines = "\n".join(f"- {tip}" for tip in suggestions)
    last_user = next((entry.content for entry in reversed(history) if entry.role == "user"), None)

    acknowledgement = "Thanks for the update!"
    if last_user:
        acknowledgement = f"Thanks for sharing that context about '{last_user[:80]}'."

    return (
        f"{acknowledgement} Here's how you can move forward:\n"
        f"{bullet_lines}\n"
        "Let me know if you'd like me to focus on specific sections or prepare a bullet draft."
    )
