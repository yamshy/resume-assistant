"""FastAPI application factory for the resume service."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .agents import MissingIngestionLLMError, ResumeIngestionAgent
from .dependencies import build_dependencies
from .generator import ResumeGenerator
from .ingestion import ResumeIngestor
from .llm import resolve_llm
from .routes.generation import router as generation_router
from .routes.knowledge import router as knowledge_router


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

    dependencies = build_dependencies()

    try:
        ingestion_agent = ResumeIngestionAgent()
    except MissingIngestionLLMError as exc:
        ingestion_agent = None
        ingestor = None
        app.state.resume_ingestion_error = exc
    else:
        ingestor = ResumeIngestor(agent=ingestion_agent)
        app.state.resume_ingestion_error = None
    generator = ResumeGenerator(
        cache=dependencies.cache,
        vector_store=dependencies.vector_store,
        llm=resolve_llm(),
        router=dependencies.router,
        validator=dependencies.validator,
        monitor=dependencies.monitor,
    )

    app.state.embedder = dependencies.embedder
    app.state.vector_store = dependencies.vector_store
    app.state.knowledge_store = dependencies.knowledge_store
    app.state.cache = dependencies.cache
    app.state.router = dependencies.router
    app.state.validator = dependencies.validator
    app.state.monitor = dependencies.monitor
    app.state.generator = generator
    app.state.resume_ingestor = ingestor
    app.state.resume_ingestion_agent = ingestion_agent

    app.include_router(generation_router)
    app.include_router(knowledge_router)

    @app.get("/health")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    return app
