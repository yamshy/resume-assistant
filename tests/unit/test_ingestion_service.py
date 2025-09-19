from uuid import uuid4

import pytest

from app.core.database import close_db, init_db
from app.services.ingestion import IngestionService
from app.services.repository import ProfileRepository, ReviewRepository
from app.services.validation import ReviewService


@pytest.mark.asyncio
async def test_ingestion_pipeline_creates_profile() -> None:
    await init_db()
    service = IngestionService(ProfileRepository(), ReviewService(ReviewRepository()))
    user_id = str(uuid4())

    structured_resume = (
        "Experience: Acme Corp - Software Engineer 2018-2021: Built APIs; Led migrations\n"
        "Skills: Python, FastAPI, SQL\n"
        "Education: BS Computer Science\n"
    ).encode()

    unstructured_resume = b"Seasoned technologist with diverse experience."

    profile, review_items = await service.ingest_resumes(
        [structured_resume, unstructured_resume],
        user_id,
    )

    assert profile.experiences
    assert any(exp.company == "Acme Corp" for exp in profile.experiences)
    assert any(skill.name.lower() == "python" for skill in profile.skills)
    assert review_items  # the unstructured resume should trigger a review item

    stored = await service.load_profile(user_id)
    assert stored is not None
    assert stored.id == profile.id

    await close_db()
