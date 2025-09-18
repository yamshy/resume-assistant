"""
Resume Assistant FastAPI Application.

Main application setup with all routers, middleware, and configuration
following constitutional patterns for agent-chain architecture.

Constitutional compliance:
- FastAPI for all HTTP services
- Structured JSON logging
- Health check endpoints required
- Environment-based configuration
"""

import logging
import sys
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api.approval import router as approval_router
from api.download import router as download_router

# Import all API routers
from api.health import router as health_router
from api.history import router as history_router
from api.jobs import router as jobs_router
from api.profile import router as profile_router
from api.resumes import router as resumes_router

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)

logger = logging.getLogger("resume-assistant")


class ErrorResponse(BaseModel):
    """Standard error response format."""

    error: str
    timestamp: str


# Create FastAPI application
app = FastAPI(
    title="Resume Assistant API",
    description="AI-powered resume tailoring system using agent-chain architecture",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with structured response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "detail": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions with structured response."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "detail": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.now().isoformat(),
        },
    )


# Add startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    logger.info("Resume Assistant API starting up")
    logger.info("Agent-chain architecture initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event."""
    logger.info("Resume Assistant API shutting down")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Resume Assistant API",
        "description": "AI-powered resume tailoring using agent-chain architecture",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_check": "/health",
        "timestamp": datetime.now().isoformat(),
    }


# Include all routers with /api/v1 prefix for versioning
# NOTE: history_router must come before resumes_router to avoid route conflicts
# /resumes/history must be matched before /resumes/{session_id}
app.include_router(health_router, prefix="/api/v1")
app.include_router(profile_router, prefix="/api/v1")
app.include_router(jobs_router, prefix="/api/v1")
app.include_router(history_router, prefix="/api/v1")
app.include_router(resumes_router, prefix="/api/v1")
app.include_router(approval_router, prefix="/api/v1")
app.include_router(download_router, prefix="/api/v1")


# Development server entry point
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="info")


__all__ = ["app"]
