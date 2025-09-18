from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class SkillCategory(str, Enum):
    TECHNICAL = "technical"
    SOFT = "soft"
    LANGUAGE = "language"
    CERTIFICATION = "certification"


class ContactInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Primary email address")
    location: str = Field(..., description="Location such as city and state")
    phone: Optional[str] = Field(default=None, description="Optional phone number")
    linkedin: Optional[HttpUrl] = Field(default=None, description="LinkedIn profile URL")
    portfolio: Optional[HttpUrl] = Field(default=None, description="Portfolio URL")


class WorkExperience(BaseModel):
    model_config = ConfigDict(extra="ignore")

    position: str
    company: str
    location: str
    start_date: date
    end_date: Optional[date] = None
    description: str
    achievements: List[str]
    technologies: List[str] = Field(default_factory=list)


class Education(BaseModel):
    model_config = ConfigDict(extra="ignore")

    degree: str
    institution: str
    location: str
    graduation_date: date
    gpa: Optional[float] = None
    honors: List[str] = Field(default_factory=list)
    relevant_coursework: List[str] = Field(default_factory=list)


class Skill(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    category: SkillCategory
    proficiency: int = Field(ge=1, le=5)
    years_experience: Optional[int] = None


class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    description: str
    technologies: List[str]
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    url: Optional[HttpUrl] = None


class Publication(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str
    venue: str
    date: date
    url: Optional[HttpUrl] = None
    authors: List[str] = Field(default_factory=list)


class Award(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str
    organization: str
    date: date
    description: Optional[str] = None


class VolunteerWork(BaseModel):
    model_config = ConfigDict(extra="ignore")

    role: str
    organization: str
    start_date: date
    end_date: Optional[date] = None
    description: str


class Language(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    proficiency: str


class UserProfile(BaseModel):
    model_config = ConfigDict(extra="ignore")

    version: str = Field(default="1.0", description="Schema version")
    metadata: Dict[str, str] = Field(default_factory=dict)
    contact: ContactInfo
    professional_summary: str
    experience: List[WorkExperience]
    education: List[Education]
    skills: List[Skill]
    projects: List[Project] = Field(default_factory=list)
    publications: List[Publication] = Field(default_factory=list)
    awards: List[Award] = Field(default_factory=list)
    volunteer: List[VolunteerWork] = Field(default_factory=list)
    languages: List[Language] = Field(default_factory=list)

