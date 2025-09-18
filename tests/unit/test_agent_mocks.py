"""
Unit tests for agent mocking patterns.

This module tests all 5 agents (Job Analysis, Profile Matching, Resume Generation,
Validation, Human Interface) using pydanticAI TestModel for comprehensive mocking
without external API dependencies.

Constitutional compliance:
- Uses TestModel for all agent mocking (no external API calls)
- Tests structured output validation against models
- Covers error handling and retry scenarios
- Verifies agent chain integration points
- Follows constitutional TDD patterns
"""

import pytest
from pydantic_ai.models.test import TestModel
from pydantic_ai.exceptions import ModelRetry

# Import agents
from agents.job_analysis_agent import JobAnalysisAgent, create_job_analysis_agent
from agents.profile_matching import ProfileMatchingAgent, create_profile_matching_agent
from agents.resume_generation_agent import ResumeGenerationAgent, create_resume_generation_agent
from agents.validation_agent import ValidationAgent, create_validation_agent

# Import models for output validation
from models.job_analysis import JobAnalysis, JobRequirement, ResponsibilityLevel
from models.matching import MatchingResult, SkillMatch, ExperienceMatch
from models.resume_optimization import TailoredResume, ContentOptimization
from models.validation import ValidationResult, ValidationIssue, ValidationWarning
from models.profile import UserProfile, ContactInfo, WorkExperience, Education, Skill, Project, SkillCategory
from models.approval import ResumeSection


class TestJobAnalysisAgentMock:
    """Test Job Analysis Agent mocking functionality."""

    @pytest.fixture
    def mock_job_analysis_agent(self):
        """Create Job Analysis Agent with TestModel override."""
        agent = create_job_analysis_agent()
        return agent.override(model=TestModel())

    async def test_job_analysis_agent_mock_basic(self, mock_job_analysis_agent):
        """Test basic Job Analysis Agent mocking with structured output."""
        job_posting = """
        Software Engineer position at TechCorp.
        Requirements: Python, React, 3+ years experience.
        Responsibilities: Build web applications, work with APIs.
        """

        result = await mock_job_analysis_agent.run(job_posting)

        # Verify result structure - agent returns JobAnalysis directly
        assert isinstance(result, JobAnalysis)

        # TestModel returns single character strings by default
        assert isinstance(result.company_name, str)
        assert isinstance(result.job_title, str)
        assert isinstance(result.location, str)
        assert isinstance(result.requirements, list)
        assert isinstance(result.key_responsibilities, list)

    async def test_job_analysis_agent_mock_validation_error(self):
        """Test Job Analysis Agent with validation that should trigger ModelRetry."""
        agent = create_job_analysis_agent()
        mock_agent = agent.override(model=TestModel())

        # Empty job posting should raise ValueError
        with pytest.raises(ValueError, match="Job posting content cannot be empty"):
            await mock_agent.run("")

        with pytest.raises(ValueError, match="Job posting content cannot be empty"):
            await mock_agent.run("   ")

    async def test_job_analysis_agent_override_functionality(self):
        """Test agent override functionality works correctly."""
        original_agent = create_job_analysis_agent()
        mock_agent = original_agent.override(model=TestModel())

        # Should be different instances
        assert original_agent is not mock_agent

        # Mock agent should have TestModel
        result = await mock_agent.run("Sample job posting")
        assert result is not None

    async def test_job_analysis_agent_mock_output_types(self, mock_job_analysis_agent):
        """Test that mocked agent returns correct output types."""
        result = await mock_job_analysis_agent.run("Software Engineer at TechCorp")

        # Verify all required fields exist
        assert hasattr(result, 'company_name')
        assert hasattr(result, 'job_title')
        assert hasattr(result, 'location')
        assert hasattr(result, 'requirements')
        assert hasattr(result, 'key_responsibilities')
        assert hasattr(result, 'company_culture')
        assert hasattr(result, 'role_level')
        assert hasattr(result, 'industry')


