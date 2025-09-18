from datetime import date
from uuid import UUID

import pytest

from resume_core.models.profile import (
    ContactInfo,
    Education,
    Skill,
    SkillCategory,
    UserProfile,
    WorkExperience,
)
from resume_core.services.profile import ProfileStore
from resume_core.services.tailoring import ResumeTailoringService


def build_profile() -> dict:
    profile = UserProfile(
        version="1.0",
        metadata={"created_at": "2024-01-01T00:00:00Z"},
        contact=ContactInfo(name="John Developer", email="john@example.com", location="San Francisco, CA"),
        professional_summary="Backend engineer with 6 years of experience building APIs.",
        experience=[
            WorkExperience(
                position="Senior Software Engineer",
                company="StartupXYZ",
                location="San Francisco, CA",
                start_date=date(2020, 1, 1),
                end_date=None,
                description="Lead backend engineer driving platform improvements.",
                achievements=["Improved system reliability by 30%"],
                technologies=["Python", "FastAPI", "PostgreSQL", "AWS"],
            )
        ],
        education=[
            Education(
                degree="B.S. Computer Science",
                institution="UC Berkeley",
                location="Berkeley, CA",
                graduation_date=date(2018, 5, 15),
            )
        ],
        skills=[
            Skill(name="Python", category=SkillCategory.TECHNICAL, proficiency=5, years_experience=6),
            Skill(name="FastAPI", category=SkillCategory.TECHNICAL, proficiency=4, years_experience=4),
            Skill(name="PostgreSQL", category=SkillCategory.TECHNICAL, proficiency=4, years_experience=4),
        ],
        projects=[],
        publications=[],
        awards=[],
        volunteer=[],
        languages=[],
    )
    return profile.model_dump(mode="json")


@pytest.mark.asyncio
async def test_resume_tailoring_flow(async_client, monkeypatch, tmp_path):
    monkeypatch.setenv("RESUME_ASSISTANT_DATA_DIR", str(tmp_path))

    from app.api import deps
    from app.main import app

    store = ProfileStore(base_path=tmp_path)
    service = ResumeTailoringService(profile_store=store)
    app.dependency_overrides[deps.get_tailoring_service] = lambda: service

    payload = build_profile()
    response = await async_client.put("/api/v1/profile", json=payload)
    assert response.status_code == 200

    job_desc = {
        "job_description": "Senior Software Engineer wanted. Experience with Python, FastAPI, and PostgreSQL required."
    }
    response = await async_client.post("/api/v1/jobs/analyze", json=job_desc)
    assert response.status_code == 200
    analysis = response.json()
    assert analysis["job_title"] == "Senior Software Engineer"
    assert any(req["skill"].lower() == "python" for req in analysis["requirements"])
    assert analysis["company_culture"] in {"collaborative environment", "Not specified"}

    tailor_request = {
        "job_description": job_desc["job_description"],
        "preferences": {"emphasis_areas": ["Python"], "excluded_sections": []},
    }
    response = await async_client.post("/api/v1/resumes/tailor", json=tailor_request)
    assert response.status_code == 200
    result = response.json()
    resume_id = UUID(result["resume_id"])
    assert result["matching_result"]["recommendations"]

    decision_payload = {
        "decision": "approved",
        "feedback": "Ship it",
        "approved_sections": ["summary", "experience"],
    }
    response = await async_client.post(f"/api/v1/resumes/{resume_id}/approve", json=decision_payload)
    assert response.status_code == 200
    approval = response.json()
    assert approval["status"] == "approved"
    assert not approval["revision_needed"]
    assert approval["next_steps"] == [
        "Download your tailored resume",
        "Review final formatting",
        "Submit your application to Unknown Company",
    ]

    response = await async_client.get(f"/api/v1/resumes/{resume_id}/download", params={"format": "markdown"})
    assert response.status_code == 200
    assert "John Developer" in response.text

    response = await async_client.get("/api/v1/resumes/history")
    assert response.status_code == 200
    history = response.json()
    assert history["total"] == 1
    assert UUID(history["resumes"][0]["resume_id"]) == resume_id

    app.dependency_overrides.pop(deps.get_tailoring_service, None)
