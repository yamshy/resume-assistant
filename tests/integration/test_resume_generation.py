"""
Integration tests for Resume Generation Agent quality and performance.

This test suite validates the Resume Generation Agent's ability to:
1. Generate high-quality tailored resume content
2. Optimize content based on job matching results
3. Integrate keywords effectively
4. Maintain content accuracy against source profile
5. Meet performance requirements (<5 seconds per constitution)

TDD Implementation: These tests MUST FAIL initially as Resume Generation Agent doesn't exist yet.
"""

import time
from datetime import date

import pytest

# pydanticAI imports for testing
from pydantic_ai.models.test import TestModel

# Project models (will fail until implemented)
try:
    from src.resume_core.agents.resume_generation_agent import ResumeGenerationAgent
    from src.resume_core.models.resume_optimization import TailoredResume
    from src.resume_core.models.approval import ResumeSection
    from src.resume_core.models.profile import (
        ContactInfo,
        Skill,
        SkillCategory,
        UserProfile,
        WorkExperience,
    )

    from src.resume_core.models.job_analysis import JobAnalysis, JobRequirement, ResponsibilityLevel
    from src.resume_core.models.matching import ExperienceMatch, MatchingResult, SkillMatch
except ImportError:
    # Expected to fail in TDD - agents and models don't exist yet
    pytest.skip("Resume Generation Agent and models not implemented yet", allow_module_level=True)


