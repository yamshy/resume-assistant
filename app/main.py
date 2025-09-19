from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app

from app.api.v1 import generation, ingestion, verification
from app.config import get_settings
from app.core.cache import close_cache, init_cache
from app.core.database import close_db, init_db

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("startup.begin", env=settings.app_env)
    await init_db()
    await init_cache()
    logger.info("startup.complete")
    yield
    logger.info("shutdown.begin")
    await close_db()
    await close_cache()
    logger.info("shutdown.complete")


app = FastAPI(title="Resume Tailoring API", version="1.0.0", lifespan=lifespan)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

app.include_router(ingestion.router, prefix="/api/v1/ingest", tags=["ingestion"])
app.include_router(generation.router, prefix="/api/v1/generate", tags=["generation"])
app.include_router(verification.router, prefix="/api/v1/verify", tags=["verification"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
