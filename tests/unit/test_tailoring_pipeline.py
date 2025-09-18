from datetime import date

import pytest

from resume_core.models.profile import (
    ContactInfo,
    Education,
    Skill,
    SkillCategory,
    UserProfile,
    WorkExperience,
)
from resume_core.models.resume import ReviewDecision
from resume_core.services.profile import ProfileStore
from resume_core.services.tailoring import ResumeTailoringService, TailoringPreferences


JOB_DESCRIPTION = """
Senior Software Engineer - Backend Platform
TechCorp Inc.

We are looking for an experienced backend engineer to build scalable services.
You will collaborate with a cross-functional team to deliver platform features.

Requirements:
- 5+ years of Python experience
- Strong knowledge of FastAPI
- Experience with PostgreSQL databases
- Familiarity with AWS cloud services

Preferred Qualifications:
- Experience with Kubernetes
- Experience leading engineering projects
""".strip()


def build_profile() -> UserProfile:
    return UserProfile(
        version="1.0",
        metadata={"created_at": "2024-01-01T00:00:00Z", "updated_at": "2024-02-01T00:00:00Z"},
        contact=ContactInfo(
            name="John Developer",
            email="john@example.com",
            location="San Francisco, CA",
        ),
        professional_summary="Backend engineer with 6 years of experience building scalable APIs.",
        experience=[
            WorkExperience(
                position="Senior Software Engineer",
                company="StartupXYZ",
                location="San Francisco, CA",
                start_date=date(2020, 6, 1),
                end_date=None,
                description="Leads backend platform team shipping reliable services.",
                achievements=[
                    "Scaled API throughput by 3x while reducing latency",
                    "Introduced observability stack improving MTTR by 40%",
                ],
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
            Skill(name="AWS", category=SkillCategory.TECHNICAL, proficiency=3, years_experience=3),
        ],
        projects=[],
        publications=[],
        awards=[],
        volunteer=[],
        languages=[],
    )


@pytest.mark.asyncio
async def test_tailoring_pipeline_generates_resume(tmp_path) -> None:
    store = ProfileStore(base_path=tmp_path)
    store.save_profile(build_profile())

    pipeline = ResumeTailoringService(profile_store=store)

    analysis = await pipeline.analyze_job(JOB_DESCRIPTION)
    assert analysis.job_title.startswith("Senior Software Engineer")
    assert any(req.skill.lower() == "python" for req in analysis.requirements)
    assert any(req.skill == "Kubernetes" for req in analysis.requirements)
    kubernetes_reqs = [req for req in analysis.requirements if req.skill == "Kubernetes"]
    assert kubernetes_reqs and not kubernetes_reqs[0].is_required
    assert any("Kubernetes" in pref for pref in analysis.preferred_qualifications)
    assert analysis.company_culture == "collaborative environment"

    preferences = TailoringPreferences(emphasis_areas=["Python", "FastAPI"], excluded_sections=[])
    result = await pipeline.tailor_resume(job_description=JOB_DESCRIPTION, preferences=preferences)

    assert result.resume_id in pipeline._resumes  # stored for future approval
    assert result.tailored_resume.full_resume_markdown.startswith("# John Developer")
    assert result.matching_result.overall_match_score >= 0.0
    assert result.matching_result.recommendations
    assert result.validation_result.is_valid

    history, total = pipeline.get_history(limit=5, offset=0)
    assert total == 1
    assert history[0].resume_id == result.resume_id

    decision = ReviewDecision(decision="approved", feedback="Looks good", approved_sections=["summary"])
    approval = await pipeline.approve_resume(result.resume_id, decision)
    assert approval.status == "approved"
    assert not approval.revision_needed
    assert approval.next_steps == [
        "Download your tailored resume",
        "Review final formatting",
        "Submit your application to TechCorp Inc.",
    ]

    markdown = pipeline.get_resume_markdown(result.resume_id)
    assert "Senior Software Engineer" in markdown