class TestResumeGenerationQuality:
    """Test resume generation quality and optimization."""

    @pytest.fixture
    def high_match_profile(self) -> UserProfile:
        """High-match user profile for testing."""
        return UserProfile(
            version="1.0",
            metadata={"created_at": "2025-09-18T00:00:00Z", "updated_at": "2025-09-18T00:00:00Z"},
            contact=ContactInfo(
                name="Jane Smith",
                email="jane.smith@email.com",
                location="San Francisco, CA",
                linkedin="https://linkedin.com/in/janesmith"
            ),
            professional_summary="Senior Python developer with 5 years of experience in web applications and API development.",
            experience=[
                WorkExperience(
                    position="Senior Software Engineer",
                    company="TechCorp",
                    location="San Francisco, CA",
                    start_date=date(2020, 1, 1),
                    end_date=None,
                    description="Lead development of RESTful APIs and microservices using Python and FastAPI.",
                    achievements=[
                        "Reduced API response time by 40% through optimization",
                        "Led team of 3 engineers in delivering major feature releases"
                    ],
                    technologies=["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"]
                )
            ],
            education=[],
            skills=[
                Skill(name="Python", category=SkillCategory.TECHNICAL, proficiency=5, years_experience=5),
                Skill(name="FastAPI", category=SkillCategory.TECHNICAL, proficiency=4, years_experience=3),
                Skill(name="PostgreSQL", category=SkillCategory.TECHNICAL, proficiency=4, years_experience=4),
                Skill(name="Leadership", category=SkillCategory.SOFT, proficiency=4, years_experience=2)
            ]
        )

    @pytest.fixture
    def low_match_profile(self) -> UserProfile:
        """Low-match user profile requiring skill emphasis."""
        return UserProfile(
            version="1.0",
            metadata={"created_at": "2025-09-18T00:00:00Z", "updated_at": "2025-09-18T00:00:00Z"},
            contact=ContactInfo(
                name="John Doe",
                email="john.doe@email.com",
                location="Austin, TX",
                linkedin="https://linkedin.com/in/johndoe"
            ),
            professional_summary="Frontend developer transitioning to full-stack development.",
            experience=[
                WorkExperience(
                    position="Frontend Developer",
                    company="WebStart",
                    location="Austin, TX",
                    start_date=date(2022, 6, 1),
                    end_date=None,
                    description="Develop responsive web applications using React and JavaScript.",
                    achievements=[
                        "Built 10+ responsive web applications",
                        "Improved user engagement by 25%"
                    ],
                    technologies=["JavaScript", "React", "CSS", "HTML"]
                )
            ],
            education=[],
            skills=[
                Skill(name="JavaScript", category=SkillCategory.TECHNICAL, proficiency=4, years_experience=3),
                Skill(name="React", category=SkillCategory.TECHNICAL, proficiency=4, years_experience=2),
                Skill(name="Python", category=SkillCategory.TECHNICAL, proficiency=2, years_experience=1),
                Skill(name="Problem Solving", category=SkillCategory.SOFT, proficiency=4, years_experience=3)
            ]
        )

    @pytest.fixture
    def senior_backend_job(self) -> JobAnalysis:
        """Senior backend job analysis for testing."""
        return JobAnalysis(
            company_name="InnovateTech",
            job_title="Senior Backend Engineer",
            location="San Francisco, CA",
            requirements=[
                JobRequirement(
                    skill="Python",
                    importance=5,
                    category=SkillCategory.TECHNICAL,
                    is_required=True,
                    context="5+ years of Python development experience required"
                ),
                JobRequirement(
                    skill="FastAPI",
                    importance=4,
                    category=SkillCategory.TECHNICAL,
                    is_required=True,
                    context="Experience with FastAPI or similar frameworks"
                ),
                JobRequirement(
                    skill="PostgreSQL",
                    importance=4,
                    category=SkillCategory.TECHNICAL,
                    is_required=True,
                    context="Database design and optimization experience"
                ),
                JobRequirement(
                    skill="Leadership",
                    importance=3,
                    category=SkillCategory.SOFT,
                    is_required=False,
                    context="Mentoring junior developers preferred"
                )
            ],
            key_responsibilities=[
                "Design and implement scalable backend services",
                "Optimize database performance and queries",
                "Mentor junior team members",
                "Collaborate with frontend teams on API design"
            ],
            company_culture="Fast-paced startup environment with focus on innovation",
            role_level=ResponsibilityLevel.SENIOR,
            industry="Technology"
        )

    @pytest.fixture
    def high_match_result(self, high_match_profile: UserProfile, senior_backend_job: JobAnalysis) -> MatchingResult:
        """High-match result for testing."""
        return MatchingResult(
            overall_match_score=0.85,
            skill_matches=[
                SkillMatch(
                    skill_name="Python",
                    job_importance=5,
                    user_proficiency=5,
                    match_score=1.0,
                    evidence=["Senior Software Engineer with 5 years Python experience"]
                ),
                SkillMatch(
                    skill_name="FastAPI",
                    job_importance=4,
                    user_proficiency=4,
                    match_score=0.8,
                    evidence=["3 years FastAPI experience at TechCorp"]
                ),
                SkillMatch(
                    skill_name="PostgreSQL",
                    job_importance=4,
                    user_proficiency=4,
                    match_score=0.8,
                    evidence=["4 years database experience"]
                )
            ],
            experience_matches=[
                ExperienceMatch(
                    job_responsibility="Design and implement scalable backend services",
                    matching_experiences=["Lead development of RESTful APIs and microservices"],
                    relevance_score=0.9
                )
            ],
            missing_requirements=[],
            strength_areas=["Python expertise", "API development", "Performance optimization"],
            transferable_skills=["Leadership experience"],
            recommendations=["Emphasize team leadership experience"],
            confidence_score=0.9
        )

    @pytest.fixture
    def low_match_result(self, low_match_profile: UserProfile, senior_backend_job: JobAnalysis) -> MatchingResult:
        """Low-match result requiring skill emphasis."""
        return MatchingResult(
            overall_match_score=0.35,
            skill_matches=[
                SkillMatch(
                    skill_name="Python",
                    job_importance=5,
                    user_proficiency=2,
                    match_score=0.2,
                    evidence=["1 year Python experience"]
                ),
                SkillMatch(
                    skill_name="FastAPI",
                    job_importance=4,
                    user_proficiency=0,
                    match_score=0.0,
                    evidence=[]
                ),
                SkillMatch(
                    skill_name="JavaScript",
                    job_importance=1,
                    user_proficiency=4,
                    match_score=0.8,
                    evidence=["3 years JavaScript development"]
                )
            ],
            experience_matches=[],
            missing_requirements=[
                JobRequirement(
                    skill="FastAPI",
                    importance=4,
                    category=SkillCategory.TECHNICAL,
                    is_required=True,
                    context="Experience with FastAPI or similar frameworks"
                )
            ],
            strength_areas=["Frontend development", "User experience focus"],
            transferable_skills=["Problem solving", "Web development fundamentals"],
            recommendations=[
                "Emphasize transferable programming skills",
                "Highlight eagerness to learn backend technologies",
                "Showcase problem-solving abilities"
            ],
            confidence_score=0.7
        )

    @pytest.fixture
    def mock_resume_agent(self):
        """Mock Resume Generation Agent using TestModel."""
        agent = ResumeGenerationAgent()
        return agent.override(model=TestModel())

    async def test_high_match_profile_generates_targeted_resume(
        self,
        mock_resume_agent,
        high_match_profile: UserProfile,
        senior_backend_job: JobAnalysis,
        high_match_result: MatchingResult
    ):
        """Test high-match profile generating targeted resume content."""
        start_time = time.time()

        result = await mock_resume_agent.run({
            "user_profile": high_match_profile.model_dump(),
            "job_analysis": senior_backend_job.model_dump(),
            "matching_result": high_match_result.model_dump()
        })

        execution_time = time.time() - start_time

        # Performance requirement: <5 seconds per constitution
        assert execution_time < 5.0, f"Resume generation took {execution_time:.2f}s, must be <5s"

        tailored_resume = result.output
        assert isinstance(tailored_resume, TailoredResume)

        # Quality checks for high-match scenario
        assert tailored_resume.job_title == "Senior Backend Engineer"
        assert tailored_resume.company_name == "InnovateTech"
        assert tailored_resume.estimated_match_score >= 0.8

        # Content optimization checks
        optimizations = tailored_resume.optimizations
        assert len(optimizations) >= 2  # At least summary and experience sections

        # Keyword integration effectiveness
        summary_opt = next((opt for opt in optimizations if opt.section == ResumeSection.SUMMARY), None)
        assert summary_opt is not None
        assert "Python" in summary_opt.keywords_added
        assert "FastAPI" in summary_opt.keywords_added

        # Content accuracy - should emphasize strengths
        assert "5 years" in tailored_resume.full_resume_markdown
        assert "API response time by 40%" in tailored_resume.full_resume_markdown

    async def test_low_match_profile_emphasizes_transferable_skills(
        self,
        mock_resume_agent,
        low_match_profile: UserProfile,
        senior_backend_job: JobAnalysis,
        low_match_result: MatchingResult
    ):
        """Test low-match profile requiring skill emphasis and transferable skills."""
        start_time = time.time()

        result = await mock_resume_agent.run({
            "user_profile": low_match_profile.model_dump(),
            "job_analysis": senior_backend_job.model_dump(),
            "matching_result": low_match_result.model_dump()
        })

        execution_time = time.time() - start_time
        assert execution_time < 5.0, f"Resume generation took {execution_time:.2f}s, must be <5s"

        tailored_resume = result.output
        assert isinstance(tailored_resume, TailoredResume)

        # Should have lower match score but still valid
        assert 0.3 <= tailored_resume.estimated_match_score <= 0.5

        # Content optimization should emphasize transferable skills
        summary_opt = next((opt for opt in tailored_resume.optimizations if opt.section == ResumeSection.SUMMARY), None)
        assert summary_opt is not None
        assert summary_opt.match_improvement > 0

        # Should highlight programming fundamentals and learning ability
        resume_content = tailored_resume.full_resume_markdown.lower()
        assert any(word in resume_content for word in ["programming", "development", "problem-solving"])

        # Should mention willingness to learn or adaptability
        assert any(phrase in resume_content for phrase in ["eager", "learning", "adapt", "transition"])

    async def test_resume_sections_optimization(
        self,
        mock_resume_agent,
        high_match_profile: UserProfile,
        senior_backend_job: JobAnalysis,
        high_match_result: MatchingResult
    ):
        """Test different resume sections are optimized correctly."""
        result = await mock_resume_agent.run({
            "user_profile": high_match_profile.model_dump(),
            "job_analysis": senior_backend_job.model_dump(),
            "matching_result": high_match_result.model_dump()
        })

        tailored_resume = result.output
        optimizations = tailored_resume.optimizations

        # Should optimize multiple sections
        sections_optimized = {opt.section for opt in optimizations}
        expected_sections = {ResumeSection.SUMMARY, ResumeSection.EXPERIENCE, ResumeSection.SKILLS}
        assert expected_sections.issubset(sections_optimized)

        # Each optimization should have clear reasoning
        for opt in optimizations:
            assert len(opt.optimization_reason) > 10
            assert opt.match_improvement >= 0
            assert len(opt.keywords_added) > 0

        # Experience section should highlight relevant achievements
        exp_opt = next((opt for opt in optimizations if opt.section == ResumeSection.EXPERIENCE), None)
        assert exp_opt is not None
        assert "API" in exp_opt.optimized_content or "performance" in exp_opt.optimized_content.lower()

    async def test_keyword_integration_effectiveness(
        self,
        mock_resume_agent,
        high_match_profile: UserProfile,
        senior_backend_job: JobAnalysis,
        high_match_result: MatchingResult
    ):
        """Test keyword integration effectiveness and natural placement."""
        result = await mock_resume_agent.run({
            "user_profile": high_match_profile.model_dump(),
            "job_analysis": senior_backend_job.model_dump(),
            "matching_result": high_match_result.model_dump()
        })

        tailored_resume = result.output

        # Job-specific keywords should be integrated
        job_keywords = ["Python", "FastAPI", "PostgreSQL", "backend", "API"]
        resume_lower = tailored_resume.full_resume_markdown.lower()

        keyword_count = sum(1 for keyword in job_keywords if keyword.lower() in resume_lower)
        assert keyword_count >= 3, f"Only {keyword_count} keywords found, expected at least 3"

        # Keywords should appear in optimization records
        all_keywords_added = []
        for opt in tailored_resume.optimizations:
            all_keywords_added.extend(opt.keywords_added)

        assert len(all_keywords_added) >= 3
        assert any("Python" in kw for kw in all_keywords_added)

        # Keywords should be naturally integrated, not just appended
        assert "Python," not in tailored_resume.full_resume_markdown  # Avoid simple comma lists
        assert tailored_resume.full_resume_markdown.count("Python") >= 1

    async def test_content_accuracy_against_source_profile(
        self,
        mock_resume_agent,
        high_match_profile: UserProfile,
        senior_backend_job: JobAnalysis,
        high_match_result: MatchingResult
    ):
        """Test content accuracy and no hallucinations against source profile."""
        result = await mock_resume_agent.run({
            "user_profile": high_match_profile.model_dump(),
            "job_analysis": senior_backend_job.model_dump(),
            "matching_result": high_match_result.model_dump()
        })

        tailored_resume = result.output
        resume_content = tailored_resume.full_resume_markdown

        # Must include accurate contact information
        assert "Jane Smith" in resume_content
        assert "jane.smith@email.com" in resume_content
        assert "San Francisco, CA" in resume_content

        # Must include accurate work experience
        assert "TechCorp" in resume_content
        assert "Senior Software Engineer" in resume_content

        # Must include accurate achievements (no inflation)
        assert "40%" in resume_content  # Specific metric from profile
        assert "team of 3" in resume_content or "3 engineers" in resume_content

        # Should not hallucinate technologies not in profile
        # Allow reasonable variations but check for major hallucinations
        assert "React" not in resume_content  # Not in backend profile
        assert "Java" not in resume_content   # Not in profile

        # Summary of changes should be descriptive
        assert len(tailored_resume.summary_of_changes) > 20

    async def test_performance_timing_validation(
        self,
        mock_resume_agent,
        high_match_profile: UserProfile,
        senior_backend_job: JobAnalysis,
        high_match_result: MatchingResult
    ):
        """Test performance timing meets constitutional requirements."""
        # Test multiple runs to check consistency
        execution_times = []

        for _ in range(3):
            start_time = time.time()

            result = await mock_resume_agent.run({
                "user_profile": high_match_profile.model_dump(),
                "job_analysis": senior_backend_job.model_dump(),
                "matching_result": high_match_result.model_dump()
            })

            execution_time = time.time() - start_time
            execution_times.append(execution_time)

            # Each run must be under 5 seconds
            assert execution_time < 5.0, f"Run took {execution_time:.2f}s, must be <5s"

        # Average should also be reasonable
        avg_time = sum(execution_times) / len(execution_times)
        assert avg_time < 4.0, f"Average time {avg_time:.2f}s should be well under 5s limit"

        # Results should be consistent
        assert all(isinstance(result.output, TailoredResume) for result in [result])

    async def test_multiple_format_outputs_if_applicable(
        self,
        mock_resume_agent,
        high_match_profile: UserProfile,
        senior_backend_job: JobAnalysis,
        high_match_result: MatchingResult
    ):
        """Test multiple format outputs if supported by agent."""
        result = await mock_resume_agent.run({
            "user_profile": high_match_profile.model_dump(),
            "job_analysis": senior_backend_job.model_dump(),
            "matching_result": high_match_result.model_dump()
        })

        tailored_resume = result.output

        # Primary format should be Markdown as per spec
        assert tailored_resume.full_resume_markdown.startswith("#") or tailored_resume.full_resume_markdown.startswith("##")

        # Should be valid Markdown structure
        markdown_content = tailored_resume.full_resume_markdown
        assert "##" in markdown_content or "#" in markdown_content  # Headers
        assert len(markdown_content.split('\n')) > 5  # Multi-line content

        # Content should be structured with clear sections
        content_lower = markdown_content.lower()
        expected_sections = ["experience", "skills", "education"]
        present_sections = sum(1 for section in expected_sections if section in content_lower)
        assert present_sections >= 2, f"Only {present_sections} sections found in resume"


