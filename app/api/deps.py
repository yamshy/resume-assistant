"""FastAPI dependency wiring."""

from functools import lru_cache

from app.services.generation import GenerationService
from app.services.ingestion import IngestionService
from app.services.repository import ProfileRepository, ReviewRepository
from app.services.validation import ReviewService


@lru_cache(maxsize=1)
def get_profile_repository() -> ProfileRepository:
    return ProfileRepository()


@lru_cache(maxsize=1)
def get_review_repository() -> ReviewRepository:
    return ReviewRepository()


@lru_cache(maxsize=1)
def get_review_service() -> ReviewService:
    return ReviewService(get_review_repository())


@lru_cache(maxsize=1)
def get_ingestion_service() -> IngestionService:
    return IngestionService(get_profile_repository(), get_review_service())


@lru_cache(maxsize=1)
def get_generation_service() -> GenerationService:
    return GenerationService(get_profile_repository(), get_review_service())


__all__ = [
    "get_ingestion_service",
    "get_generation_service",
    "get_review_service",
]
