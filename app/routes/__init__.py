"""Route modules for the FastAPI application."""

from .generation import router as generation_router
from .knowledge import router as knowledge_router

__all__ = ["generation_router", "knowledge_router"]
