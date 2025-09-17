# Data Model: Resume Tailoring System

*Generated during Phase 1 of implementation planning*

## Core Entities

### 1. User Profile
**Purpose**: Comprehensive professional data store for single user
**Storage**: Local JSON file (`~/.resume-assistant/profile.json`)

```python
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict
from datetime import date
from enum import Enum

class ContactInfo(BaseModel):
    name: str = Field(description="Full name")
    email: EmailStr = Field(description="Email address")
    phone: Optional[str] = Field(default=None, description="Phone number")
    location: str = Field(description="City, State or City, Country")
    linkedin: Optional[str] = Field(default=None, description="LinkedIn profile URL")
    portfolio: Optional[str] = Field(default=None, description="Portfolio website URL")

class WorkExperience(BaseModel):
    position: str = Field(description="Job title")
    company: str = Field(description="Company name")
    location: str = Field(description="Work location")
    start_date: date = Field(description="Start date")
    end_date: Optional[date] = Field(default=None, description="End date (None if current)")
    description: str = Field(description="Role description and responsibilities")
    achievements: List[str] = Field(description="Quantified achievements with metrics")
    technologies: List[str] = Field(default=[], description="Technologies used")

class Education(BaseModel):
    degree: str = Field(description="Degree type and field")
    institution: str = Field(description="School/university name")
    location: str = Field(description="School location")
    graduation_date: date = Field(description="Graduation date")
    gpa: Optional[float] = Field(default=None, description="GPA if noteworthy")
    honors: List[str] = Field(default=[], description="Academic honors and awards")
    relevant_coursework: List[str] = Field(default=[], description="Relevant courses")

class SkillCategory(str, Enum):
    TECHNICAL = "technical"
    SOFT = "soft"
    LANGUAGE = "language"
    CERTIFICATION = "certification"

class Skill(BaseModel):
    name: str = Field(description="Skill name")
    category: SkillCategory = Field(description="Skill category")
    proficiency: int = Field(ge=1, le=5, description="Proficiency level 1-5")
    years_experience: Optional[int] = Field(default=None, description="Years of experience")

class Project(BaseModel):
    name: str = Field(description="Project name")
    description: str = Field(description="Project description")
    technologies: List[str] = Field(description="Technologies used")
    start_date: date = Field(description="Start date")
    end_date: Optional[date] = Field(default=None, description="End date (None if ongoing)")
    url: Optional[str] = Field(default=None, description="Project URL")
    achievements: List[str] = Field(description="Key achievements and outcomes")

class Publication(BaseModel):
    title: str = Field(description="Publication title")
    venue: str = Field(description="Journal, conference, or platform")
    date: date = Field(description="Publication date")
    url: Optional[str] = Field(default=None, description="Publication URL")
    authors: List[str] = Field(description="Co-authors")

class Award(BaseModel):
    title: str = Field(description="Award title")
    organization: str = Field(description="Awarding organization")
    date: date = Field(description="Award date")
    description: str = Field(description="Award description")

class VolunteerWork(BaseModel):
    role: str = Field(description="Volunteer role")
    organization: str = Field(description="Organization name")
    start_date: date = Field(description="Start date")
    end_date: Optional[date] = Field(default=None, description="End date (None if ongoing)")
    description: str = Field(description="Role description and impact")

class Language(BaseModel):
    name: str = Field(description="Language name")
    proficiency: str = Field(description="Proficiency level (native, fluent, conversational, basic)")

class UserProfile(BaseModel):
    version: str = Field(default="1.0", description="Schema version")
    metadata: Dict[str, str] = Field(description="Creation/update timestamps")
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
```

### 2. Job Posting Analysis
**Purpose**: Structured representation of job requirements extracted by Job Analysis Agent

```python
class JobRequirement(BaseModel):
    skill: str = Field(description="Required skill or qualification")
    importance: int = Field(ge=1, le=5, description="Importance level 1-5")
    category: SkillCategory = Field(description="Skill category")
    is_required: bool = Field(description="True if hard requirement, False if preferred")
    context: str = Field(description="Context where this requirement was mentioned")

class ResponsibilityLevel(str, Enum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"

class JobAnalysis(BaseModel):
    company_name: str = Field(description="Company name")
    job_title: str = Field(description="Job title")
    department: Optional[str] = Field(default=None, description="Department or team")
    location: str = Field(description="Job location")
    remote_policy: Optional[str] = Field(default=None, description="Remote work policy")
    requirements: List[JobRequirement] = Field(description="Extracted job requirements")
    key_responsibilities: List[str] = Field(description="Main job responsibilities")
    company_culture: str = Field(description="Company culture description")
    role_level: ResponsibilityLevel = Field(description="Role seniority level")
    industry: str = Field(description="Industry sector")
    salary_range: Optional[str] = Field(default=None, description="Salary range if mentioned")
    benefits: List[str] = Field(default=[], description="Benefits mentioned")
    preferred_qualifications: List[str] = Field(default=[], description="Nice-to-have qualifications")
```