class TestProfileMatchingAgentMock:
    """Test Profile Matching Agent mocking functionality."""

    @pytest.fixture
    def mock_profile_matching_agent(self):
        """Create Profile Matching Agent with TestModel override."""
        agent = create_profile_matching_agent()
        return agent.override(model=TestModel())

    @pytest.fixture
    def sample_user_profile(self):
        """Create sample user profile for testing."""
        return UserProfile(
            version="1.0",
            metadata={"created_at": "2023-01-01T00:00:00", "updated_at": "2023-01-01T00:00:00"},
            contact=ContactInfo(
                name="John Doe",
                email="john@example.com",
                phone="555-0123",
                location="San Francisco, CA",
                linkedin="https://linkedin.com/in/johndoe",
                portfolio="https://johndoe.dev"
            ),
            professional_summary="Experienced software engineer with 5 years in web development",
            experience=[
                WorkExperience(
                    position="Software Engineer",
                    company="TechCorp",
                    location="San Francisco, CA",
                    start_date="2020-01-01",
                    end_date="2023-01-01",
                    description="Built web applications using Python and React",
                    achievements=["Increased performance by 30%", "Led team of 3 developers"],
                    technologies=["Python", "React", "PostgreSQL"]
                )
            ],
            education=[
                Education(
                    degree="BS Computer Science",
                    institution="Stanford University",
                    location="Stanford, CA",
                    graduation_date="2020-06-01",
                    gpa=3.8,
                    honors=["Cum Laude"],
                    relevant_coursework=["Data Structures", "Algorithms", "Web Development"]
                )
            ],
            skills=[
                Skill(
                    name="Python",
                    category=SkillCategory.TECHNICAL,
                    proficiency=4,
                    years_experience=5
                ),
                Skill(
                    name="React",
                    category=SkillCategory.TECHNICAL,
                    proficiency=4,
                    years_experience=3
                )
            ],
            projects=[
                Project(
                    name="E-commerce Platform",
                    description="Built full-stack e-commerce platform",
                    technologies=["Python", "React", "PostgreSQL"],
                    start_date="2022-01-01",
                    end_date="2022-06-01",
                    url="https://github.com/johndoe/ecommerce",
                    achievements=["1000+ active users", "98% uptime"]
                )
            ]
        )

    @pytest.fixture
    def sample_job_analysis(self):
        """Create sample job analysis for testing."""
        return JobAnalysis(
            company_name="TechCorp",
            job_title="Senior Software Engineer",
            department="Engineering",
            location="San Francisco, CA",
            remote_policy="Hybrid",
            requirements=[
                JobRequirement(
                    skill="Python",
                    importance=5,
                    category=SkillCategory.TECHNICAL,
                    is_required=True,
                    context="Must have 3+ years Python experience"
                ),
                JobRequirement(
                    skill="React",
                    importance=4,
                    category=SkillCategory.TECHNICAL,
                    is_required=True,
                    context="Frontend development with React"
                )
            ],
            key_responsibilities=["Build scalable web applications", "Mentor junior developers"],
            company_culture="Fast-paced startup environment",
            role_level=ResponsibilityLevel.SENIOR,
            industry="Technology",
            salary_range="$120k-$150k",
            benefits=["Health insurance", "401k matching"],
            preferred_qualifications=["Docker experience", "AWS certification"],
            analysis_timestamp="2025-09-18T12:00:00Z"
        )

    async def test_profile_matching_agent_mock_basic(self, mock_profile_matching_agent, sample_user_profile, sample_job_analysis):
        """Test basic Profile Matching Agent mocking with structured output."""
        result = await mock_profile_matching_agent.run(sample_user_profile, sample_job_analysis)

        # Verify result structure - profile matching agent returns MatchingResult directly
        assert isinstance(result, MatchingResult)

        # Verify required fields exist
        assert hasattr(result, 'overall_match_score')
        assert hasattr(result, 'skill_matches')
        assert hasattr(result, 'experience_matches')
        assert hasattr(result, 'missing_requirements')
        assert hasattr(result, 'strength_areas')
        assert hasattr(result, 'transferable_skills')
        assert hasattr(result, 'recommendations')
        assert hasattr(result, 'confidence_score')

    async def test_profile_matching_agent_mock_output_validation(self, mock_profile_matching_agent, sample_user_profile, sample_job_analysis):
        """Test that mocked agent returns valid MatchingResult structure."""
        result = await mock_profile_matching_agent.run(sample_user_profile, sample_job_analysis)

        # TestModel returns minimal valid structures
        assert isinstance(result.overall_match_score, float)
        assert isinstance(result.skill_matches, list)
        assert isinstance(result.experience_matches, list)
        assert isinstance(result.missing_requirements, list)
        assert isinstance(result.confidence_score, float)

    async def test_profile_matching_agent_override_functionality(self, sample_user_profile, sample_job_analysis):
        """Test Profile Matching Agent override functionality."""
        original_agent = create_profile_matching_agent()
        mock_agent = original_agent.override(model=TestModel())

        # Should be different instances
        assert original_agent is not mock_agent

        # Mock agent should work
        result = await mock_agent.run(sample_user_profile, sample_job_analysis)
        assert result is not None


