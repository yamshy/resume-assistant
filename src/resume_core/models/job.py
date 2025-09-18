from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .profile import SkillCategory


class ResponsibilityLevel(str, Enum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"


class JobRequirement(BaseModel):
    model_config = ConfigDict(extra="ignore")

    skill: str
    importance: int = Field(ge=1, le=5)
    category: SkillCategory
    is_required: bool = True
    context: str


class JobAnalysis(BaseModel):
    model_config = ConfigDict(extra="ignore")

    company_name: str
    job_title: str
    department: Optional[str] = None
    location: str = "Not specified"
    remote_policy: Optional[str] = None
    requirements: List[JobRequirement] = Field(default_factory=list)
    key_responsibilities: List[str] = Field(default_factory=list)
    company_culture: str = "Not specified"
    role_level: ResponsibilityLevel = ResponsibilityLevel.MID
    industry: str = "technology"
    salary_range: Optional[str] = None
    benefits: List[str] = Field(default_factory=list)
    preferred_qualifications: List[str] = Field(default_factory=list)

