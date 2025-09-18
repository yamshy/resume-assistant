"""
Comprehensive data validation and schema tests for Resume Assistant models.

Tests all pydantic models for validation, serialization, and agent chain compatibility.
Constitutional compliance: Focus on data integrity across the agent chain.
"""

import pytest
from datetime import date
from typing import Dict, Any
from pydantic import ValidationError

# Import all models from main models package (which re-exports from src)
from models import (
    # Profile models
    ContactInfo,
    WorkExperience,
    Education,
    SkillCategory,
    Skill,
    Project,
    Publication,
    Award,
    VolunteerWork,
    Language,
    UserProfile,
)

# Import job analysis models
from models.job_analysis import (
    JobRequirement,
    ResponsibilityLevel,
    JobAnalysis,
)

# Import matching models from src
from src.models.matching import (
    SkillMatch,
    ExperienceMatch,
    MatchingResult,
)

# Import validation models from src
from src.models.validation import (
    ValidationIssue,
    ValidationWarning,
    ValidationResult,
)

# Import resume optimization models from src
from src.models.resume_optimization import (
    ContentOptimization,
    TailoredResume,
)

# Import approval models from src
from src.models.approval import (
    ResumeSection,
    ApprovalStatus,
    ReviewDecision,
    ApprovalRequest,
    ApprovalWorkflow,
)


# Test Fixtures for reusable test data
@pytest.fixture
def valid_contact_info() -> Dict[str, Any]:
    """Valid contact information data."""
    return {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "+1-555-0123",
        "location": "San Francisco, CA",
        "linkedin": "https://linkedin.com/in/johndoe",
        "portfolio": "https://johndoe.dev"
    }


@pytest.fixture
def valid_work_experience() -> Dict[str, Any]:
    """Valid work experience data."""
    return {
        "position": "Senior Software Engineer",
        "company": "Tech Corp",
        "location": "San Francisco, CA",
        "start_date": date(2020, 1, 15),
        "end_date": date(2023, 6, 30),
        "description": "Led development of microservices architecture",
        "achievements": [
            "Reduced API response time by 40%",
            "Mentored 5 junior developers"
        ],
        "technologies": ["Python", "FastAPI", "PostgreSQL"]
    }


@pytest.fixture
def valid_education() -> Dict[str, Any]:
    """Valid education data."""
    return {
        "degree": "Bachelor of Science in Computer Science",
        "institution": "Stanford University",
        "location": "Stanford, CA",
        "graduation_date": date(2019, 6, 15),
        "gpa": 3.8,
        "honors": ["Magna Cum Laude", "Dean's List"],
        "relevant_coursework": ["Data Structures", "Algorithms", "Machine Learning"]
    }


@pytest.fixture
def valid_skill() -> Dict[str, Any]:
    """Valid skill data."""
    return {
        "name": "Python",
        "category": SkillCategory.TECHNICAL,
        "proficiency": 4,
        "years_experience": 5
    }


@pytest.fixture
def valid_user_profile(valid_contact_info, valid_work_experience, valid_education, valid_skill) -> Dict[str, Any]:
    """Valid complete user profile data."""
    return {
        "version": "1.0",
        "metadata": {
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-15T12:00:00Z"
        },
        "contact": valid_contact_info,
        "professional_summary": "Experienced software engineer with expertise in backend development",
        "experience": [valid_work_experience],
        "education": [valid_education],
        "skills": [valid_skill],
        "projects": [],
        "publications": [],
        "awards": [],
        "volunteer": [],
        "languages": []
    }


@pytest.fixture
def valid_job_requirement() -> Dict[str, Any]:
    """Valid job requirement data."""
    return {
        "skill": "Python",
        "importance": 4,
        "category": SkillCategory.TECHNICAL,
        "is_required": True,
        "context": "Required for backend development tasks"
    }


@pytest.fixture
def valid_job_analysis(valid_job_requirement) -> Dict[str, Any]:
    """Valid job analysis data."""
    return {
        "company_name": "Tech Startup Inc",
        "job_title": "Senior Python Developer",
        "department": "Engineering",
        "location": "Remote",
        "remote_policy": "Fully remote",
        "requirements": [valid_job_requirement],
        "key_responsibilities": [
            "Develop and maintain backend services",
            "Optimize database performance"
        ],
        "company_culture": "Fast-paced startup environment with emphasis on innovation",
        "role_level": ResponsibilityLevel.SENIOR,
        "industry": "Technology",
        "salary_range": "$120,000 - $160,000",
        "benefits": ["Health insurance", "401k matching", "Flexible PTO"],
        "preferred_qualifications": ["AWS experience", "Docker knowledge"],
        "analysis_timestamp": "2025-09-18T12:00:00Z"
    }


# Profile Models Tests
class TestContactInfo:
    """Test ContactInfo model validation and serialization."""

    def test_valid_contact_info(self, valid_contact_info):
        """Test valid contact info creation and validation."""
        contact = ContactInfo(**valid_contact_info)
        assert contact.name == "John Doe"
        assert contact.email == "john.doe@example.com"
        assert contact.phone == "+1-555-0123"
        assert contact.location == "San Francisco, CA"
        assert contact.linkedin == "https://linkedin.com/in/johndoe"
        assert contact.portfolio == "https://johndoe.dev"

    def test_required_fields_validation(self):
        """Test that required fields are properly validated."""
        with pytest.raises(ValidationError) as exc_info:
            ContactInfo(email="john@example.com", location="SF, CA")  # Missing name

        assert "name" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            ContactInfo(name="John Doe", location="SF, CA")  # Missing email

        assert "email" in str(exc_info.value)

    def test_email_validation(self):
        """Test email format validation."""
        with pytest.raises(ValidationError) as exc_info:
            ContactInfo(
                name="John Doe",
                email="invalid-email",
                location="SF, CA"
            )

        assert "email" in str(exc_info.value).lower()

    def test_optional_fields(self):
        """Test that optional fields work correctly."""
        contact = ContactInfo(
            name="Jane Doe",
            email="jane@example.com",
            location="NYC, NY"
        )
        assert contact.phone is None
        assert contact.linkedin is None
        assert contact.portfolio is None

    def test_json_serialization(self, valid_contact_info):
        """Test JSON serialization and deserialization."""
        contact = ContactInfo(**valid_contact_info)
        json_data = contact.model_dump()

        # Verify serialization
        assert isinstance(json_data, dict)
        assert json_data["name"] == "John Doe"
        assert json_data["email"] == "john.doe@example.com"

        # Verify deserialization
        contact_restored = ContactInfo(**json_data)
        assert contact_restored.name == contact.name
        assert contact_restored.email == contact.email


