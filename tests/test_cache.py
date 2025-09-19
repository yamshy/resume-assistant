import asyncio
from datetime import date

import pytest

from app.cache import SemanticCache
from app.memory import InMemoryRedis
from app.models import Experience, Resume


@pytest.mark.asyncio
async def test_semantic_cache_roundtrip():
    redis_client = InMemoryRedis()
    cache = SemanticCache(redis_client)
    resume = Resume(
        full_name="Taylor Candidate",
        email="taylor@example.com",
        phone="+1 555-0100",
        location="Remote",
        summary="""Seasoned engineer delivering 40% deployment gains and cost savings.""",
        experiences=[
            Experience(
                company="Acme",
                role="Engineer",
                start_date=date(2020, 1, 1),
                achievements=["Improved deployment speed by 40%"],
            )
        ],
        education=[],
        skills=["Python"],
    )

    await cache.set("Software Engineer", {"full_name": "Taylor Candidate"}, resume)
    cached = await cache.get("Software Engineer", {"full_name": "Taylor Candidate"})
    assert cached is not None
    assert cached.full_name == resume.full_name
    assert cached.metadata.get("cached") is True