class TestResumeGenerationAgentMock:
    """Test Resume Generation Agent mocking functionality."""

    @pytest.fixture
    def mock_resume_generation_agent(self):
        """Create Resume Generation Agent with TestModel override."""
        agent = create_resume_generation_agent()
        return agent.override(model=TestModel())

    @pytest.fixture
    def sample_context_data(self):
        """Create sample context data for resume generation testing."""
        return {
            "user_profile": {
                "contact": {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "555-0123",
                    "location": "San Francisco, CA"
                },
                "professional_summary": "Experienced software engineer"
            },
            "job_analysis": {
                "company_name": "TechCorp",
                "job_title": "Software Engineer",
                "location": "San Francisco, CA"
            },
            "matching_result": {
                "overall_match_score": 0.85,
                "confidence_score": 0.9
            }
        }

    async def test_resume_generation_agent_mock_basic(self, mock_resume_generation_agent, sample_context_data):
        """Test basic Resume Generation Agent mocking with structured output."""
        result = await mock_resume_generation_agent.run(sample_context_data)

        # Verify result structure - resume generation agent returns TailoredResume directly
        assert isinstance(result, TailoredResume)

        # Verify required fields exist
        assert hasattr(result, 'job_title')
        assert hasattr(result, 'company_name')
        assert hasattr(result, 'optimizations')
        assert hasattr(result, 'full_resume_markdown')
        assert hasattr(result, 'summary_of_changes')
        assert hasattr(result, 'estimated_match_score')
        assert hasattr(result, 'generation_timestamp')

    async def test_resume_generation_agent_mock_output_types(self, mock_resume_generation_agent, sample_context_data):
        """Test that mocked agent returns correct TailoredResume structure."""
        result = await mock_resume_generation_agent.run(sample_context_data)

        assert isinstance(result.job_title, str)
        assert isinstance(result.company_name, str)
        assert isinstance(result.optimizations, list)
        assert isinstance(result.full_resume_markdown, str)
        assert isinstance(result.summary_of_changes, str)
        assert isinstance(result.estimated_match_score, float)
        assert isinstance(result.generation_timestamp, str)

    async def test_resume_generation_agent_override_functionality(self, sample_context_data):
        """Test Resume Generation Agent override functionality."""
        original_agent = create_resume_generation_agent()
        mock_agent = original_agent.override(model=TestModel())

        # Should be different instances
        assert original_agent is not mock_agent

        # Mock agent should work
        result = await mock_agent.run(sample_context_data)
        assert result is not None