### 3. Profile Matching Results
**Purpose**: Results from Profile Matching Agent comparing job requirements with user profile

```python
class SkillMatch(BaseModel):
    skill_name: str = Field(description="Skill name")
    job_importance: int = Field(ge=1, le=5, description="Importance in job posting")
    user_proficiency: int = Field(ge=0, le=5, description="User proficiency (0 if not found)")
    match_score: float = Field(ge=0, le=1, description="Match score 0-1")
    evidence: List[str] = Field(description="Evidence from user profile")

class ExperienceMatch(BaseModel):
    job_responsibility: str = Field(description="Job responsibility")
    matching_experiences: List[str] = Field(description="Matching user experiences")
    relevance_score: float = Field(ge=0, le=1, description="Relevance score 0-1")

class MatchingResult(BaseModel):
    overall_match_score: float = Field(ge=0, le=1, description="Overall match score")
    skill_matches: List[SkillMatch] = Field(description="Individual skill match details")
    experience_matches: List[ExperienceMatch] = Field(description="Experience alignment details")
    missing_requirements: List[JobRequirement] = Field(description="Requirements user doesn't meet")
    strength_areas: List[str] = Field(description="Areas where user exceeds requirements")
    transferable_skills: List[str] = Field(description="Skills that could transfer to missing areas")
    recommendations: List[str] = Field(description="Specific improvement recommendations")
    confidence_score: float = Field(ge=0, le=1, description="Confidence in analysis")
```

### 4. Resume Optimization
**Purpose**: Tailored resume content generated by Resume Generation Agent

```python
class ResumeSection(str, Enum):
    SUMMARY = "summary"
    EXPERIENCE = "experience"
    SKILLS = "skills"
    EDUCATION = "education"
    PROJECTS = "projects"
    ACHIEVEMENTS = "achievements"

class ContentOptimization(BaseModel):
    section: ResumeSection = Field(description="Resume section being optimized")
    original_content: str = Field(description="Original content from user profile")
    optimized_content: str = Field(description="Tailored content for this job")
    optimization_reason: str = Field(description="Explanation of changes made")
    keywords_added: List[str] = Field(description="Job-specific keywords incorporated")
    match_improvement: float = Field(ge=0, le=1, description="Expected match score improvement")

class TailoredResume(BaseModel):
    job_title: str = Field(description="Target job title")
    company_name: str = Field(description="Target company name")
    optimizations: List[ContentOptimization] = Field(description="Section-by-section optimizations")
    full_resume_markdown: str = Field(description="Complete tailored resume in Markdown")
    summary_of_changes: str = Field(description="High-level summary of modifications")
    estimated_match_score: float = Field(ge=0, le=1, description="Estimated overall match score")
    generation_timestamp: str = Field(description="When resume was generated")
```

### 5. Validation Results
**Purpose**: Accuracy and quality validation from Validation Agent

```python
class ValidationIssue(BaseModel):
    severity: str = Field(description="low, medium, high, critical")
    category: str = Field(description="accuracy, consistency, formatting, content")
    description: str = Field(description="Issue description")
    location: str = Field(description="Where in resume this issue occurs")
    suggestion: str = Field(description="How to fix this issue")

class ValidationResult(BaseModel):
    is_valid: bool = Field(description="Overall validation result")
    accuracy_score: float = Field(ge=0, le=1, description="Accuracy against source profile")
    readability_score: float = Field(ge=0, le=1, description="Content readability and flow")
    keyword_optimization_score: float = Field(ge=0, le=1, description="Keyword usage effectiveness")
    issues: List[ValidationIssue] = Field(description="Identified issues")
    strengths: List[str] = Field(description="Validation strengths identified")
    overall_quality_score: float = Field(ge=0, le=1, description="Overall quality rating")
    validation_timestamp: str = Field(description="When validation was performed")
```

### 6. Approval Workflow
**Purpose**: Human-in-the-loop approval process managed by Human Interface Agent

