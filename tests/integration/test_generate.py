import pytest


@pytest.mark.asyncio
async def test_generate_endpoint_applies_memory(async_client, app_context):
    storage = app_context["storage"]
    orchestrator = app_context["orchestrator"]
    orchestrator_llm = app_context["orchestrator_llm"]
    memory_llm = app_context["memory_llm"]

    job_posting = "Python backend developer"
    profile = storage.load_profile()
    discovered = storage.get_discovered_items()
    preferences = storage.get_preferences()
    cache_key = orchestrator._cache_key(job_posting, profile, discovered, preferences)

    orchestrator_llm.queue_response(
        {
            "resume_text": "Base resume",
            "sections": {"summary": ["Uses Python daily"]},
            "confidence": 0.88,
            "section_confidence": {"summary": 0.88},
            "review_flags": [],
            "conversation": "User confirmed FastAPI experience",
            "used_discoveries": [],
            "cache_key": cache_key,
        }
    )
    memory_llm.queue_response("Personalized resume text")
    memory_llm.queue_response({"new_skills": [{"name": "Go"}]})

    response = await async_client.post("/generate", json={"job_posting": job_posting})
    assert response.status_code == 200
    body = response.json()
    assert body["personalized_resume"] == "Personalized resume text"
    assert body["new_discoveries"]["new_skills"][0]["name"] == "Go"
    pending = storage.get_discovered_items()["skills"]
    assert any(skill["name"] == "Go" for skill in pending)


@pytest.mark.asyncio
async def test_review_submit_learns_corrections(async_client, app_context):
    memory_llm = app_context["memory_llm"]
    memory_llm.queue_response({})

    decisions = [
        {"id": "1", "original": "worked on", "edited": "built", "context": "Summary"}
    ]
    response = await async_client.post("/review/submit", json={"decisions": decisions})
    assert response.status_code == 200
    corrections = app_context["storage"].get_corrections()
    assert any(item["original"] == "worked on" and item["corrected_to"] == "built" for item in corrections)


@pytest.mark.asyncio
async def test_teach_and_approve_skill(async_client, app_context):
    skill_payload = {
        "type": "skill",
        "data": {"name": "Terraform", "confidence": 0.7},
    }

    response = await async_client.post("/memory/teach", json=skill_payload)
    assert response.status_code == 200
    discovered = app_context["storage"].get_discovered_items()["skills"]
    skill_id = discovered[0]["id"]

    approve_payload = {"item_type": "skill", "item_id": skill_id}
    response = await async_client.post("/memory/approve", json=approve_payload)
    assert response.status_code == 200
    profile = app_context["storage"].load_profile()
    assert any(skill.get("name") == "Terraform" for skill in profile.get("skills", {}).get("technical", []))