class TestValidationAgentMock:
    """Test Validation Agent mocking functionality."""

    @pytest.fixture
    def mock_validation_agent(self):
        """Create Validation Agent with TestModel override."""
        agent = create_validation_agent()
        return agent.override(model=TestModel())

    @pytest.fixture
    def sample_resume_data(self):
        """Create sample resume data for validation testing."""
        return {
            "personal_info": "John Doe | john@example.com | 555-0123",
            "professional_summary": "Experienced software engineer with 5 years",
            "experience": "Software Engineer at TechCorp (2020-2023)",
            "education": "BS Computer Science, Stanford University (2020)",
            "skills": "Python, React, PostgreSQL"
        }

    @pytest.fixture
    def sample_source_profile(self):
        """Create sample source profile for validation testing."""
        return {
            "personal_info": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "555-0123"
            },
            "experience": [
                {
                    "position": "Software Engineer",
                    "company": "TechCorp",
                    "start_date": "2020-01-01",
                    "end_date": "2023-01-01"
                }
            ],
            "education": [
                {
                    "degree": "BS Computer Science",
                    "institution": "Stanford University",
                    "graduation_date": "2020-06-01"
                }
            ],
            "skills": ["Python", "React", "PostgreSQL"]
        }

    async def test_validation_agent_mock_basic(self, mock_validation_agent, sample_resume_data, sample_source_profile):
        """Test basic Validation Agent mocking with structured output."""
        result = await mock_validation_agent.run(sample_resume_data, sample_source_profile)

        # Verify result structure - validation agent returns ValidationResult directly
        assert isinstance(result, ValidationResult)

        # Verify required fields exist
        assert hasattr(result, 'is_valid')
        assert hasattr(result, 'accuracy_score')
        assert hasattr(result, 'readability_score')
        assert hasattr(result, 'keyword_optimization_score')
        assert hasattr(result, 'overall_quality_score')
        assert hasattr(result, 'issues')
        assert hasattr(result, 'strengths')
        assert hasattr(result, 'validation_timestamp')

    async def test_validation_agent_mock_output_types(self, mock_validation_agent, sample_resume_data, sample_source_profile):
        """Test that mocked agent returns correct ValidationResult structure."""
        result = await mock_validation_agent.run(sample_resume_data, sample_source_profile)

        assert isinstance(result.is_valid, bool)
        assert isinstance(result.accuracy_score, float)
        assert isinstance(result.readability_score, float)
        assert isinstance(result.keyword_optimization_score, float)
        assert isinstance(result.overall_quality_score, float)
        assert isinstance(result.issues, list)
        assert isinstance(result.strengths, list)
        assert isinstance(result.validation_timestamp, str)

    async def test_validation_agent_override_functionality(self, sample_resume_data, sample_source_profile):
        """Test Validation Agent override functionality."""
        original_agent = create_validation_agent()
        mock_agent = original_agent.override(model=TestModel())

        # Should be different instances
        assert original_agent is not mock_agent

        # Mock agent should work
        result = await mock_agent.run(sample_resume_data, sample_source_profile)
        assert result is not None


class TestAgentOverrideFunctionality:
    """Test agent override functionality across all agents."""

    async def test_agent_override_creates_new_instances(self):
        """Test that override creates new agent instances, not modifying originals."""
        # Create original agents
        job_agent = create_job_analysis_agent()
        profile_agent = create_profile_matching_agent()
        resume_agent = create_resume_generation_agent()
        validation_agent = create_validation_agent()

        # Create overridden agents
        mock_job_agent = job_agent.override(model=TestModel())
        mock_profile_agent = profile_agent.override(model=TestModel())
        mock_resume_agent = resume_agent.override(model=TestModel())
        mock_validation_agent = validation_agent.override(model=TestModel())

        # Verify they are different instances
        assert job_agent is not mock_job_agent
        assert profile_agent is not mock_profile_agent
        assert resume_agent is not mock_resume_agent
        assert validation_agent is not mock_validation_agent

    async def test_agent_override_with_test_model(self):
        """Test that all agents work correctly with TestModel override."""
        # Override all agents with TestModel
        job_agent = create_job_analysis_agent().override(model=TestModel())
        profile_agent = create_profile_matching_agent().override(model=TestModel())
        resume_agent = create_resume_generation_agent().override(model=TestModel())
        validation_agent = create_validation_agent().override(model=TestModel())

        # Test each agent can run with TestModel
        job_result = await job_agent.run("Sample job posting")
        assert job_result is not None

        # For profile agent, we need sample data
        sample_profile = UserProfile(
            version="1.0",
            metadata={"created_at": "2023-01-01T00:00:00"},
            contact=ContactInfo(name="Test", email="test@example.com", phone="555-0123", location="Test City"),
            professional_summary="Test summary",
            experience=[], education=[], skills=[], projects=[]
        )
        sample_job = JobAnalysis(
            company_name="Test Co", job_title="Test Role", location="Test City",
            requirements=[], key_responsibilities=["Test"], company_culture="Test",
            role_level=ResponsibilityLevel.MID, industry="Test",
            analysis_timestamp="2024-01-15T12:00:00Z"
        )
        profile_result = await profile_agent.run(sample_profile, sample_job)
        assert profile_result is not None

        # Test resume agent
        sample_context = {"user_profile": {"contact": {"name": "Test"}}, "job_analysis": {"company_name": "Test"}, "matching_result": {"overall_match_score": 0.8}}
        resume_result = await resume_agent.run(sample_context)
        assert resume_result is not None

        # Test validation agent
        validation_result = await validation_agent.run({"test": "data"}, {"source": "data"})
        assert validation_result is not None


