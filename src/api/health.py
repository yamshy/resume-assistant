"""
Health check endpoint for Resume Assistant API.

Provides basic health status and system information for monitoring
and load balancer health checks.

Constitutional compliance:
- Simple health check implementation
- Standard FastAPI patterns
- JSON response matching OpenAPI spec
"""

from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: str


# Create router for health endpoints
router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns basic health status and current timestamp.
    Used by load balancers and monitoring systems.

    Returns:
        HealthResponse: Status and timestamp
    """
    return HealthResponse(status="ok", timestamp=datetime.now().isoformat())


__all__ = ["router", "HealthResponse"]
