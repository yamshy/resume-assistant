from datetime import date

import pytest

from app.embeddings import SemanticEmbedder
from app.models import Experience, Resume
from app.validator import ClaimValidator


def _build_resume(
    *,
    company: str,
    role: str,
    achievement: str,
    skills: list[str],
) -> Resume:
    return Resume(
        full_name="Taylor Candidate",
        email="taylor@example.com",
        phone="+1 555-0100",
        location="Remote",
        summary=(
            "Seasoned professional delivering measurable improvements across "
            "large-scale engineering programs while aligning outcomes to business needs."
        ),
        experiences=[
            Experience(
                company=company,
                role=role,
                start_date=date(2020, 1, 1),
                achievements=[achievement],
            )
        ],
        skills=skills,
    )


@pytest.mark.asyncio
async def test_validator_scores_profile_alignment() -> None:
    resume = _build_resume(
        company="Acme Corporation",
        role="Senior Engineer",
        achievement="Improved system reliability by 30% through automation",
        skills=["Python", "AWS"],
    )
    context = {
        "profile": {
            "skills": ["Python", "AWS"],
            "experience": [
                {
                    "company": "Acme Corporation",
                    "role": "Senior Engineer",
                    "achievements": ["Improved system reliability by 30% through automation"],
                }
            ],
        }
    }

    validator = ClaimValidator(SemanticEmbedder())
    validated = await validator.validate(resume, context)

    assert validated.confidence_scores["skill:Python"] == pytest.approx(1.0)
    assert validated.confidence_scores["experience.company:Acme Corporation"] == pytest.approx(1.0)
    assert (
        validated.confidence_scores["experience.role:Senior Engineer at Acme Corporation"]
        == pytest.approx(1.0)
    )
    assert validated.confidence_scores["overall"] == pytest.approx(1.0)
    assert validated.citations["skill:Python"] == "Python"
    assert (
        validated.citations["experience.role:Senior Engineer at Acme Corporation"]
        == "Senior Engineer at Acme Corporation"
    )


@pytest.mark.asyncio
async def test_validator_flags_hallucinated_skill_and_role() -> None:
    resume = _build_resume(
        company="Initech",
        role="Platform Lead",
        achievement="Reduced deployment failures by 40% via new CI pipelines",
        skills=["GraphQL"],
    )
    context = {
        "profile": {
            "skills": ["Python"],
            "experience": [
                {
                    "company": "Acme Corporation",
                    "role": "Senior Engineer",
                    "achievements": ["Improved system reliability by 30% through automation"],
                }
            ],
        }
    }

    validator = ClaimValidator(SemanticEmbedder())
    validated = await validator.validate(resume, context)

    assert validated.confidence_scores["skill:GraphQL"] == 0.0
    assert validated.confidence_scores["experience.company:Initech"] == 0.0
    assert validated.confidence_scores["experience.role:Platform Lead at Initech"] == 0.0
    assert validated.confidence_scores["overall"] == 0.0
    assert "skill:GraphQL" not in validated.citations