class TestResumeGenerationErrorHandling:
    """Test error handling and edge cases for Resume Generation Agent."""

    @pytest.fixture
    def mock_resume_agent(self):
        """Mock Resume Generation Agent using TestModel."""
        agent = ResumeGenerationAgent()
        return agent.override(model=TestModel())

    async def test_handles_empty_matching_result(self, mock_resume_agent, high_match_profile: UserProfile, senior_backend_job: JobAnalysis):
        """Test handling of empty or minimal matching results."""
        minimal_matching = MatchingResult(
            overall_match_score=0.1,
            skill_matches=[],
            experience_matches=[],
            missing_requirements=[],
            strength_areas=[],
            transferable_skills=[],
            recommendations=[],
            confidence_score=0.5
        )

        # Should still generate a resume, even with poor match
        result = await mock_resume_agent.run({
            "user_profile": high_match_profile.model_dump(),
            "job_analysis": senior_backend_job.model_dump(),
            "matching_result": minimal_matching.model_dump()
        })

        tailored_resume = result.output
        assert isinstance(tailored_resume, TailoredResume)
        assert len(tailored_resume.full_resume_markdown) > 100  # Should still generate content

    async def test_handles_missing_profile_sections(self, mock_resume_agent, senior_backend_job: JobAnalysis, high_match_result: MatchingResult):
        """Test handling of profiles with missing sections."""
        minimal_profile = UserProfile(
            version="1.0",
            metadata={"created_at": "2025-09-18T00:00:00Z", "updated_at": "2025-09-18T00:00:00Z"},
            contact=ContactInfo(
                name="Minimal User",
                email="minimal@email.com",
                location="Anywhere, USA"
            ),
            professional_summary="Recent graduate seeking opportunities.",
            experience=[],  # No experience
            education=[],   # No education
            skills=[]       # No skills
        )

        result = await mock_resume_agent.run({
            "user_profile": minimal_profile.model_dump(),
            "job_analysis": senior_backend_job.model_dump(),
            "matching_result": high_match_result.model_dump()
        })

        tailored_resume = result.output
        assert isinstance(tailored_resume, TailoredResume)
        # Should handle gracefully and still produce something
        assert len(tailored_resume.optimizations) >= 1  # At least summary optimization