class TestWorkExperience:
    """Test WorkExperience model validation and serialization."""

    def test_valid_work_experience(self, valid_work_experience):
        """Test valid work experience creation."""
        experience = WorkExperience(**valid_work_experience)
        assert experience.position == "Senior Software Engineer"
        assert experience.company == "Tech Corp"
        assert experience.start_date == date(2020, 1, 15)
        assert experience.end_date == date(2023, 6, 30)
        assert len(experience.achievements) == 2
        assert len(experience.technologies) == 3

    def test_current_position_no_end_date(self, valid_work_experience):
        """Test work experience without end date (current position)."""
        valid_work_experience["end_date"] = None
        experience = WorkExperience(**valid_work_experience)
        assert experience.end_date is None

    def test_date_validation(self, valid_work_experience):
        """Test date field validation."""
        # Test invalid date type
        with pytest.raises(ValidationError):
            valid_work_experience["start_date"] = "invalid-date"
            WorkExperience(**valid_work_experience)

    def test_required_fields(self):
        """Test required field validation."""
        with pytest.raises(ValidationError) as exc_info:
            WorkExperience(company="Tech Corp", location="SF")  # Missing position
        assert "position" in str(exc_info.value)

    def test_json_serialization(self, valid_work_experience):
        """Test JSON serialization with date handling."""
        experience = WorkExperience(**valid_work_experience)
        json_data = experience.model_dump(mode='json')

        # Dates should be serialized as strings in JSON mode
        assert isinstance(json_data["start_date"], str)
        assert json_data["start_date"] == "2020-01-15"

        # Verify round-trip serialization
        experience_restored = WorkExperience.model_validate(json_data)
        assert experience_restored.start_date == experience.start_date


class TestEducation:
    """Test Education model validation and serialization."""

    def test_valid_education(self, valid_education):
        """Test valid education creation."""
        education = Education(**valid_education)
        assert education.degree == "Bachelor of Science in Computer Science"
        assert education.institution == "Stanford University"
        assert education.gpa == 3.8
        assert len(education.honors) == 2
        assert len(education.relevant_coursework) == 3

    def test_optional_gpa(self, valid_education):
        """Test that GPA is optional."""
        valid_education["gpa"] = None
        education = Education(**valid_education)
        assert education.gpa is None

    def test_empty_lists_default(self, valid_education):
        """Test default empty lists for optional fields."""
        del valid_education["honors"]
        del valid_education["relevant_coursework"]
        education = Education(**valid_education)
        assert education.honors == []
        assert education.relevant_coursework == []


class TestSkillCategory:
    """Test SkillCategory enum validation."""

    def test_valid_categories(self):
        """Test all valid skill categories."""
        assert SkillCategory.TECHNICAL == "technical"
        assert SkillCategory.SOFT == "soft"
        assert SkillCategory.LANGUAGE == "language"
        assert SkillCategory.CERTIFICATION == "certification"

    def test_enum_serialization(self):
        """Test enum serialization behavior."""
        category = SkillCategory.TECHNICAL
        assert category.value == "technical"
        assert str(category) == "SkillCategory.TECHNICAL"


class TestSkill:
    """Test Skill model validation and serialization."""

    def test_valid_skill(self, valid_skill):
        """Test valid skill creation."""
        skill = Skill(**valid_skill)
        assert skill.name == "Python"
        assert skill.category == SkillCategory.TECHNICAL
        assert skill.proficiency == 4
        assert skill.years_experience == 5

    def test_proficiency_constraints(self, valid_skill):
        """Test proficiency level constraints (1-5)."""
        # Test valid range
        for level in range(1, 6):
            valid_skill["proficiency"] = level
            skill = Skill(**valid_skill)
            assert skill.proficiency == level

        # Test invalid range
        with pytest.raises(ValidationError):
            valid_skill["proficiency"] = 0
            Skill(**valid_skill)

        with pytest.raises(ValidationError):
            valid_skill["proficiency"] = 6
            Skill(**valid_skill)

    def test_optional_years_experience(self, valid_skill):
        """Test that years_experience is optional."""
        valid_skill["years_experience"] = None
        skill = Skill(**valid_skill)
        assert skill.years_experience is None


class TestProject:
    """Test Project model validation and serialization."""

    def test_valid_project(self):
        """Test valid project creation."""
        project_data = {
            "name": "Resume Assistant",
            "description": "AI-powered resume tailoring system",
            "technologies": ["Python", "FastAPI", "pydanticAI"],
            "start_date": date(2024, 1, 1),
            "end_date": date(2024, 6, 30),
            "url": "https://github.com/user/resume-assistant",
            "achievements": [
                "Reduced resume creation time by 80%",
                "Achieved 95% user satisfaction rating"
            ]
        }
        project = Project(**project_data)
        assert project.name == "Resume Assistant"
        assert len(project.technologies) == 3
        assert len(project.achievements) == 2

    def test_ongoing_project(self):
        """Test project without end date (ongoing)."""
        project_data = {
            "name": "Open Source Project",
            "description": "Contributing to open source",
            "technologies": ["Python"],
            "start_date": date(2024, 1, 1),
            "achievements": ["100+ commits"]
        }
        project = Project(**project_data)
        assert project.end_date is None


class TestUserProfile:
    """Test UserProfile model validation and serialization."""

    def test_valid_user_profile(self, valid_user_profile):
        """Test valid user profile creation."""
        profile = UserProfile(**valid_user_profile)
        assert profile.version == "1.0"
        assert isinstance(profile.contact, ContactInfo)
        assert len(profile.experience) == 1
        assert len(profile.education) == 1
        assert len(profile.skills) == 1

    def test_default_empty_lists(self, valid_user_profile):
        """Test that optional list fields default to empty."""
        # Remove optional list fields
        del valid_user_profile["projects"]
        del valid_user_profile["publications"]
        del valid_user_profile["awards"]
        del valid_user_profile["volunteer"]
        del valid_user_profile["languages"]

        profile = UserProfile(**valid_user_profile)
        assert profile.projects == []
        assert profile.publications == []
        assert profile.awards == []
        assert profile.volunteer == []
        assert profile.languages == []

    def test_nested_model_validation(self, valid_user_profile):
        """Test that nested models are validated properly."""
        # Invalid contact info should fail
        valid_user_profile["contact"]["email"] = "invalid-email"
        with pytest.raises(ValidationError) as exc_info:
            UserProfile(**valid_user_profile)
        assert "email" in str(exc_info.value).lower()

    def test_comprehensive_json_serialization(self, valid_user_profile):
        """Test complete JSON serialization of user profile."""
        profile = UserProfile(**valid_user_profile)
        json_data = profile.model_dump(mode='json')

        # Verify structure
        assert "contact" in json_data
        assert "experience" in json_data
        assert "education" in json_data
        assert "skills" in json_data

        # Verify nested serialization
        assert isinstance(json_data["contact"], dict)
        assert isinstance(json_data["experience"], list)

        # Verify round-trip
        profile_restored = UserProfile.model_validate(json_data)
        assert profile_restored.contact.name == profile.contact.name
        assert len(profile_restored.experience) == len(profile.experience)


