"""FastAPI application factory for the resume service."""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Literal

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
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
from .ingestion import ResumeIngestor
from .knowledge_store import KnowledgeStore
from .llm import resolve_llm
from .memory import InMemoryRedis
from .models import Resume
from .monitoring import ResumeMonitor
from .router import ModelRouter
from .validator import ClaimValidator
from .vectorstore import VectorDocument, VectorStore


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

    knowledge_store = KnowledgeStore(_resolve_knowledge_store_path())
    ingestor = ResumeIngestor()

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
    app.state.knowledge_store = knowledge_store
    app.state.resume_ingestor = ingestor

    @app.post("/chat", response_model=ChatResponse)
    async def chat_turn(request: ChatRequest) -> ChatResponse:
        reply_payload, session_state = await generator.chat(
            [message.model_dump() for message in request.messages],
            request.session,
        )
        reply = ChatMessage(**reply_payload)
        return ChatResponse(reply=reply, session=session_state)

    @app.post("/generate", response_model=Resume)
    async def generate_resume(request: GenerateRequest, background_tasks: BackgroundTasks) -> Resume:
        profile = request.profile or knowledge_store.aggregated_profile()
        if not profile:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Profile data is required. Upload resumes to the knowledge base or "
                    "include a profile payload with the request."
                ),
            )

        resume = await generator.generate(request.job_posting, profile)
        resume.metadata.setdefault("profile_source", "payload" if request.profile else "knowledge-base")
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

    @app.post("/knowledge", status_code=201)
    async def ingest_knowledge(
        resumes: list[UploadFile] = File(..., description="Resume files to ingest"),
        notes: str = Form(default=""),
    ) -> Dict[str, Any]:
        if not resumes:
            raise HTTPException(status_code=400, detail="At least one resume file is required.")

        payloads: list[tuple[str, str]] = []
        for upload in resumes:
            raw_bytes = await upload.read()
            await upload.close()
            text = raw_bytes.decode("utf-8", errors="ignore").strip()
            if text:
                payloads.append((upload.filename or "resume.txt", text))

        if not payloads:
            raise HTTPException(
                status_code=400,
                detail="Uploaded resumes were empty or unreadable.",
            )

        parsed_resumes = [ingestor.parse(name, body, notes) for name, body in payloads]
        store_result = knowledge_store.add_resumes(parsed_resumes)

        documents: list[VectorDocument] = []
        for parsed in parsed_resumes:
            for experience in parsed.experiences:
                for achievement in experience.achievements:
                    clean = achievement.strip()
                    if not clean:
                        continue
                    documents.append(
                        VectorDocument(
                            content=clean,
                            metadata={
                                "source": parsed.source,
                                "company": experience.company,
                                "role": experience.role,
                                "type": "achievement",
                            },
                        )
                    )
            for skill in parsed.skills:
                documents.append(
                    VectorDocument(
                        content=skill,
                        metadata={"source": parsed.source, "type": "skill"},
                    )
                )

        if documents:
            vector_store.add_documents(documents)

        summary_text = _build_ingestion_summary(
            len(parsed_resumes),
            store_result.get("skills_added", []),
            store_result.get("achievements_indexed", 0),
        )

        return {
            "ingested": len(parsed_resumes),
            "skills_indexed": store_result.get("skills_added", []),
            "achievements_indexed": store_result.get("achievements_indexed", 0),
            "summary": summary_text,
            "profile_snapshot": store_result.get("profile_snapshot", {}),
        }

    @app.get("/health")
    async def healthcheck() -> Dict[str, str]:
        return {"status": "ok"}

    return app


def _resolve_knowledge_store_path() -> Path:
    env_path = os.getenv("KNOWLEDGE_STORE_PATH")
    if env_path:
        return Path(env_path)
    storage_root = Path(tempfile.gettempdir()) / "resume-assistant"
    storage_root.mkdir(parents=True, exist_ok=True)
    return storage_root / "knowledge_store.json"


def _build_ingestion_summary(count: int, skills: list[str], achievements: int) -> str:
    resume_phrase = f"{count} resume{'s' if count != 1 else ''}"
    achievements_phrase = f"{achievements} achievement{'s' if achievements != 1 else ''}"
    if skills:
        preview = ", ".join(skills[:5])
        skills_phrase = f"{len(skills)} new skill{'s' if len(skills) != 1 else ''}"
        if preview:
            skills_phrase += f" ({preview})"
    else:
        skills_phrase = "no new skills"
    return (
        f"Ingested {resume_phrase} and indexed {achievements_phrase} while capturing {skills_phrase}."
    )


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

