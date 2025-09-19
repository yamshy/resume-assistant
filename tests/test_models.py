from datetime import date

import pytest
from pydantic import ValidationError

from app.models import Experience, Resume


def test_experience_requires_metrics():
    with pytest.raises(ValidationError):
        Experience(
            company="Acme",
            role="Engineer",
            start_date=date(2020, 1, 1),
            achievements=["Led a team"],
        )


def test_resume_text_formatting():
    resume = Resume(
        full_name="Taylor Candidate",
        email="taylor@example.com",
        phone="+1 555-0100",
        location="Remote",
        summary="""Experienced engineer delivering 30% efficiency improvements across cloud deployments while mentoring peers.""",
        experiences=[
            Experience(
                company="Acme",
                role="Engineer",
                start_date=date(2020, 1, 1),
                achievements=["Increased deployment frequency by 40%"],
            )
        ],
        education=[],
        skills=["Python", "AWS"],
    )
    text = resume.to_text()
    assert "Professional Experience" in text
    assert "Skills" in text
    assert "Increased deployment frequency" in text