# Job Analysis Models Tests
class TestJobRequirement:
    """Test JobRequirement model validation and serialization."""

    def test_valid_job_requirement(self, valid_job_requirement):
        """Test valid job requirement creation."""
        requirement = JobRequirement(**valid_job_requirement)
        assert requirement.skill == "Python"
        assert requirement.importance == 4
        assert requirement.category == SkillCategory.TECHNICAL
        assert requirement.is_required is True
        assert requirement.context == "Required for backend development tasks"

    def test_importance_constraints(self, valid_job_requirement):
        """Test importance level constraints (1-5)."""
        # Test valid range
        for level in range(1, 6):
            valid_job_requirement["importance"] = level
            requirement = JobRequirement(**valid_job_requirement)
            assert requirement.importance == level

        # Test invalid range
        with pytest.raises(ValidationError):
            valid_job_requirement["importance"] = 0
            JobRequirement(**valid_job_requirement)

        with pytest.raises(ValidationError):
            valid_job_requirement["importance"] = 6
            JobRequirement(**valid_job_requirement)


class TestResponsibilityLevel:
    """Test ResponsibilityLevel enum validation."""

    def test_valid_levels(self):
        """Test all valid responsibility levels."""
        assert ResponsibilityLevel.JUNIOR == "junior"
        assert ResponsibilityLevel.MID == "mid"
        assert ResponsibilityLevel.SENIOR == "senior"
        assert ResponsibilityLevel.LEAD == "lead"
        assert ResponsibilityLevel.EXECUTIVE == "executive"


class TestJobAnalysis:
    """Test JobAnalysis model validation and serialization."""

    def test_valid_job_analysis(self, valid_job_analysis):
        """Test valid job analysis creation."""
        analysis = JobAnalysis(**valid_job_analysis)
        assert analysis.company_name == "Tech Startup Inc"
        assert analysis.job_title == "Senior Python Developer"
        assert analysis.role_level == ResponsibilityLevel.SENIOR
        assert len(analysis.requirements) == 1
        assert len(analysis.key_responsibilities) == 2
        assert len(analysis.benefits) == 3

    def test_optional_fields(self, valid_job_analysis):
        """Test optional fields in job analysis."""
        # Remove optional fields
        del valid_job_analysis["department"]
        del valid_job_analysis["remote_policy"]
        del valid_job_analysis["salary_range"]

        analysis = JobAnalysis(**valid_job_analysis)
        assert analysis.department is None
        assert analysis.remote_policy is None
        assert analysis.salary_range is None

    def test_nested_requirements_validation(self, valid_job_analysis):
        """Test that nested job requirements are validated."""
        # Invalid requirement should fail
        valid_job_analysis["requirements"][0]["importance"] = 10  # Invalid range
        with pytest.raises(ValidationError):
            JobAnalysis(**valid_job_analysis)


# Matching Models Tests
class TestSkillMatch:
    """Test SkillMatch model validation and serialization."""

    def test_valid_skill_match(self):
        """Test valid skill match creation."""
        match_data = {
            "skill_name": "Python",
            "job_importance": 5,
            "user_proficiency": 4,
            "match_score": 0.8,
            "evidence": ["5 years experience", "Used in recent projects"]
        }
        match = SkillMatch(**match_data)
        assert match.skill_name == "Python"
        assert match.job_importance == 5
        assert match.user_proficiency == 4
        assert match.match_score == 0.8
        assert len(match.evidence) == 2

    def test_score_constraints(self):
        """Test match score constraints (0-1)."""
        match_data = {
            "skill_name": "Python",
            "job_importance": 5,
            "user_proficiency": 4,
            "match_score": 1.0,  # Valid upper bound
            "evidence": ["Evidence"]
        }
        match = SkillMatch(**match_data)
        assert match.match_score == 1.0

        # Test invalid range
        with pytest.raises(ValidationError):
            match_data["match_score"] = 1.5
            SkillMatch(**match_data)

    def test_proficiency_constraints(self):
        """Test user proficiency constraints (0-5, where 0 means not found)."""
        match_data = {
            "skill_name": "Python",
            "job_importance": 5,
            "user_proficiency": 0,  # Valid - skill not found
            "match_score": 0.0,
            "evidence": []
        }
        match = SkillMatch(**match_data)
        assert match.user_proficiency == 0

        # Test invalid range
        with pytest.raises(ValidationError):
            match_data["user_proficiency"] = 6
            SkillMatch(**match_data)


class TestExperienceMatch:
    """Test ExperienceMatch model validation and serialization."""

    def test_valid_experience_match(self):
        """Test valid experience match creation."""
        match_data = {
            "job_responsibility": "Lead backend development",
            "matching_experiences": [
                "Led team of 5 developers at Tech Corp",
                "Architected microservices at Previous Company"
            ],
            "relevance_score": 0.9
        }
        match = ExperienceMatch(**match_data)
        assert match.job_responsibility == "Lead backend development"
        assert len(match.matching_experiences) == 2
        assert match.relevance_score == 0.9

    def test_relevance_score_constraints(self):
        """Test relevance score constraints (0-1)."""
        match_data = {
            "job_responsibility": "Development",
            "matching_experiences": ["Experience"],
            "relevance_score": 0.0  # Valid lower bound
        }
        match = ExperienceMatch(**match_data)
        assert match.relevance_score == 0.0

        # Test invalid range
        with pytest.raises(ValidationError):
            match_data["relevance_score"] = -0.1
            ExperienceMatch(**match_data)


