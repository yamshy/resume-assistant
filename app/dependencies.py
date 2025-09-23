"""Dependency construction helpers for the FastAPI application."""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from .cache import SemanticCache
from .embeddings import SemanticEmbedder
from .knowledge_store import KnowledgeStore
from .memory import InMemoryRedis
from .monitoring import ResumeMonitor
from .router import ModelRouter
from .validator import ClaimValidator
from .vectorstore import VectorDocument, VectorStore

redis_async: ModuleType | None

try:  # pragma: no cover - optional for tests
    import redis.asyncio as redis_async_module
except Exception:  # pragma: no cover
    redis_async = None
else:
    redis_async = redis_async_module


@dataclass(slots=True)
class AppDependencies:
    """Container object holding the core app services."""

    embedder: SemanticEmbedder
    vector_store: VectorStore
    knowledge_store: KnowledgeStore
    cache: SemanticCache | None
    router: ModelRouter
    validator: ClaimValidator
    monitor: ResumeMonitor


def build_dependencies() -> AppDependencies:
    """Instantiate core dependencies and seed shared resources."""

    embedder = SemanticEmbedder()
    vector_store = VectorStore(embedder)
    seed_vector_store(vector_store)

    knowledge_store = KnowledgeStore(resolve_knowledge_store_path())

    redis_client = create_redis()
    cache = SemanticCache(redis_client, embedder) if redis_client else None

    router = ModelRouter()
    validator = ClaimValidator(embedder)
    monitor = ResumeMonitor()

    return AppDependencies(
        embedder=embedder,
        vector_store=vector_store,
        knowledge_store=knowledge_store,
        cache=cache,
        router=router,
        validator=validator,
        monitor=monitor,
    )


def resolve_knowledge_store_path() -> Path:
    """Resolve the filesystem path backing the knowledge store."""

    env_path = os.getenv("KNOWLEDGE_STORE_PATH")
    if env_path:
        return Path(env_path)

    storage_root = Path(tempfile.gettempdir()) / "resume-assistant"
    storage_root.mkdir(parents=True, exist_ok=True)
    return storage_root / "knowledge_store.json"


def seed_vector_store(vector_store: VectorStore) -> None:
    """Populate the vector store with default guidance documents."""

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


def create_redis():
    """Create a redis-compatible client, defaulting to an in-memory fallback."""

    url = os.getenv("REDIS_URL")
    if url and redis_async is not None:
        return redis_async.from_url(url, decode_responses=True)
    return InMemoryRedis()


__all__ = [
    "AppDependencies",
    "build_dependencies",
    "create_redis",
    "resolve_knowledge_store_path",
    "seed_vector_store",
]