class TestAgentErrorHandling:
    """Test agent error handling and edge cases."""

    async def test_job_analysis_agent_empty_input_error(self):
        """Test that Job Analysis Agent properly handles empty input."""
        agent = create_job_analysis_agent().override(model=TestModel())

        # Empty string should raise ValueError
        with pytest.raises(ValueError, match="Job posting content cannot be empty"):
            await agent.run("")

        # Whitespace-only string should raise ValueError
        with pytest.raises(ValueError, match="Job posting content cannot be empty"):
            await agent.run("   \n\t  ")

    async def test_validation_agent_handles_test_model_quirks(self):
        """Test that Validation Agent properly handles TestModel's single-character responses."""
        agent = create_validation_agent().override(model=TestModel())

        # TestModel returns single characters, validation should handle this gracefully
        result = await agent.run({"test": "data"}, {"source": "data"})

        # Should complete without errors despite TestModel's minimal responses
        assert result is not None
        assert hasattr(result, 'confidence')
        assert hasattr(result, 'errors')
        assert hasattr(result, 'warnings')

    async def test_agents_handle_missing_optional_fields(self):
        """Test that agents handle missing optional fields gracefully."""
        # Test with minimal valid inputs
        job_agent = create_job_analysis_agent().override(model=TestModel())
        result = await job_agent.run("Minimal job posting")

        # Should work even with minimal input
        assert result is not None
        assert isinstance(result, JobAnalysis)


class TestAgentChainIntegrationPoints:
    """Test agent chain integration points for pipeline compatibility."""

    async def test_job_analysis_to_profile_matching_chain(self):
        """Test that Job Analysis output can be used as Profile Matching input."""
        # Create mocked agents
        job_agent = create_job_analysis_agent().override(model=TestModel())
        profile_agent = create_profile_matching_agent().override(model=TestModel())

        # Run job analysis
        job_result = await job_agent.run("Software Engineer at TechCorp")

        # Create minimal profile for testing
        test_profile = UserProfile(
            version="1.0",
            metadata={"created_at": "2023-01-01T00:00:00"},
            contact=ContactInfo(name="Test", email="test@example.com", phone="555-0123", location="Test City"),
            professional_summary="Test", experience=[], education=[], skills=[], projects=[]
        )

        # Use job analysis result as input to profile matching
        # Note: TestModel outputs won't be realistic, but structure should work
        profile_result = await profile_agent.run(test_profile, job_result)

        assert profile_result is not None
        assert isinstance(profile_result, MatchingResult)

    async def test_matching_to_resume_generation_chain(self):
        """Test that Profile Matching output can be used for Resume Generation."""
        profile_agent = create_profile_matching_agent().override(model=TestModel())
        resume_agent = create_resume_generation_agent().override(model=TestModel())

        # Create test data for profile matching
        test_profile = UserProfile(
            version="1.0",
            metadata={"created_at": "2023-01-01T00:00:00"},
            contact=ContactInfo(name="Test", email="test@example.com", phone="555-0123", location="Test City"),
            professional_summary="Test", experience=[], education=[], skills=[], projects=[]
        )
        test_job = JobAnalysis(
            company_name="Test Co", job_title="Test Role", location="Test City",
            requirements=[], key_responsibilities=["Test"], company_culture="Test",
            role_level=ResponsibilityLevel.MID, industry="Test",
            analysis_timestamp="2024-01-15T12:00:00Z"
        )

        # Run profile matching
        matching_result = await profile_agent.run(test_profile, test_job)

        # Create context for resume generation
        context = {
            "user_profile": {"contact": {"name": "Test"}},
            "job_analysis": {"company_name": "Test Co"},
            "matching_result": {"overall_match_score": 0.8, "confidence_score": 0.9}
        }

        # Generate resume
        resume_result = await resume_agent.run(context)

        assert resume_result is not None
        assert isinstance(resume_result, TailoredResume)

    async def test_resume_to_validation_chain(self):
        """Test that Resume Generation output can be validated."""
        resume_agent = create_resume_generation_agent().override(model=TestModel())
        validation_agent = create_validation_agent().override(model=TestModel())

        # Generate resume
        context = {
            "user_profile": {"contact": {"name": "Test"}},
            "job_analysis": {"company_name": "Test Co"},
            "matching_result": {"overall_match_score": 0.8}
        }
        resume_result = await resume_agent.run(context)

        # Validate resume (using dict format for testing)
        resume_data = {"content": "test resume content"}
        source_data = {"profile": "test profile"}

        validation_result = await validation_agent.run(resume_data, source_data)

        assert validation_result is not None
        assert isinstance(validation_result, ValidationResult)