class TestMatchingResult:
    """Test MatchingResult model validation and serialization."""

    def test_valid_matching_result(self, valid_job_requirement):
        """Test valid matching result creation."""
        skill_match = SkillMatch(
            skill_name="Python",
            job_importance=5,
            user_proficiency=4,
            match_score=0.8,
            evidence=["5 years experience"]
        )

        experience_match = ExperienceMatch(
            job_responsibility="Backend development",
            matching_experiences=["Python backend at Tech Corp"],
            relevance_score=0.9
        )

        result_data = {
            "overall_match_score": 0.85,
            "skill_matches": [skill_match.model_dump()],
            "experience_matches": [experience_match.model_dump()],
            "missing_requirements": [valid_job_requirement],
            "strength_areas": ["Python expertise", "Leadership experience"],
            "transferable_skills": ["Problem solving", "Team collaboration"],
            "recommendations": ["Learn Docker", "Get AWS certification"],
            "confidence_score": 0.9
        }

        result = MatchingResult(**result_data)
        assert result.overall_match_score == 0.85
        assert len(result.skill_matches) == 1
        assert len(result.experience_matches) == 1
        assert len(result.missing_requirements) == 1
        assert result.confidence_score == 0.9

    def test_score_constraints(self):
        """Test all score field constraints (0-1)."""
        minimal_data = {
            "overall_match_score": 0.5,
            "skill_matches": [],
            "experience_matches": [],
            "missing_requirements": [],
            "strength_areas": [],
            "transferable_skills": [],
            "recommendations": [],
            "confidence_score": 0.8
        }

        result = MatchingResult(**minimal_data)
        assert result.overall_match_score == 0.5
        assert result.confidence_score == 0.8

        # Test invalid scores
        with pytest.raises(ValidationError):
            minimal_data["overall_match_score"] = 1.1
            MatchingResult(**minimal_data)


# Validation Models Tests
class TestValidationIssue:
    """Test ValidationIssue model validation and serialization."""

    def test_valid_validation_issue(self):
        """Test valid validation issue creation."""
        issue_data = {
            "severity": "high",
            "category": "accuracy",
            "description": "Work experience dates overlap",
            "location": "Experience section, entry 2",
            "suggestion": "Verify and correct employment dates",
            "error_type": "date_conflict"
        }
        issue = ValidationIssue(**issue_data)
        assert issue.severity == "high"
        assert issue.category == "accuracy"
        assert issue.description == "Work experience dates overlap"
        assert issue.location == "Experience section, entry 2"
        assert issue.suggestion == "Verify and correct employment dates"
        assert issue.error_type == "date_conflict"


class TestValidationWarning:
    """Test ValidationWarning model validation and serialization."""

    def test_valid_validation_warning(self):
        """Test valid validation warning creation."""
        warning_data = {
            "severity": "medium",
            "category": "formatting",
            "description": "Inconsistent date formatting",
            "location": "Education section",
            "suggestion": "Use consistent MM/YYYY format",
            "warning_type": "formatting_inconsistency"
        }
        warning = ValidationWarning(**warning_data)
        assert warning.severity == "medium"
        assert warning.category == "formatting"
        assert warning.warning_type == "formatting_inconsistency"


class TestValidationResult:
    """Test ValidationResult model validation and serialization."""

    def test_valid_validation_result(self):
        """Test valid validation result creation."""
        issue = ValidationIssue(
            severity="medium",
            category="accuracy",
            description="Minor discrepancy",
            location="Skills section",
            suggestion="Verify skill level",
            error_type="skill_mismatch"
        )

        warning = ValidationWarning(
            severity="low",
            category="style",
            description="Long sentence",
            location="Summary",
            suggestion="Break into shorter sentences",
            warning_type="readability"
        )

        result_data = {
            "is_valid": True,
            "accuracy_score": 0.92,
            "readability_score": 0.88,
            "keyword_optimization_score": 0.85,
            "issues": [issue.model_dump()],
            "strengths": ["Strong technical skills", "Clear achievements"],
            "overall_quality_score": 0.90,
            "validation_timestamp": "2024-01-15T12:00:00Z",
            "confidence": 0.95,
            "errors": [],
            "warnings": [warning.model_dump()]
        }

        result = ValidationResult(**result_data)
        assert result.is_valid is True
        assert result.accuracy_score == 0.92
        assert result.confidence == 0.95
        assert len(result.issues) == 1
        assert len(result.warnings) == 1

    def test_score_constraints(self):
        """Test all score field constraints (0-1)."""
        minimal_data = {
            "is_valid": False,
            "accuracy_score": 0.0,
            "readability_score": 1.0,
            "keyword_optimization_score": 0.5,
            "issues": [],
            "strengths": [],
            "overall_quality_score": 0.3,
            "validation_timestamp": "2024-01-15T12:00:00Z",
            "confidence": 0.7,
            "errors": [],
            "warnings": []
        }

        result = ValidationResult(**minimal_data)
        assert result.accuracy_score == 0.0
        assert result.readability_score == 1.0

        # Test invalid scores
        with pytest.raises(ValidationError):
            minimal_data["accuracy_score"] = 1.5
            ValidationResult(**minimal_data)


# Resume Optimization Models Tests
class TestContentOptimization:
    """Test ContentOptimization model validation and serialization."""

    def test_valid_content_optimization(self):
        """Test valid content optimization creation."""
        optimization_data = {
            "section": ResumeSection.EXPERIENCE,
            "original_content": "Developed software applications",
            "optimized_content": "Developed Python microservices using FastAPI for high-traffic fintech applications",
            "optimization_reason": "Added specific technologies and domain context to match job requirements",
            "keywords_added": ["Python", "FastAPI", "microservices", "fintech"],
            "match_improvement": 0.3
        }
        optimization = ContentOptimization(**optimization_data)
        assert optimization.section == ResumeSection.EXPERIENCE
        assert optimization.original_content == "Developed software applications"
        assert len(optimization.keywords_added) == 4
        assert optimization.match_improvement == 0.3

    def test_match_improvement_constraints(self):
        """Test match improvement score constraints (0-1)."""
        optimization_data = {
            "section": ResumeSection.SKILLS,
            "original_content": "Original",
            "optimized_content": "Optimized",
            "optimization_reason": "Reason",
            "keywords_added": [],
            "match_improvement": 1.0  # Valid upper bound
        }
        optimization = ContentOptimization(**optimization_data)
        assert optimization.match_improvement == 1.0

        # Test invalid range
        with pytest.raises(ValidationError):
            optimization_data["match_improvement"] = 1.5
            ContentOptimization(**optimization_data)


