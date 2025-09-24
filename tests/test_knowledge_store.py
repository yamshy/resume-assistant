"""Regression tests for the disk-backed knowledge store."""

from __future__ import annotations

import json

from app.ingestion import ParsedExperience, ParsedResume
from app.knowledge_store import KnowledgeStore


def test_store_recovers_from_malformed_disk_state(tmp_path) -> None:
    store_path = tmp_path / "knowledge_store.json"
    malformed_payload = {
        "resumes": [
            {
                "source": "seed",
                "full_name": "Seed Example",
                "email": "seed@example.com",
                "phone": None,
            },
            "not a resume entry",
        ],
        "skills": "SeedSkill",
        "experiences": [
            "totally invalid",
            {
                "source": "seed",
                "company": "Seed Co",
                "role": "Engineer",
                "achievements": "Launched product",
                "start_date": "2018-06-01",
                "end_date": None,
                "location": "Remote",
            },
        ],
    }
    store_path.write_text(json.dumps(malformed_payload), encoding="utf-8")

    store = KnowledgeStore(store_path)

    assert all(isinstance(entry, dict) for entry in store._data["resumes"])
    assert store._data["skills"] == ["SeedSkill"]
    assert len(store._data["experiences"]) == 1
    assert store._data["experiences"][0]["achievements"] == ["Launched product"]

    resume = ParsedResume(
        source="upload",
        full_name="New Candidate",
        email="candidate@example.com",
        phone="555-0100",
        skills=["SeedSkill", "Python"],
        experiences=[
            ParsedExperience(
                company="New Co",
                role="Developer",
                achievements=["Built tooling", "Improved reliability"],
                start_date="2022-01-01",
                end_date="2023-06-01",
                location="Remote",
            ),
            ParsedExperience(
                company="Prior Co",
                role="Engineer",
                achievements=[],
                start_date="2020-01-01",
                end_date="2021-01-01",
                location="On-site",
            ),
        ],
    )

    summary = store.add_resumes([resume])

    assert summary["skills_added"] == ["Python"]
    assert summary["achievements_indexed"] == 2

    assert len(store._data["resumes"]) == 2
    assert len(store._data["experiences"]) == 3
    assert all(isinstance(exp, dict) for exp in store._data["experiences"])
    assert all(
        isinstance(achievement, str)
        for exp in store._data["experiences"]
        for achievement in exp.get("achievements", [])
    )

    persisted = json.loads(store_path.read_text(encoding="utf-8"))
    assert persisted["skills"] == ["Python", "SeedSkill"]
    assert len(persisted["experiences"]) == 3
    assert all(isinstance(exp, dict) for exp in persisted["experiences"])
    assert all(
        isinstance(achievement, str)
        for exp in persisted["experiences"]
        for achievement in exp.get("achievements", [])
    )
