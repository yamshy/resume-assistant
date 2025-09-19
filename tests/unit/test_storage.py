from app.storage import MemoryStorage


def test_remember_skill_and_promote(app_context):
    storage: MemoryStorage = app_context["storage"]
    entry = storage.remember_skill({"name": "GraphQL"}, "Conversation snippet")
    pending_skills = storage.get_discovered_items()["skills"]
    assert any(skill["id"] == entry["id"] for skill in pending_skills)

    storage.promote_to_profile("skill", entry["id"])
    profile = storage.load_profile()
    assert any(
        skill.get("name") == "GraphQL" for skill in profile.get("skills", {}).get("technical", [])
    )


def test_cache_roundtrip(app_context):
    storage: MemoryStorage = app_context["storage"]
    payload = {"resume_text": "Example"}
    storage.store_cached_resume("cache-key", payload)
    cached = storage.load_cached_resume("cache-key")
    assert cached == payload