class TestTailoredResume:
    """Test TailoredResume model validation and serialization."""

    def test_valid_tailored_resume(self):
        """Test valid tailored resume creation."""
        optimization = ContentOptimization(
            section=ResumeSection.SUMMARY,
            original_content="Software engineer",
            optimized_content="Senior Python engineer with fintech experience",
            optimization_reason="Added seniority and domain expertise",
            keywords_added=["Senior", "Python", "fintech"],
            match_improvement=0.4
        )

        resume_data = {
            "job_title": "Senior Python Developer",
            "company_name": "FinTech Corp",
            "optimizations": [optimization.model_dump()],
            "full_resume_markdown": "# John Doe\n\n## Summary\nSenior Python engineer...",
            "summary_of_changes": "Enhanced summary with relevant keywords and experience",
            "estimated_match_score": 0.88,
            "generation_timestamp": "2024-01-15T12:00:00Z"
        }

        resume = TailoredResume(**resume_data)
        assert resume.job_title == "Senior Python Developer"
        assert resume.company_name == "FinTech Corp"
        assert len(resume.optimizations) == 1
        assert resume.estimated_match_score == 0.88

    def test_estimated_match_score_constraints(self):
        """Test estimated match score constraints (0-1)."""
        minimal_data = {
            "job_title": "Developer",
            "company_name": "Company",
            "optimizations": [],
            "full_resume_markdown": "# Resume",
            "summary_of_changes": "Changes",
            "estimated_match_score": 0.0,  # Valid lower bound
            "generation_timestamp": "2024-01-15T12:00:00Z"
        }

        resume = TailoredResume(**minimal_data)
        assert resume.estimated_match_score == 0.0

        # Test invalid range
        with pytest.raises(ValidationError):
            minimal_data["estimated_match_score"] = -0.1
            TailoredResume(**minimal_data)


# Approval Models Tests
class TestResumeSection:
    """Test ResumeSection enum validation."""

    def test_valid_sections(self):
        """Test all valid resume sections."""
        assert ResumeSection.SUMMARY == "summary"
        assert ResumeSection.EXPERIENCE == "experience"
        assert ResumeSection.SKILLS == "skills"
        assert ResumeSection.EDUCATION == "education"
        assert ResumeSection.PROJECTS == "projects"
        assert ResumeSection.ACHIEVEMENTS == "achievements"


class TestApprovalStatus:
    """Test ApprovalStatus enum validation."""

    def test_valid_statuses(self):
        """Test all valid approval statuses."""
        assert ApprovalStatus.PENDING == "pending"
        assert ApprovalStatus.APPROVED == "approved"
        assert ApprovalStatus.REJECTED == "rejected"
        assert ApprovalStatus.NEEDS_REVISION == "needs_revision"


class TestReviewDecision:
    """Test ReviewDecision model validation and serialization."""

    def test_valid_review_decision(self):
        """Test valid review decision creation."""
        decision_data = {
            "decision": ApprovalStatus.NEEDS_REVISION,
            "feedback": "Please strengthen the technical skills section",
            "requested_modifications": [
                "Add more specific Python frameworks",
                "Include cloud platform experience"
            ],
            "approved_sections": [ResumeSection.SUMMARY, ResumeSection.EXPERIENCE],
            "rejected_sections": [ResumeSection.SKILLS]
        }
        decision = ReviewDecision(**decision_data)
        assert decision.decision == ApprovalStatus.NEEDS_REVISION
        assert decision.feedback == "Please strengthen the technical skills section"
        assert len(decision.requested_modifications) == 2
        assert len(decision.approved_sections) == 2
        assert len(decision.rejected_sections) == 1

    def test_optional_fields(self):
        """Test that feedback and lists are optional."""
        decision = ReviewDecision(decision=ApprovalStatus.APPROVED)
        assert decision.feedback is None
        assert decision.requested_modifications == []
        assert decision.approved_sections == []
        assert decision.rejected_sections == []


class TestApprovalRequest:
    """Test ApprovalRequest model validation and serialization."""

    def test_valid_approval_request(self):
        """Test valid approval request creation."""
        request_data = {
            "resume_id": "resume_123",
            "requires_human_review": True,
            "review_reasons": ["Low confidence score", "Sensitive industry context"],
            "confidence_score": 0.65,
            "risk_factors": ["Potential skill overstatement", "Date inconsistency"],
            "auto_approve_eligible": False,
            "review_deadline": "2024-01-20T12:00:00Z"
        }
        request = ApprovalRequest(**request_data)
        assert request.resume_id == "resume_123"
        assert request.requires_human_review is True
        assert request.confidence_score == 0.65
        assert request.auto_approve_eligible is False
        assert len(request.review_reasons) == 2
        assert len(request.risk_factors) == 2

    def test_confidence_score_constraints(self):
        """Test confidence score constraints (0-1)."""
        request_data = {
            "resume_id": "test",
            "requires_human_review": False,
            "review_reasons": [],
            "confidence_score": 1.0,  # Valid upper bound
            "risk_factors": [],
            "auto_approve_eligible": True
        }
        request = ApprovalRequest(**request_data)
        assert request.confidence_score == 1.0

        # Test invalid range
        with pytest.raises(ValidationError):
            request_data["confidence_score"] = 1.1
            ApprovalRequest(**request_data)

    def test_optional_deadline(self):
        """Test that review_deadline is optional."""
        request_data = {
            "resume_id": "test",
            "requires_human_review": False,
            "review_reasons": [],
            "confidence_score": 0.9,
            "risk_factors": [],
            "auto_approve_eligible": True
        }
        request = ApprovalRequest(**request_data)
        assert request.review_deadline is None


