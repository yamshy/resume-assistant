from datetime import date

from resume_core.models.profile import (
    ContactInfo,
    Education,
    Skill,
    SkillCategory,
    UserProfile,
    WorkExperience,
)
from resume_core.services.profile import ProfileStore


def build_profile() -> UserProfile:
    return UserProfile(
        version="1.0",
        metadata={"created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-01-10T00:00:00Z"},
        contact=ContactInfo(
            name="John Developer",
            email="john@example.com",
            location="San Francisco, CA",
            phone="555-123-4567",
            linkedin="https://linkedin.com/in/johndeveloper",
        ),
        professional_summary="Experienced engineer with a focus on backend services and infrastructure.",
        experience=[
            WorkExperience(
                position="Software Engineer",
                company="StartupXYZ",
                location="San Francisco, CA",
                start_date=date(2019, 1, 15),
                end_date=None,
                description="Led development of scalable backend systems.",
                achievements=[
                    "Reduced API latency by 35% through caching and profiling",
                    "Implemented CI/CD pipelines to ship features twice as fast",
                ],
                technologies=["Python", "FastAPI", "PostgreSQL", "Docker"],
            )
        ],
        education=[
            Education(
                degree="B.S. Computer Science",
                institution="UC Berkeley",
                location="Berkeley, CA",
                graduation_date=date(2018, 5, 15),
                honors=["Magna Cum Laude"],
                relevant_coursework=["Distributed Systems", "Machine Learning"],
            )
        ],
        skills=[
            Skill(name="Python", category=SkillCategory.TECHNICAL, proficiency=5, years_experience=6),
            Skill(name="FastAPI", category=SkillCategory.TECHNICAL, proficiency=4, years_experience=3),
            Skill(name="PostgreSQL", category=SkillCategory.TECHNICAL, proficiency=4, years_experience=4),
            Skill(name="AWS", category=SkillCategory.TECHNICAL, proficiency=3, years_experience=3),
        ],
        projects=[],
        publications=[],
        awards=[],
        volunteer=[],
        languages=[],
    )


def test_profile_store_round_trip(tmp_path) -> None:
    store = ProfileStore(base_path=tmp_path)

    profile = build_profile()
    saved = store.save_profile(profile)

    assert saved.contact.name == "John Developer"
    assert (tmp_path / "profile.json").exists()

    loaded = store.get_profile()
    assert loaded == profile


def test_profile_store_returns_none_when_missing(tmp_path) -> None:
    store = ProfileStore(base_path=tmp_path)

    assert store.get_profile() is None
