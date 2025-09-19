import pytest


@pytest.mark.asyncio
async def test_generate_with_memory_uses_cache(app_context):
    orchestrator = app_context["orchestrator"]
    storage = app_context["storage"]
    orchestrator_llm = app_context["orchestrator_llm"]

    job_posting = "Backend engineer"
    profile = storage.load_profile()
    discovered = storage.get_discovered_items()
    preferences = storage.get_preferences()
    cache_key = orchestrator._cache_key(job_posting, profile, discovered, preferences)

    orchestrator_llm.queue_response(
        {
            "resume_text": "Generated resume",
            "sections": {"summary": ["Experienced engineer"]},
            "confidence": 0.92,
            "section_confidence": {"summary": 0.92},
            "review_flags": [],
            "conversation": "Discussed verified experiences",
            "used_discoveries": [],
            "cache_key": cache_key,
        }
    )

    first = await orchestrator.generate_with_memory(job_posting, profile, discovered, preferences)
    assert first["status"] == "generated"
    assert storage.load_cached_resume(cache_key)["resume_text"] == "Generated resume"

    orchestrator_llm.responses.clear()
    second = await orchestrator.generate_with_memory(job_posting, profile, discovered, preferences)
    assert second["status"] == "cached"
    assert len(orchestrator_llm.calls) == 1