class TestApprovalWorkflow:
    """Test ApprovalWorkflow model validation and serialization."""

    def test_valid_approval_workflow(self):
        """Test valid approval workflow creation."""
        request = ApprovalRequest(
            resume_id="resume_456",
            requires_human_review=True,
            review_reasons=["Quality check needed"],
            confidence_score=0.75,
            risk_factors=["New user profile"],
            auto_approve_eligible=False
        )

        decision = ReviewDecision(
            decision=ApprovalStatus.APPROVED,
            feedback="Looks good!",
            requested_modifications=[],
            approved_sections=[ResumeSection.SUMMARY],
            rejected_sections=[]
        )

        workflow_data = {
            "request": request.model_dump(),
            "decision": decision.model_dump(),
            "iterations": 2,
            "final_resume": "# Final Resume\n\nApproved content...",
            "workflow_status": ApprovalStatus.APPROVED,
            "created_at": "2024-01-15T10:00:00Z",
            "completed_at": "2024-01-15T14:00:00Z"
        }

        workflow = ApprovalWorkflow(**workflow_data)
        assert isinstance(workflow.request, ApprovalRequest)
        assert isinstance(workflow.decision, ReviewDecision)
        assert workflow.iterations == 2
        assert workflow.workflow_status == ApprovalStatus.APPROVED
        assert workflow.final_resume is not None

    def test_default_values(self):
        """Test default values for optional fields."""
        request = ApprovalRequest(
            resume_id="test",
            requires_human_review=False,
            review_reasons=[],
            confidence_score=0.9,
            risk_factors=[],
            auto_approve_eligible=True
        )

        workflow_data = {
            "request": request.model_dump(),
            "created_at": "2024-01-15T10:00:00Z"
        }

        workflow = ApprovalWorkflow(**workflow_data)
        assert workflow.decision is None
        assert workflow.iterations == 1
        assert workflow.final_resume is None
        assert workflow.workflow_status == ApprovalStatus.PENDING
        assert workflow.completed_at is None


# Cross-Model Compatibility Tests
class TestCrossModelCompatibility:
    """Test data flow compatibility between models in agent chain."""

    def test_job_analysis_to_matching_flow(self, valid_job_analysis, valid_user_profile):
        """Test JobAnalysis output can be used with MatchingResult."""
        # Create job analysis
        analysis = JobAnalysis(**valid_job_analysis)

        # Create user profile
        profile = UserProfile(**valid_user_profile)

        # Verify job requirements can be used in matching
        job_requirements = analysis.requirements
        assert len(job_requirements) > 0

        # Create skill matches based on job requirements
        skill_matches = []
        for req in job_requirements:
            # Find matching skills in user profile
            user_skill = next(
                (skill for skill in profile.skills if skill.name.lower() == req.skill.lower()),
                None
            )

            skill_match = SkillMatch(
                skill_name=req.skill,
                job_importance=req.importance,
                user_proficiency=user_skill.proficiency if user_skill else 0,
                match_score=0.8 if user_skill else 0.0,
                evidence=[f"Found in user profile"] if user_skill else []
            )
            skill_matches.append(skill_match)

        # Create matching result
        matching_result = MatchingResult(
            overall_match_score=0.7,
            skill_matches=[sm.model_dump() for sm in skill_matches],
            experience_matches=[],
            missing_requirements=[req.model_dump() for req in job_requirements if req.is_required],
            strength_areas=[],
            transferable_skills=[],
            recommendations=[],
            confidence_score=0.8
        )

        assert matching_result.overall_match_score == 0.7
        assert len(matching_result.skill_matches) == len(job_requirements)

    def test_matching_to_resume_optimization_flow(self):
        """Test MatchingResult output can be used with TailoredResume."""
        # Create matching result
        skill_match = SkillMatch(
            skill_name="Python",
            job_importance=5,
            user_proficiency=4,
            match_score=0.8,
            evidence=["5 years experience"]
        )

        matching_result = MatchingResult(
            overall_match_score=0.75,
            skill_matches=[skill_match.model_dump()],
            experience_matches=[],
            missing_requirements=[],
            strength_areas=["Python expertise"],
            transferable_skills=[],
            recommendations=["Highlight Python projects"],
            confidence_score=0.85
        )

        # Use matching results to create resume optimizations
        optimizations = []
        for strength in matching_result.strength_areas:
            optimization = ContentOptimization(
                section=ResumeSection.SKILLS,
                original_content="Programming languages: Python, Java",
                optimized_content=f"Expert-level {strength}: 5+ years developing scalable applications",
                optimization_reason=f"Emphasized {strength} based on matching analysis",
                keywords_added=[strength.split()[0]],  # Extract main keyword
                match_improvement=0.2
            )
            optimizations.append(optimization)

        # Create tailored resume
        tailored_resume = TailoredResume(
            job_title="Senior Python Developer",
            company_name="Tech Company",
            optimizations=[opt.model_dump() for opt in optimizations],
            full_resume_markdown="# Optimized Resume Content",
            summary_of_changes="Enhanced skills section based on matching analysis",
            estimated_match_score=matching_result.overall_match_score + 0.1,
            generation_timestamp="2024-01-15T12:00:00Z"
        )

        assert tailored_resume.estimated_match_score == 0.85
        assert len(tailored_resume.optimizations) == 1

    def test_resume_to_validation_flow(self):
        """Test TailoredResume output can be used with ValidationResult."""
        # Create tailored resume
        optimization = ContentOptimization(
            section=ResumeSection.SUMMARY,
            original_content="Software engineer",
            optimized_content="Senior Python engineer with 5+ years experience",
            optimization_reason="Added seniority and experience details",
            keywords_added=["Senior", "Python", "5+ years"],
            match_improvement=0.3
        )

        resume = TailoredResume(
            job_title="Senior Python Developer",
            company_name="Tech Corp",
            optimizations=[optimization.model_dump()],
            full_resume_markdown="# Resume\n\n## Summary\nSenior Python engineer...",
            summary_of_changes="Enhanced with relevant keywords",
            estimated_match_score=0.82,
            generation_timestamp="2024-01-15T12:00:00Z"
        )

        # Validate the resume content
        validation_issues = []

        # Check for potential issues based on optimizations
        for opt_data in resume.optimizations:
            opt = ContentOptimization.model_validate(opt_data)
            if len(opt.keywords_added) > 5:
                issue = ValidationIssue(
                    severity="medium",
                    category="content",
                    description="Too many keywords added to section",
                    location=f"{opt.section.value} section",
                    suggestion="Reduce keyword density for natural flow",
                    error_type="keyword_stuffing"
                )
                validation_issues.append(issue)

        # Create validation result
        validation_result = ValidationResult(
            is_valid=len(validation_issues) == 0,
            accuracy_score=0.9,
            readability_score=0.85,
            keyword_optimization_score=0.8,
            issues=[issue.model_dump() for issue in validation_issues],
            strengths=["Good keyword integration", "Appropriate length"],
            overall_quality_score=0.85,
            validation_timestamp="2024-01-15T12:30:00Z",
            confidence=0.9,
            errors=[],
            warnings=[]
        )

        assert validation_result.is_valid is True
        assert validation_result.overall_quality_score == 0.85

    def test_validation_to_approval_flow(self):
        """Test ValidationResult output can be used with ApprovalWorkflow."""
        # Create validation result
        validation_result = ValidationResult(
            is_valid=True,
            accuracy_score=0.88,
            readability_score=0.92,
            keyword_optimization_score=0.85,
            issues=[],
            strengths=["Clear structure", "Good keyword usage"],
            overall_quality_score=0.88,
            validation_timestamp="2024-01-15T12:00:00Z",
            confidence=0.87,
            errors=[],
            warnings=[]
        )

        # Determine approval eligibility based on validation
        requires_review = validation_result.confidence < 0.9 or not validation_result.is_valid
        auto_approve_eligible = validation_result.overall_quality_score > 0.8 and validation_result.confidence > 0.85

        # Create approval request
        approval_request = ApprovalRequest(
            resume_id="resume_789",
            requires_human_review=requires_review,
            review_reasons=["Confidence score below 0.9"] if requires_review else [],
            confidence_score=validation_result.confidence,
            risk_factors=["Minor validation issues"] if validation_result.issues else [],
            auto_approve_eligible=auto_approve_eligible
        )

        # Create approval workflow
        workflow = ApprovalWorkflow(
            request=approval_request.model_dump(),
            workflow_status=ApprovalStatus.PENDING if requires_review else ApprovalStatus.APPROVED,
            created_at="2024-01-15T12:00:00Z"
        )

        assert workflow.request.confidence_score == validation_result.confidence
        assert workflow.request.auto_approve_eligible == auto_approve_eligible


