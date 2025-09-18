from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Iterable

from pydantic import AnyHttpUrl, BaseModel, EmailStr, Field


class ProfileMetadata(BaseModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ContactInfo(BaseModel):
    name: str
    email: EmailStr
    location: str
    phone: str | None = None
    linkedin: AnyHttpUrl | None = None
    portfolio: AnyHttpUrl | None = None


class WorkExperience(BaseModel):
    position: str
    company: str
    location: str
    start_date: date
    end_date: date | None = None
    description: str
    achievements: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)


class Education(BaseModel):
    degree: str
    institution: str
    location: str
    graduation_date: date
    gpa: float | None = None
    honors: list[str] = Field(default_factory=list)
    relevant_coursework: list[str] = Field(default_factory=list)


class SkillCategory(str, Enum):
    TECHNICAL = "technical"
    SOFT = "soft"
    LANGUAGE = "language"
    CERTIFICATION = "certification"


class Skill(BaseModel):
    name: str
    category: SkillCategory
    proficiency: int = Field(ge=1, le=5)
    years_experience: int | None = None


class Project(BaseModel):
    name: str
    description: str
    technologies: list[str] = Field(default_factory=list)
    start_date: date | None = None
    end_date: date | None = None
    url: AnyHttpUrl | None = None
    achievements: list[str] = Field(default_factory=list)


class Publication(BaseModel):
    title: str
    venue: str
    date: date
    url: AnyHttpUrl | None = None
    authors: list[str] = Field(default_factory=list)


class Award(BaseModel):
    title: str
    organization: str
    date: date
    description: str


class VolunteerWork(BaseModel):
    role: str
    organization: str
    start_date: date
    end_date: date | None = None
    description: str


class Language(BaseModel):
    name: str
    proficiency: str


class UserProfile(BaseModel):
    version: str = "1.0"
    metadata: ProfileMetadata
    contact: ContactInfo
    professional_summary: str
    experience: list[WorkExperience]
    education: list[Education]
    skills: list[Skill]
    projects: list[Project] = Field(default_factory=list)
    publications: list[Publication] = Field(default_factory=list)
    awards: list[Award] = Field(default_factory=list)
    volunteer: list[VolunteerWork] = Field(default_factory=list)
    languages: list[Language] = Field(default_factory=list)

    def keyword_set(self) -> set[str]:
        keywords: set[str] = set()
        keywords.update(skill.name.lower() for skill in self.skills)
        keywords.update(self._iter_lower(self.professional_summary.split()))
        for experience in self.experience:
            keywords.update(word.lower() for word in experience.description.split())
            keywords.update(tech.lower() for tech in experience.technologies)
            for achievement in experience.achievements:
                keywords.update(word.lower().strip(".,") for word in achievement.split())
        for project in self.projects:
            keywords.update(tech.lower() for tech in project.technologies)
            for achievement in project.achievements:
                keywords.update(word.lower().strip(".,") for word in achievement.split())
        return {keyword for keyword in keywords if keyword}

    @staticmethod
    def _iter_lower(words: Iterable[str]) -> set[str]:
        return {word.lower().strip(".,") for word in words if word}
