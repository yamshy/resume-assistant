from __future__ import annotations

from resume_core.models.profile import (
    ContactInfo,
    EducationEntry,
    ExperienceAchievement,
    SkillEntry,
    UserProfile,
    WorkExperience,
)

SAMPLE_JOB_POSTING = "Senior Backend Engineer needed to build FastAPI services, manage AWS infrastructure, and mentor developers."


def build_sample_profile() -> UserProfile:
    return UserProfile(
        contact=ContactInfo(
            name="Jordan Smith",
            email="jordan@example.com",
            phone="555-0100",
            location="Remote",
        ),
        summary="Backend engineer with strong FastAPI and AWS experience.",
        experience=[
            WorkExperience(
                role="Senior Backend Engineer",
                company="ScaleUp",
                start_date="2019-01",
                end_date="2023-12",
                achievements=[
                    ExperienceAchievement(
                        description="Led migration to FastAPI microservices",
                        metrics="Cut latency by 40%",
                    )
                ],
                skills=["python", "fastapi", "aws", "mentoring"],
            )
        ],
        education=[
            EducationEntry(
                degree="BSc Computer Science",
                institution="Tech University",
                start_date="2012-09",
                end_date="2016-06",
            )
        ],
        skills=[
            SkillEntry(name="Python", level="expert"),
            SkillEntry(name="FastAPI", level="advanced"),
            SkillEntry(name="AWS", level="advanced"),
        ],
    )