# JSON Serialization and Deserialization Tests
class TestSerializationPatterns:
    """Test JSON serialization and deserialization patterns across all models."""

    def test_profile_serialization_round_trip(self, valid_user_profile):
        """Test complete user profile serialization round trip."""
        profile = UserProfile(**valid_user_profile)

        # Serialize to JSON
        json_data = profile.model_dump(mode='json')

        # Verify JSON structure
        assert isinstance(json_data, dict)
        assert "contact" in json_data
        assert "experience" in json_data
        assert isinstance(json_data["experience"], list)

        # Verify date serialization
        if json_data["experience"]:
            assert isinstance(json_data["experience"][0]["start_date"], str)

        # Deserialize from JSON
        profile_restored = UserProfile.model_validate(json_data)

        # Verify round trip preservation
        assert profile_restored.contact.name == profile.contact.name
        assert profile_restored.contact.email == profile.contact.email
        assert len(profile_restored.experience) == len(profile.experience)
        if profile_restored.experience:
            assert profile_restored.experience[0].start_date == profile.experience[0].start_date

    def test_enum_serialization_patterns(self):
        """Test enum serialization across different models."""
        # Test SkillCategory enum
        skill = Skill(
            name="Python",
            category=SkillCategory.TECHNICAL,
            proficiency=4
        )
        json_data = skill.model_dump(mode='json')
        assert json_data["category"] == "technical"

        skill_restored = Skill.model_validate(json_data)
        assert skill_restored.category == SkillCategory.TECHNICAL

        # Test ResponsibilityLevel enum
        analysis = JobAnalysis(
            company_name="Test Corp",
            job_title="Developer",
            location="Remote",
            requirements=[],
            key_responsibilities=[],
            company_culture="Great culture",
            role_level=ResponsibilityLevel.SENIOR,
            industry="Tech",
            analysis_timestamp="2024-01-15T12:00:00Z"
        )
        json_data = analysis.model_dump(mode='json')
        assert json_data["role_level"] == "senior"

        analysis_restored = JobAnalysis.model_validate(json_data)
        assert analysis_restored.role_level == ResponsibilityLevel.SENIOR

    def test_nested_model_serialization(self, valid_job_analysis):
        """Test nested model serialization patterns."""
        analysis = JobAnalysis(**valid_job_analysis)

        # Serialize with nested models
        json_data = analysis.model_dump(mode='json')

        # Verify nested structure
        assert isinstance(json_data["requirements"], list)
        if json_data["requirements"]:
            requirement = json_data["requirements"][0]
            assert isinstance(requirement, dict)
            assert "skill" in requirement
            assert "importance" in requirement
            assert "category" in requirement

        # Verify round trip with nested models
        analysis_restored = JobAnalysis.model_validate(json_data)
        assert len(analysis_restored.requirements) == len(analysis.requirements)
        if analysis_restored.requirements:
            original_req = analysis.requirements[0]
            restored_req = analysis_restored.requirements[0]
            assert restored_req.skill == original_req.skill
            assert restored_req.importance == original_req.importance
            assert restored_req.category == original_req.category

    def test_optional_field_serialization(self):
        """Test serialization of models with optional fields."""
        # Create model with some optional fields None
        contact = ContactInfo(
            name="Test User",
            email="test@example.com",
            location="Test City"
            # phone, linkedin, portfolio are None
        )

        json_data = contact.model_dump(mode='json')

        # Optional fields should be included with null values in JSON mode
        assert json_data["phone"] is None
        assert json_data["linkedin"] is None
        assert json_data["portfolio"] is None

        # Verify round trip
        contact_restored = ContactInfo.model_validate(json_data)
        assert contact_restored.phone is None
        assert contact_restored.linkedin is None
        assert contact_restored.portfolio is None

    def test_list_field_serialization(self):
        """Test serialization of models with list fields."""
        # Create model with various list types
        experience = WorkExperience(
            position="Developer",
            company="Tech Corp",
            location="Remote",
            start_date=date(2020, 1, 1),
            description="Development work",
            achievements=["Achievement 1", "Achievement 2"],
            technologies=["Python", "FastAPI"]
        )

        json_data = experience.model_dump(mode='json')

        # Verify list serialization
        assert isinstance(json_data["achievements"], list)
        assert isinstance(json_data["technologies"], list)
        assert len(json_data["achievements"]) == 2
        assert len(json_data["technologies"]) == 2

        # Verify round trip
        experience_restored = WorkExperience.model_validate(json_data)
        assert experience_restored.achievements == experience.achievements
        assert experience_restored.technologies == experience.technologies