```python
class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"

class ReviewDecision(BaseModel):
    decision: ApprovalStatus = Field(description="User's decision")
    feedback: Optional[str] = Field(default=None, description="User feedback on changes")
    requested_modifications: List[str] = Field(default=[], description="Specific changes requested")
    approved_sections: List[ResumeSection] = Field(default=[], description="Sections user approved")
    rejected_sections: List[ResumeSection] = Field(default=[], description="Sections user rejected")

class ApprovalRequest(BaseModel):
    resume_id: str = Field(description="Unique identifier for this resume version")
    requires_human_review: bool = Field(description="Whether human review is required")
    review_reasons: List[str] = Field(description="Why human review is needed")
    confidence_score: float = Field(ge=0, le=1, description="AI confidence in generated resume")
    risk_factors: List[str] = Field(description="Potential issues identified")
    auto_approve_eligible: bool = Field(description="Whether auto-approval is possible")
    review_deadline: Optional[str] = Field(default=None, description="When review expires")

class ApprovalWorkflow(BaseModel):
    request: ApprovalRequest = Field(description="Initial approval request")
    decision: Optional[ReviewDecision] = Field(default=None, description="User decision")
    iterations: int = Field(default=1, description="Number of revision cycles")
    final_resume: Optional[str] = Field(default=None, description="Final approved resume markdown")
    workflow_status: ApprovalStatus = Field(default=ApprovalStatus.PENDING)
    created_at: str = Field(description="Workflow creation timestamp")
    completed_at: Optional[str] = Field(default=None, description="Workflow completion timestamp")
```

## Entity Relationships

```
UserProfile (1) --> (1) MatchingResult: Profile analyzed against job
JobAnalysis (1) --> (1) MatchingResult: Job requirements matched against profile
MatchingResult (1) --> (1) TailoredResume: Match results used for optimization
TailoredResume (1) --> (1) ValidationResult: Generated resume validated
ValidationResult (1) --> (1) ApprovalWorkflow: Validation triggers approval process
ApprovalWorkflow (1) --> (0..1) TailoredResume: May result in final approved resume
```

## Data Validation Rules

### User Profile Validation
- All dates must be in the past except for current positions (end_date = None)
- Skills proficiency must be 1-5 scale
- Contact email must be valid email format
- Work experience should be in reverse chronological order

### Job Analysis Validation
- Requirements importance must be 1-5 scale
- At least one requirement must be marked as required (is_required = True)
- Role level must match defined enum values

### Matching Validation
- All scores must be 0-1 range
- Skill matches must reference existing skills from job analysis
- Overall match score should align with individual skill/experience scores

### Resume Optimization Validation
- Optimized content must not contradict original profile data
- Keywords added must appear in optimized content
- All resume sections must be valid enum values

### Approval Workflow Validation
- Confidence scores must be 0-1 range
- Review decisions must include feedback for rejected/revision statuses
- Final resume required if status is approved

## Storage Schema

### File Structure
```
~/.resume-assistant/
├── profile.json          # UserProfile
├── sessions/              # Temporary session data
│   ├── job_analysis/     # JobAnalysis results (temp)
│   ├── matching/         # MatchingResult data (temp)
│   ├── generation/       # TailoredResume drafts (temp)
│   └── validation/       # ValidationResult data (temp)
└── exports/              # Final approved resumes
    ├── YYYY-MM-DD_CompanyName_JobTitle.md
    └── ...
```

### Profile JSON Schema
```json
{
  "version": "1.0",
  "metadata": {
    "created_at": "2025-09-17T00:00:00Z",
    "updated_at": "2025-09-17T00:00:00Z"
  },
  "contact": { /* ContactInfo */ },
  "professional_summary": "string",
  "experience": [ /* WorkExperience[] */ ],
  "education": [ /* Education[] */ ],
  "skills": [ /* Skill[] */ ],
  "projects": [ /* Project[] */ ],
  "publications": [ /* Publication[] */ ],
  "awards": [ /* Award[] */ ],
  "volunteer": [ /* VolunteerWork[] */ ],
  "languages": [ /* Language[] */ ]
}
```

## State Transitions

### Resume Generation Workflow
```
UserProfile + JobPosting → JobAnalysis → MatchingResult → TailoredResume → ValidationResult → ApprovalWorkflow → Final Resume
```

### Approval Workflow States
```
PENDING → APPROVED → Final Resume Export
PENDING → NEEDS_REVISION → Modified Resume → PENDING (loop)
PENDING → REJECTED → End Workflow
```

---

*Data model complete - ready for API contract generation*