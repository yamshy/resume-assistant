#!/usr/bin/env python
"""Run the resume tailoring pipeline with dummy data."""

from __future__ import annotations

import asyncio
from pprint import pprint
from uuid import uuid4

from app.core.cache import close_cache, init_cache
from app.core.database import close_db, init_db
from app.services.generation import GenerationService
from app.services.ingestion import IngestionService
from app.services.repository import ProfileRepository, ReviewRepository
from app.services.validation import ReviewService

SAMPLE_RESUMES = [
    (
        "Experience: Initech - Data Engineer 2019-2022: Built pipelines; Optimized ETL\n"
        "Skills: Python, SQL, Airflow\n"
        "Education: MS Data Science\n"
    ),
    "Experienced technologist with a passion for data platforms and automation.",
]

SAMPLE_JOB_POSTING = (
    "Looking for a data engineer with Python and SQL expertise to build analytics pipelines."
)


def _encode_resumes(resumes: list[str]) -> list[bytes]:
    return [resume.encode("utf-8") for resume in resumes]


async def run_demo() -> None:
    """Execute ingestion, generation, and review queries with sample data."""

    await init_db()
    await init_cache()

    profile_repository = ProfileRepository()
    review_service = ReviewService(ReviewRepository())

    ingestion = IngestionService(profile_repository, review_service)
    generation = GenerationService(profile_repository, review_service)

    user_id = str(uuid4())

    print("Ingesting resumes...")
    profile, review_items = await ingestion.ingest_resumes(
        _encode_resumes(SAMPLE_RESUMES),
        user_id,
    )
    print(f"Created profile {profile.id}")
    print("Parsed experiences:")
    for experience in profile.experiences:
        print(f" - {experience.role} at {experience.company} ({experience.start_date:%Y})")

    if review_items:
        print("Review items queued:")
        for item in review_items:
            print(f" - [{item.item_type}] {item.content} -> {item.reason}")
    else:
        print("No review items were generated during ingestion.")

    print("\nGenerating tailored resume...")
    result = await generation.generate_resume(SAMPLE_JOB_POSTING, user_id)
    print(f"Validation confidence: {result['confidence']:.2f}")
    print("Resume summary:")
    pprint(result["resume"], sort_dicts=False)

    pending = await review_service.get_pending(user_id)
    if pending:
        print("\nPending review items:")
        for item in pending:
            print(f" - {item.item_type}: {item.content} (confidence={item.confidence:.2f})")
    else:
        print("\nNo pending review items after generation.")

    await close_cache()
    await close_db()


if __name__ == "__main__":
    asyncio.run(run_demo())