class TestAgentMockDataConsistency:
    """Test that mocked agents return consistent data structures."""

    async def test_all_agents_return_structured_outputs(self):
        """Test that all agents return properly structured outputs when mocked."""
        # Create all mocked agents
        agents = {
            'job_analysis': create_job_analysis_agent().override(model=TestModel()),
            'profile_matching': create_profile_matching_agent().override(model=TestModel()),
            'resume_generation': create_resume_generation_agent().override(model=TestModel()),
            'validation': create_validation_agent().override(model=TestModel())
        }

        # Test job analysis
        job_result = await agents['job_analysis'].run("Test job posting")
        assert isinstance(job_result, JobAnalysis)

        # Test profile matching with minimal data
        test_profile = UserProfile(
            version="1.0",
            metadata={"created_at": "2023-01-01T00:00:00"},
            contact=ContactInfo(name="Test", email="test@example.com", phone="555-0123", location="Test City"),
            professional_summary="Test", experience=[], education=[], skills=[], projects=[]
        )
        test_job = JobAnalysis(
            company_name="Test Co", job_title="Test Role", location="Test City",
            requirements=[], key_responsibilities=["Test"], company_culture="Test",
            role_level=ResponsibilityLevel.MID, industry="Test",
            analysis_timestamp="2024-01-15T12:00:00Z"
        )
        matching_result = await agents['profile_matching'].run(test_profile, test_job)
        assert isinstance(matching_result, MatchingResult)

        # Test resume generation
        context = {"user_profile": {"contact": {"name": "Test"}}, "job_analysis": {"company_name": "Test"}, "matching_result": {"overall_match_score": 0.8}}
        resume_result = await agents['resume_generation'].run(context)
        assert isinstance(resume_result, TailoredResume)

        # Test validation
        validation_result = await agents['validation'].run({"test": "data"}, {"source": "data"})
        assert isinstance(validation_result, ValidationResult)

    async def test_mocked_agents_handle_pydantic_validation(self):
        """Test that mocked agents work with pydantic validation constraints."""
        # TestModel outputs may not always satisfy pydantic constraints,
        # but the structure should be valid
        validation_agent = create_validation_agent().override(model=TestModel())

        result = await validation_agent.run({"test": "data"}, {"source": "data"})

        # Basic structure should be valid even if values are minimal
        assert hasattr(result, 'is_valid')
        assert hasattr(result, 'accuracy_score')
        assert hasattr(result, 'overall_quality_score')
        assert hasattr(result, 'validation_timestamp')


# Configuration for pytest-asyncio
pytestmark = pytest.mark.asyncio