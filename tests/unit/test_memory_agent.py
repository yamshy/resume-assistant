import pytest


@pytest.mark.asyncio
async def test_analyze_conversation_records_discoveries(app_context):
    agent = app_context["memory_agent"]
    storage = app_context["storage"]
    memory_llm = app_context["memory_llm"]

    memory_llm.queue_response(
        {
            "new_skills": [{"name": "Kubernetes", "confidence": 0.9}],
            "preferences": {"writing_style": {"tone": "friendly"}},
            "corrections": [
                {"original": "worked on", "corrected_to": "architected", "context": "Testing"}
            ],
        }
    )

    discoveries = await agent.analyze_conversation("User mentioned Kubernetes", {"summary": ""})
    assert discoveries["new_skills"][0]["name"] == "Kubernetes"
    skills = storage.get_discovered_items()["skills"]
    assert any(skill["name"] == "Kubernetes" for skill in skills)
    prefs = storage.get_preferences()
    assert "writing_style" in prefs
    corrections = storage.get_corrections()
    assert any(item["original"] == "worked on" for item in corrections)


@pytest.mark.asyncio
async def test_apply_learned_preferences_uses_llm(app_context):
    agent = app_context["memory_agent"]
    memory_llm = app_context["memory_llm"]

    memory_llm.queue_response("Improved resume content")

    result = await agent.apply_learned_preferences("Original resume")
    assert result == "Improved resume content"


@pytest.mark.asyncio
async def test_learn_from_decision_adds_skill(app_context):
    agent = app_context["memory_agent"]
    storage = app_context["storage"]
    memory_llm = app_context["memory_llm"]

    memory_llm.queue_response({"new_skill": {"name": "Rust"}, "notes": "Prefers backend depth"})

    learning = await agent.learn_from_decision({"id": "rev-1"})
    assert learning["new_skill_discovered"] is True
    skills = storage.get_discovered_items()["skills"]
    assert any(skill["name"] == "Rust" for skill in skills)
