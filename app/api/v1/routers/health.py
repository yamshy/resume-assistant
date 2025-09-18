from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Simple liveness probe used by the quickstart manual tests."""

    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
