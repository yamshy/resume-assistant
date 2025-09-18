"""User profile data models for the resume assistant.

This module contains all pydantic models for user profile data storage and validation.
Models follow the specifications from specs/001-resume-tailoring-feature/data-model.md.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from enum import Enum


class ContactInfo(BaseModel):
    """Basic contact information with EmailStr validation."""
    name: str = Field(description="Full name")
    email: EmailStr = Field(description="Email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    location: str = Field(description="City, State or City, Country")
    linkedin: Optional[str] = Field(default=None, description="LinkedIn profile URL")
    portfolio: Optional[str] = Field(default=None, description="Portfolio website URL")


class WorkExperience(BaseModel):
    """Job history with dates and achievements."""
    position: str = Field(description="Job title")
    company: str = Field(description="Company name")
    location: str = Field(description="Work location")
    start_date: str = Field(description="Start date")
    end_date: Optional[str] = Field(default=None, description="End date (None if current)")
    description: str = Field(description="Role description and responsibilities")
    achievements: List[str] = Field(description="Quantified achievements with metrics")
    technologies: List[str] = Field(default=[], description="Technologies used")


class Education(BaseModel):
    """Educational background with graduation dates."""
    degree: str = Field(description="Degree type and field")
    institution: str = Field(description="School/university name")
    location: str = Field(description="School location")
    graduation_date: str = Field(description="Graduation date")
    gpa: Optional[float] = Field(default=None, description="GPA if noteworthy")
    honors: List[str] = Field(default=[], description="Academic honors and awards")
    relevant_coursework: List[str] = Field(default=[], description="Relevant courses")


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
    years_experience: Optional[int] = Field(default=None, description="Years of experience")


class Project(BaseModel):
    """Personal/professional projects."""
    name: str = Field(description="Project name")
    description: str = Field(description="Project description")
    technologies: List[str] = Field(description="Technologies used")
    start_date: str = Field(description="Start date")
    end_date: Optional[str] = Field(default=None, description="End date (None if ongoing)")
    url: Optional[str] = Field(default=None, description="Project URL")
    achievements: List[str] = Field(description="Key achievements and outcomes")


class Publication(BaseModel):
    """Articles and papers."""
    title: str = Field(description="Publication title")
    venue: str = Field(description="Journal, conference, or platform")
    date: str = Field(description="Publication date")
    url: Optional[str] = Field(default=None, description="Publication URL")
    authors: List[str] = Field(description="Co-authors")


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
    end_date: Optional[str] = Field(default=None, description="End date (None if ongoing)")
    description: str = Field(description="Role description and impact")


class Language(BaseModel):
    """Language proficiencies."""
    name: str = Field(description="Language name")
    proficiency: str = Field(description="Proficiency level (native, fluent, conversational, basic)")


class UserProfile(BaseModel):
    """Main profile aggregating all components."""
    contact: ContactInfo = Field(description="Contact information")
    professional_summary: str = Field(description="Professional summary/objective")
    experience: List[WorkExperience] = Field(description="Work experience entries")
    education: List[Education] = Field(description="Education entries")
    skills: List[Skill] = Field(description="Skills with categories and proficiency")
    projects: List[Project] = Field(default=[], description="Personal/professional projects")
    publications: List[Publication] = Field(default=[], description="Publications and articles")
    awards: List[Award] = Field(default=[], description="Awards and recognitions")
    volunteer: List[VolunteerWork] = Field(default=[], description="Volunteer experience")
    languages: List[Language] = Field(default=[], description="Language proficiencies")


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