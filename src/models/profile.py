"""User profile data models for the resume assistant.

This module contains all pydantic models for user profile data storage and validation.
Models follow the specifications from specs/001-resume-tailoring-feature/data-model.md.
"""

from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class ContactInfo(BaseModel):
    """Basic contact information with EmailStr validation."""

    name: str = Field(description="Full name")
    email: EmailStr = Field(description="Email address")
    phone: str | None = Field(default=None, description="Phone number")
    location: str = Field(description="City, State or City, Country")
    linkedin: str | None = Field(default=None, description="LinkedIn profile URL")
    portfolio: str | None = Field(default=None, description="Portfolio website URL")


class WorkExperience(BaseModel):
    """Job history with dates and achievements."""

    position: str = Field(description="Job title")
    company: str = Field(description="Company name")
    location: str = Field(description="Work location")
    start_date: str = Field(description="Start date")
    end_date: str | None = Field(default=None, description="End date (None if current)")
    description: str = Field(description="Role description and responsibilities")
    achievements: list[str] = Field(description="Quantified achievements with metrics")
    technologies: list[str] = Field(default=[], description="Technologies used")


class Education(BaseModel):
    """Educational background with graduation dates."""

    degree: str = Field(description="Degree type and field")
    institution: str = Field(description="School/university name")
    location: str = Field(description="School location")
    graduation_date: str = Field(description="Graduation date")
    gpa: float | None = Field(default=None, description="GPA if noteworthy")
    honors: list[str] = Field(default=[], description="Academic honors and awards")
    relevant_coursework: list[str] = Field(default=[], description="Relevant courses")


class SkillCategory(str, Enum):
    """Categories for different types of skills."""

    TECHNICAL = "technical"
    SOFT = "soft"
    LANGUAGE = "language"
    CERTIFICATION = "certification"


class Skill(BaseModel):
    """Skills with categories and proficiency levels."""

    name: str = Field(description="Skill name")
    category: SkillCategory = Field(description="Skill category")
    proficiency: int = Field(ge=1, le=5, description="Proficiency level 1-5")
    years_experience: int | None = Field(default=None, description="Years of experience")


class Project(BaseModel):
    """Personal/professional projects."""

    name: str = Field(description="Project name")
    description: str = Field(description="Project description")
    technologies: list[str] = Field(description="Technologies used")
    start_date: str = Field(description="Start date")
    end_date: str | None = Field(default=None, description="End date (None if ongoing)")
    url: str | None = Field(default=None, description="Project URL")
    achievements: list[str] = Field(description="Key achievements and outcomes")


class Publication(BaseModel):
    """Articles and papers."""

    title: str = Field(description="Publication title")
    venue: str = Field(description="Journal, conference, or platform")
    date: str = Field(description="Publication date")
    url: str | None = Field(default=None, description="Publication URL")
    authors: list[str] = Field(description="Co-authors")


class Award(BaseModel):
    """Recognition and awards."""

    title: str = Field(description="Award title")
    organization: str = Field(description="Awarding organization")
    date: str = Field(description="Award date")
    description: str = Field(description="Award description")


class VolunteerWork(BaseModel):
    """Volunteer experience."""

    role: str = Field(description="Volunteer role")
    organization: str = Field(description="Organization name")
    start_date: str = Field(description="Start date")
    end_date: str | None = Field(default=None, description="End date (None if ongoing)")
    description: str = Field(description="Role description and impact")


class Language(BaseModel):
    """Language proficiencies."""

    name: str = Field(description="Language name")
    proficiency: str = Field(
        description="Proficiency level (native, fluent, conversational, basic)"
    )


class UserProfile(BaseModel):
    """Main profile aggregating all components."""

    contact: ContactInfo = Field(description="Contact information")
    professional_summary: str = Field(description="Professional summary/objective")
    experience: list[WorkExperience] = Field(description="Work experience entries")
    education: list[Education] = Field(description="Education entries")
    skills: list[Skill] = Field(description="Skills with categories and proficiency")
    projects: list[Project] = Field(default=[], description="Personal/professional projects")
    publications: list[Publication] = Field(default=[], description="Publications and articles")
    awards: list[Award] = Field(default=[], description="Awards and recognitions")
    volunteer: list[VolunteerWork] = Field(default=[], description="Volunteer experience")
    languages: list[Language] = Field(default=[], description="Language proficiencies")


__all__ = [
    "ContactInfo",
    "WorkExperience",
    "Education",
    "SkillCategory",
    "Skill",
    "Project",
    "Publication",
    "Award",
    "VolunteerWork",
    "Language",
    "UserProfile",
]
