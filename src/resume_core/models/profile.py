from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""


class ExperienceAchievement(BaseModel):
    description: str
    metrics: str | None = None


class WorkExperience(BaseModel):
    role: str
    company: str
    start_date: str
    end_date: str | None = None
    achievements: list[ExperienceAchievement] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)


class EducationEntry(BaseModel):
    degree: str
    institution: str
    start_date: str | None = None
    end_date: str | None = None
    honors: str | None = None


class SkillEntry(BaseModel):
    name: str
    level: str | None = None


class ProjectEntry(BaseModel):
    name: str
    description: str
    skills: list[str] = Field(default_factory=list)
    outcomes: str | None = None


class CertificationEntry(BaseModel):
    name: str
    authority: str | None = None
    year: int | None = None


class LanguageEntry(BaseModel):
    name: str
    proficiency: str | None = None


class UserProfile(BaseModel):
    contact: ContactInfo = Field(default_factory=ContactInfo)
    summary: str = ""
    experience: list[WorkExperience] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    skills: list[SkillEntry] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    certifications: list[CertificationEntry] = Field(default_factory=list)
    languages: list[LanguageEntry] = Field(default_factory=list)

    def merge_overrides(self, overrides: dict[str, Any] | None) -> "UserProfile":
        if not overrides:
            return self
        updated = self.model_dump()
        for key, value in overrides.items():
            if key in {
                "experience",
                "education",
                "skills",
                "projects",
                "certifications",
                "languages",
            }:
                updated[key] = value
            else:
                updated[key] = value
        return UserProfile.model_validate(updated)

    @classmethod
    def empty(cls) -> "UserProfile":
        return cls()