# Edge Cases and Boundary Conditions Tests
class TestEdgeCasesAndBoundaryConditions:
    """Test edge cases and boundary conditions for all models."""

    def test_minimum_valid_user_profile(self):
        """Test user profile with minimal required data."""
        minimal_profile = {
            "version": "1.0",
            "metadata": {"created": "2024-01-01"},
            "contact": {
                "name": "A",  # Minimum name
                "email": "a@b.co",  # Minimum valid email
                "location": "X"  # Minimum location
            },
            "professional_summary": "X",  # Minimum summary
            "experience": [],  # Empty but required
            "education": [],   # Empty but required
            "skills": []       # Empty but required
        }

        profile = UserProfile(**minimal_profile)
        assert profile.contact.name == "A"
        assert len(profile.experience) == 0
        assert len(profile.skills) == 0

    def test_maximum_length_strings(self):
        """Test models with very long string values."""
        long_description = "X" * 5000  # Very long description

        experience = WorkExperience(
            position="Senior Software Engineer",
            company="Tech Corporation",
            location="San Francisco, CA",
            start_date=date(2020, 1, 1),
            description=long_description,
            achievements=["Achievement 1"],
            technologies=["Python"]
        )

        assert len(experience.description) == 5000

        # Test serialization with long strings
        json_data = experience.model_dump(mode='json')
        assert len(json_data["description"]) == 5000

    def test_boundary_score_values(self):
        """Test models with boundary score values (0.0 and 1.0)."""
        # Test minimum scores (0.0)
        skill_match = SkillMatch(
            skill_name="Unknown Skill",
            job_importance=1,
            user_proficiency=0,
            match_score=0.0,
            evidence=[]
        )
        assert skill_match.match_score == 0.0

        # Test maximum scores (1.0)
        validation_result = ValidationResult(
            is_valid=True,
            accuracy_score=1.0,
            readability_score=1.0,
            keyword_optimization_score=1.0,
            issues=[],
            strengths=["Perfect"],
            overall_quality_score=1.0,
            validation_timestamp="2024-01-15T12:00:00Z",
            confidence=1.0,
            errors=[],
            warnings=[]
        )
        assert validation_result.accuracy_score == 1.0
        assert validation_result.confidence == 1.0

    def test_empty_lists_and_collections(self):
        """Test models with empty lists and collections."""
        # Job analysis with empty lists
        analysis = JobAnalysis(
            company_name="Company",
            job_title="Role",
            location="Location",
            requirements=[],  # Empty requirements
            key_responsibilities=[],  # Empty responsibilities
            company_culture="Culture",
            role_level=ResponsibilityLevel.JUNIOR,
            industry="Industry",
            benefits=[],  # Empty benefits
            preferred_qualifications=[],  # Empty qualifications
            analysis_timestamp="2024-01-15T12:00:00Z"
        )

        assert len(analysis.requirements) == 0
        assert len(analysis.key_responsibilities) == 0
        assert len(analysis.benefits) == 0

        # Matching result with empty matches
        matching_result = MatchingResult(
            overall_match_score=0.0,
            skill_matches=[],  # No skill matches
            experience_matches=[],  # No experience matches
            missing_requirements=[],
            strength_areas=[],
            transferable_skills=[],
            recommendations=[],
            confidence_score=0.5
        )

        assert len(matching_result.skill_matches) == 0
        assert len(matching_result.experience_matches) == 0

    def test_date_edge_cases(self):
        """Test models with edge case dates."""
        # Very old date
        old_education = Education(
            degree="Bachelor's",
            institution="University",
            location="City",
            graduation_date=date(1970, 1, 1)
        )
        assert old_education.graduation_date.year == 1970

        # Future date
        future_project = Project(
            name="Future Project",
            description="Planned project",
            technologies=["TBD"],
            start_date=date(2030, 1, 1),
            achievements=[]
        )
        assert future_project.start_date.year == 2030

        # Same start and end date
        one_day_experience = WorkExperience(
            position="Contractor",
            company="Client",
            location="Remote",
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 1),
            description="One-day contract",
            achievements=[]
        )
        assert one_day_experience.start_date == one_day_experience.end_date

    def test_unicode_and_special_characters(self):
        """Test models with unicode and special characters."""
        # Unicode in names and descriptions
        contact = ContactInfo(
            name="José María Ñoño",
            email="jose@example.com",
            location="São Paulo, Brasil"
        )
        assert "José" in contact.name
        assert "São Paulo" in contact.location

        # Special characters in content
        project = Project(
            name="AI/ML Pipeline",
            description="End-to-end ML pipeline with 99.9% uptime & <100ms latency",
            technologies=["Python 3.11+", "TensorFlow 2.x"],
            start_date=date(2024, 1, 1),
            achievements=["Reduced costs by $50,000+"]
        )
        assert "/" in project.name
        assert "&" in project.description
        assert "+" in project.technologies[0]

    def test_realistic_data_scenarios(self):
        """Test with realistic, complex data scenarios."""
        # Career change scenario - different industries
        experience_1 = WorkExperience(
            position="Marketing Manager",
            company="Retail Corp",
            location="New York, NY",
            start_date=date(2015, 1, 1),
            end_date=date(2020, 12, 31),
            description="Managed marketing campaigns for retail products",
            achievements=["Increased sales by 25%", "Led team of 8"],
            technologies=["Google Analytics", "Salesforce"]
        )

        experience_2 = WorkExperience(
            position="Junior Software Developer",
            company="Tech Startup",
            location="San Francisco, CA",
            start_date=date(2021, 1, 1),
            description="Transitioned to software development",
            achievements=["Completed coding bootcamp", "Built 3 web applications"],
            technologies=["JavaScript", "React", "Node.js"]
        )

        # Career change profile
        profile_data = {
            "version": "1.0",
            "metadata": {"career_change": "true"},
            "contact": {
                "name": "Career Changer",
                "email": "changer@example.com",
                "location": "San Francisco, CA"
            },
            "professional_summary": "Marketing professional transitioning to software development",
            "experience": [experience_1.model_dump(), experience_2.model_dump()],
            "education": [],
            "skills": [
                {
                    "name": "JavaScript",
                    "category": SkillCategory.TECHNICAL,
                    "proficiency": 3,
                    "years_experience": 2
                },
                {
                    "name": "Project Management",
                    "category": SkillCategory.SOFT,
                    "proficiency": 5,
                    "years_experience": 8
                }
            ]
        }

        profile = UserProfile(**profile_data)
        assert len(profile.experience) == 2
        assert len(profile.skills) == 2
        assert profile.experience[0].company != profile.experience[1].company  # Different companies

        # JSON serialization should work
        json_data = profile.model_dump(mode='json')
        profile_restored = UserProfile.model_validate(json_data)
        assert len(profile_restored.experience) == 2


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])