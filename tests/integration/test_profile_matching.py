"""
Integration tests for Profile Matching Agent accuracy and performance.

Tests the Profile Matching Agent's ability to accurately match user profiles
against job requirements with proper scoring and performance timing.

These tests are designed to FAIL initially (TDD) until the Profile Matching Agent is implemented.
"""
import time
from datetime import date
from typing import List

import pytest
from pydantic_ai.models.test import TestModel

from models.profile import (
    ContactInfo,
    UserProfile,
    WorkExperience,
    Education,
    Skill,
    SkillCategory,
    Project,
)
from models.job_analysis import (
    JobAnalysis,
    JobRequirement,
    ResponsibilityLevel,
)
from models.matching import (
    MatchingResult,
    SkillMatch,
    ExperienceMatch,
)


# Test fixtures for different profile scenarios
@pytest.fixture
def high_match_profile() -> UserProfile:
    """Profile with >80% skill overlap for high-match testing."""
    return UserProfile(
        version="1.0",
        metadata={"created_at": "2025-09-17T00:00:00Z", "updated_at": "2025-09-17T00:00:00Z"},
        contact=ContactInfo(
            name="John Doe",
            email="john@example.com",
            location="San Francisco, CA",
            linkedin="https://linkedin.com/in/johndoe",
        ),
        professional_summary="Senior Software Engineer with 8+ years in Python, React, and cloud architecture",
        experience=[
            WorkExperience(
                position="Senior Software Engineer",
                company="Tech Corp",
                location="San Francisco, CA",
                start_date=date(2020, 1, 1),
                end_date=None,
                description="Lead full-stack development using Python, React, and AWS",
                achievements=[
                    "Built scalable microservices handling 1M+ requests/day",
                    "Led team of 5 engineers in agile development",
                    "Reduced system latency by 40% through optimization",
                ],
                technologies=["Python", "React", "AWS", "Docker", "PostgreSQL", "Redis"],
            ),
            WorkExperience(
                position="Software Engineer",
                company="StartupCo",
                location="San Francisco, CA",
                start_date=date(2018, 6, 1),
                end_date=date(2019, 12, 31),
                description="Full-stack development with Python/Django and React",
                achievements=[
                    "Developed REST APIs serving 100K+ users",
                    "Implemented CI/CD pipeline reducing deployment time by 60%",
                ],
                technologies=["Python", "Django", "React", "PostgreSQL", "Jenkins"],
            ),
        ],
        education=[
            Education(
                degree="Bachelor of Science in Computer Science",
                institution="UC Berkeley",
                location="Berkeley, CA",
                graduation_date=date(2018, 5, 15),
                gpa=3.8,
            )
        ],
        skills=[
            Skill(name="Python", category=SkillCategory.TECHNICAL, proficiency=5, years_experience=8),
            Skill(name="React", category=SkillCategory.TECHNICAL, proficiency=4, years_experience=6),
            Skill(name="AWS", category=SkillCategory.TECHNICAL, proficiency=4, years_experience=5),
            Skill(name="Docker", category=SkillCategory.TECHNICAL, proficiency=4, years_experience=4),
            Skill(name="PostgreSQL", category=SkillCategory.TECHNICAL, proficiency=4, years_experience=6),
            Skill(name="Leadership", category=SkillCategory.SOFT, proficiency=4, years_experience=3),
        ],
        projects=[
            Project(
                name="Microservices Platform",
                description="Built scalable microservices platform using Python and AWS",
                technologies=["Python", "AWS", "Docker", "Kubernetes"],
                start_date=date(2023, 1, 1),
                end_date=date(2023, 6, 1),
                achievements=["Reduced deployment time by 50%", "Improved system reliability to 99.9%"],
            )
        ],
    )


@pytest.fixture
def medium_match_profile() -> UserProfile:
    """Profile with 50-80% skill overlap for medium-match testing."""
    return UserProfile(
        version="1.0",
        metadata={"created_at": "2025-09-17T00:00:00Z", "updated_at": "2025-09-17T00:00:00Z"},
        contact=ContactInfo(
            name="Jane Smith",
            email="jane@example.com",
            location="Austin, TX",
        ),
        professional_summary="Software Developer with 4 years experience in web development",
        experience=[
            WorkExperience(
                position="Software Developer",
                company="WebDev Inc",
                location="Austin, TX",
                start_date=date(2021, 3, 1),
                end_date=None,
                description="Frontend development with JavaScript and React",
                achievements=[
                    "Built responsive web applications for 50K+ users",
                    "Collaborated with design team on UI/UX improvements",
                ],
                technologies=["JavaScript", "React", "HTML", "CSS", "Node.js"],
            ),
            WorkExperience(
                position="Junior Developer",
                company="LocalTech",
                location="Austin, TX",
                start_date=date(2020, 1, 1),
                end_date=date(2021, 2, 28),
                description="Full-stack development with PHP and MySQL",
                achievements=["Maintained legacy PHP applications"],
                technologies=["PHP", "MySQL", "JavaScript", "HTML", "CSS"],
            ),
        ],
        education=[
            Education(
                degree="Bachelor of Arts in Computer Science",
                institution="UT Austin",
                location="Austin, TX",
                graduation_date=date(2019, 12, 15),
                gpa=3.5,
            )
        ],
        skills=[
            Skill(name="JavaScript", category=SkillCategory.TECHNICAL, proficiency=4, years_experience=4),
            Skill(name="React", category=SkillCategory.TECHNICAL, proficiency=4, years_experience=3),
            Skill(name="HTML", category=SkillCategory.TECHNICAL, proficiency=4, years_experience=4),
            Skill(name="CSS", category=SkillCategory.TECHNICAL, proficiency=4, years_experience=4),
            Skill(name="Node.js", category=SkillCategory.TECHNICAL, proficiency=3, years_experience=2),
            Skill(name="PHP", category=SkillCategory.TECHNICAL, proficiency=3, years_experience=1),
        ],
    )


@pytest.fixture
def low_match_profile() -> UserProfile:
    """Profile with <50% skill overlap for low-match testing."""
    return UserProfile(
        version="1.0",
        metadata={"created_at": "2025-09-17T00:00:00Z", "updated_at": "2025-09-17T00:00:00Z"},
        contact=ContactInfo(
            name="Bob Wilson",
            email="bob@example.com",
            location="Chicago, IL",
        ),
        professional_summary="Marketing professional transitioning to tech with basic programming knowledge",
        experience=[
            WorkExperience(
                position="Marketing Manager",
                company="MarketingCorp",
                location="Chicago, IL",
                start_date=date(2019, 1, 1),
                end_date=None,
                description="Digital marketing campaigns and analytics",
                achievements=[
                    "Increased conversion rates by 30%",
                    "Managed $500K annual marketing budget",
                ],
                technologies=["Google Analytics", "Salesforce", "Excel"],
            ),
        ],
        education=[
            Education(
                degree="Bachelor of Business Administration",
                institution="Northwestern University",
                location="Evanston, IL",
                graduation_date=date(2018, 6, 15),
                gpa=3.6,
            )
        ],
        skills=[
            Skill(name="Digital Marketing", category=SkillCategory.SOFT, proficiency=5, years_experience=6),
            Skill(name="Analytics", category=SkillCategory.SOFT, proficiency=4, years_experience=5),
            Skill(name="Project Management", category=SkillCategory.SOFT, proficiency=4, years_experience=4),
            Skill(name="Python", category=SkillCategory.TECHNICAL, proficiency=2, years_experience=0),
            Skill(name="SQL", category=SkillCategory.TECHNICAL, proficiency=2, years_experience=1),
        ],
        projects=[
            Project(
                name="Personal Website",
                description="Built personal website using HTML and CSS",
                technologies=["HTML", "CSS", "JavaScript"],
                start_date=date(2024, 1, 1),
                end_date=date(2024, 3, 1),
                achievements=["Learned basic web development"],
            )
        ],
    )


@pytest.fixture
def senior_python_job_analysis() -> JobAnalysis:
    """Job analysis for Senior Python Engineer position."""
    return JobAnalysis(
        company_name="TechCorp",
        job_title="Senior Python Engineer",
        department="Engineering",
        location="San Francisco, CA",
        remote_policy="Hybrid (3 days in office)",
        requirements=[
            JobRequirement(
                skill="Python",
                importance=5,
                category=SkillCategory.TECHNICAL,
                is_required=True,
                context="5+ years of Python development experience required",
            ),
            JobRequirement(
                skill="React",
                importance=4,
                category=SkillCategory.TECHNICAL,
                is_required=True,
                context="Frontend experience with React framework",
            ),
            JobRequirement(
                skill="AWS",
                importance=4,
                category=SkillCategory.TECHNICAL,
                is_required=True,
                context="Cloud architecture experience with AWS services",
            ),
            JobRequirement(
                skill="Docker",
                importance=3,
                category=SkillCategory.TECHNICAL,
                is_required=False,
                context="Containerization experience preferred",
            ),
            JobRequirement(
                skill="Leadership",
                importance=4,
                category=SkillCategory.SOFT,
                is_required=True,
                context="Team leadership and mentoring experience",
            ),
            JobRequirement(
                skill="PostgreSQL",
                importance=3,
                category=SkillCategory.TECHNICAL,
                is_required=False,
                context="Database management experience",
            ),
        ],
        key_responsibilities=[
            "Lead development of scalable web applications",
            "Mentor junior developers",
            "Design and implement cloud architecture",
            "Collaborate with product team on requirements",
        ],
        company_culture="Fast-paced startup environment with strong engineering culture",
        role_level=ResponsibilityLevel.SENIOR,
        industry="Technology",
        salary_range="$150,000 - $200,000",
        benefits=["Health insurance", "401k matching", "Equity", "Flexible PTO"],
        preferred_qualifications=["Computer Science degree", "Startup experience"],
        analysis_timestamp="2025-09-18T12:00:00Z",
    )


@pytest.fixture
def empty_profile() -> UserProfile:
    """Empty profile for edge case testing."""
    return UserProfile(
        version="1.0",
        metadata={"created_at": "2025-09-17T00:00:00Z", "updated_at": "2025-09-17T00:00:00Z"},
        contact=ContactInfo(
            name="Empty User",
            email="empty@example.com",
            location="Unknown",
        ),
        professional_summary="",
        experience=[],
        education=[],
        skills=[],
    )


class TestProfileMatchingAgentAccuracy:
    """Test Profile Matching Agent accuracy across different scenarios."""

    async def test_high_match_profile_accuracy(self, high_match_profile, senior_python_job_analysis):
        """Test high-match profile (>80% skill overlap) produces accurate matching results."""
        # This test will FAIL until Profile Matching Agent is implemented
        from src.agents.profile_matching import ProfileMatchingAgent

        agent = ProfileMatchingAgent()
        agent = agent.override(model=TestModel())

        start_time = time.time()
        result = await agent.run(
            user_profile=high_match_profile,
            job_analysis=senior_python_job_analysis,
        )
        end_time = time.time()

        # Performance requirement: <5 seconds per constitution
        assert (end_time - start_time) < 5.0, "Profile matching must complete in <5 seconds"

        # Verify return type
        assert isinstance(result.output, MatchingResult)

        # High match should score >0.8
        assert result.output.overall_match_score > 0.8, "High-match profile should score >0.8"

        # Should have high confidence
        assert result.output.confidence_score > 0.8, "High-match should have high confidence"

        # Should identify key skill matches
        skill_names = [sm.skill_name for sm in result.output.skill_matches]
        assert "Python" in skill_names, "Should identify Python skill match"
        assert "React" in skill_names, "Should identify React skill match"
        assert "AWS" in skill_names, "Should identify AWS skill match"

        # Python should be high match (user has proficiency 5, job importance 5)
        python_match = next(sm for sm in result.output.skill_matches if sm.skill_name == "Python")
        assert python_match.match_score > 0.9, "Python should be near-perfect match"
        assert python_match.user_proficiency == 5, "Should detect user's Python proficiency"

        # Should have minimal missing requirements
        assert len(result.output.missing_requirements) <= 2, "High-match should have few missing requirements"

        # Should identify strength areas
        assert len(result.output.strength_areas) > 0, "Should identify user strengths"

    async def test_medium_match_profile_accuracy(self, medium_match_profile, senior_python_job_analysis):
        """Test medium-match profile (50-80% skill overlap) produces moderate matching results."""
        # This test will FAIL until Profile Matching Agent is implemented
        from src.agents.profile_matching import ProfileMatchingAgent

        agent = ProfileMatchingAgent()
        agent = agent.override(model=TestModel())

        start_time = time.time()
        result = await agent.run(
            user_profile=medium_match_profile,
            job_analysis=senior_python_job_analysis,
        )
        end_time = time.time()

        # Performance requirement
        assert (end_time - start_time) < 5.0, "Profile matching must complete in <5 seconds"

        # Medium match should score 0.5-0.8
        assert 0.5 <= result.output.overall_match_score <= 0.8, "Medium-match should score 0.5-0.8"

        # Should have moderate confidence
        assert result.output.confidence_score > 0.6, "Medium-match should have moderate confidence"

        # Should identify React match but miss Python
        skill_names = [sm.skill_name for sm in result.output.skill_matches]
        assert "React" in skill_names, "Should identify React skill match"

        # Should identify missing critical requirements
        missing_skills = [req.skill for req in result.output.missing_requirements]
        assert "Python" in missing_skills, "Should identify missing Python requirement"
        assert "AWS" in missing_skills, "Should identify missing AWS requirement"

        # Should suggest transferable skills
        assert len(result.output.transferable_skills) > 0, "Should identify transferable skills"

    async def test_low_match_profile_accuracy(self, low_match_profile, senior_python_job_analysis):
        """Test low-match profile (<50% skill overlap) produces accurate low scores."""
        # This test will FAIL until Profile Matching Agent is implemented
        from src.agents.profile_matching import ProfileMatchingAgent

        agent = ProfileMatchingAgent()
        agent = agent.override(model=TestModel())

        start_time = time.time()
        result = await agent.run(
            user_profile=low_match_profile,
            job_analysis=senior_python_job_analysis,
        )
        end_time = time.time()

        # Performance requirement
        assert (end_time - start_time) < 5.0, "Profile matching must complete in <5 seconds"

        # Low match should score <0.5
        assert result.output.overall_match_score < 0.5, "Low-match profile should score <0.5"

        # Should have lower confidence for career change scenarios
        assert result.output.confidence_score > 0.5, "Should still have reasonable confidence in analysis"

        # Should identify most requirements as missing
        assert len(result.output.missing_requirements) >= 4, "Should identify most requirements as missing"

        # Should provide career transition recommendations
        assert len(result.output.recommendations) > 0, "Should provide improvement recommendations"

        # Should identify transferable soft skills
        transferable = result.output.transferable_skills
        assert any("project" in skill.lower() or "management" in skill.lower() for skill in transferable), \
            "Should identify transferable management skills"

    async def test_transferable_skills_identification(self, low_match_profile, senior_python_job_analysis):
        """Test accurate identification of transferable skills for career transitions."""
        # This test will FAIL until Profile Matching Agent is implemented
        from src.agents.profile_matching import ProfileMatchingAgent

        agent = ProfileMatchingAgent()
        agent = agent.override(model=TestModel())

        result = await agent.run(
            user_profile=low_match_profile,
            job_analysis=senior_python_job_analysis,
        )

        # Should identify transferable skills from marketing background
        transferable = result.output.transferable_skills
        assert len(transferable) > 0, "Should identify transferable skills"

        # Analytics experience should transfer to data analysis
        assert any("analytics" in skill.lower() for skill in transferable), \
            "Should identify analytics as transferable"

        # Project management should transfer to technical leadership
        assert any("project" in skill.lower() or "management" in skill.lower() for skill in transferable), \
            "Should identify project management as transferable"

    async def test_edge_case_empty_profile(self, empty_profile, senior_python_job_analysis):
        """Test handling of empty profile edge case."""
        # This test will FAIL until Profile Matching Agent is implemented
        from src.agents.profile_matching import ProfileMatchingAgent

        agent = ProfileMatchingAgent()
        agent = agent.override(model=TestModel())

        result = await agent.run(
            user_profile=empty_profile,
            job_analysis=senior_python_job_analysis,
        )

        # Empty profile should score very low
        assert result.output.overall_match_score < 0.1, "Empty profile should score very low"

        # Should have low confidence due to lack of data
        assert result.output.confidence_score < 0.7, "Empty profile should have lower confidence"

        # All requirements should be missing
        assert len(result.output.missing_requirements) == len(senior_python_job_analysis.requirements), \
            "All requirements should be missing for empty profile"

        # Should provide basic recommendations
        assert len(result.output.recommendations) > 0, "Should provide recommendations for skill development"

    async def test_experience_matching_accuracy(self, high_match_profile, senior_python_job_analysis):
        """Test accurate matching of work experience against job responsibilities."""
        # This test will FAIL until Profile Matching Agent is implemented
        from src.agents.profile_matching import ProfileMatchingAgent

        agent = ProfileMatchingAgent()
        agent = agent.override(model=TestModel())

        result = await agent.run(
            user_profile=high_match_profile,
            job_analysis=senior_python_job_analysis,
        )

        # Should match experience with job responsibilities
        exp_matches = result.output.experience_matches
        assert len(exp_matches) > 0, "Should identify experience matches"

        # Should match leadership experience
        leadership_match = any(
            "lead" in match.job_responsibility.lower() or "mentor" in match.job_responsibility.lower()
            for match in exp_matches
        )
        assert leadership_match, "Should match leadership experience"

        # Relevant experience should have high relevance scores
        high_relevance_matches = [match for match in exp_matches if match.relevance_score > 0.7]
        assert len(high_relevance_matches) > 0, "Should have high-relevance experience matches"


class TestProfileMatchingAgentPerformance:
    """Test Profile Matching Agent performance requirements."""

    async def test_performance_timing_requirement(self, high_match_profile, senior_python_job_analysis):
        """Test that profile matching completes within 5 second constitutional requirement."""
        # This test will FAIL until Profile Matching Agent is implemented
        from src.agents.profile_matching import ProfileMatchingAgent

        agent = ProfileMatchingAgent()
        agent = agent.override(model=TestModel())

        # Test multiple runs for consistency
        execution_times = []
        for _ in range(3):
            start_time = time.time()
            await agent.run(
                user_profile=high_match_profile,
                job_analysis=senior_python_job_analysis,
            )
            end_time = time.time()
            execution_times.append(end_time - start_time)

        # All runs must be under 5 seconds (constitutional requirement)
        for exec_time in execution_times:
            assert exec_time < 5.0, f"Execution time {exec_time:.2f}s exceeds 5 second requirement"

        # Average should be well under limit for good performance
        avg_time = sum(execution_times) / len(execution_times)
        assert avg_time < 3.0, f"Average execution time {avg_time:.2f}s should be under 3 seconds"

    async def test_performance_with_large_profile(self, senior_python_job_analysis):
        """Test performance with profile containing large amounts of data."""
        # This test will FAIL until Profile Matching Agent is implemented
        from src.agents.profile_matching import ProfileMatchingAgent

        # Create profile with extensive data
        large_profile = UserProfile(
            version="1.0",
            metadata={"created_at": "2025-09-17T00:00:00Z", "updated_at": "2025-09-17T00:00:00Z"},
            contact=ContactInfo(
                name="Experienced Developer",
                email="experienced@example.com",
                location="San Francisco, CA",
            ),
            professional_summary="Highly experienced software engineer with extensive background",
            experience=[
                WorkExperience(
                    position=f"Position {i}",
                    company=f"Company {i}",
                    location="San Francisco, CA",
                    start_date=date(2020 - i, 1, 1),
                    end_date=date(2021 - i, 1, 1) if i > 0 else None,
                    description=f"Detailed description for position {i} with many responsibilities",
                    achievements=[f"Achievement {j}" for j in range(5)],
                    technologies=[f"Tech{j}" for j in range(10)],
                )
                for i in range(10)  # 10 work experiences
            ],
            education=[
                Education(
                    degree=f"Degree {i}",
                    institution=f"University {i}",
                    location="San Francisco, CA",
                    graduation_date=date(2015 - i, 5, 15),
                )
                for i in range(3)  # 3 education entries
            ],
            skills=[
                Skill(
                    name=f"Skill{i}",
                    category=SkillCategory.TECHNICAL,
                    proficiency=(i % 5) + 1,
                    years_experience=i % 10,
                )
                for i in range(50)  # 50 skills
            ],
            projects=[
                Project(
                    name=f"Project {i}",
                    description=f"Detailed project description {i}",
                    technologies=[f"Tech{j}" for j in range(5)],
                    start_date=date(2023 - i, 1, 1),
                    end_date=date(2023 - i, 6, 1),
                    achievements=[f"Project achievement {j}" for j in range(3)],
                )
                for i in range(20)  # 20 projects
            ],
        )

        agent = ProfileMatchingAgent()
        agent = agent.override(model=TestModel())

        start_time = time.time()
        result = await agent.run(
            user_profile=large_profile,
            job_analysis=senior_python_job_analysis,
        )
        end_time = time.time()

        # Even with large profile, must meet performance requirement
        execution_time = end_time - start_time
        assert execution_time < 5.0, f"Large profile execution time {execution_time:.2f}s exceeds 5 second requirement"

        # Should still produce valid results
        assert isinstance(result.output, MatchingResult)
        assert 0 <= result.output.overall_match_score <= 1
        assert 0 <= result.output.confidence_score <= 1


class TestProfileMatchingAgentErrorHandling:
    """Test Profile Matching Agent error handling and edge cases."""

    async def test_conflicting_profile_data(self, senior_python_job_analysis):
        """Test handling of conflicting data in user profile."""
        # This test will FAIL until Profile Matching Agent is implemented
        from src.agents.profile_matching import ProfileMatchingAgent

        # Create profile with conflicting skill data
        conflicting_profile = UserProfile(
            version="1.0",
            metadata={"created_at": "2025-09-17T00:00:00Z", "updated_at": "2025-09-17T00:00:00Z"},
            contact=ContactInfo(
                name="Conflicted User",
                email="conflicted@example.com",
                location="San Francisco, CA",
            ),
            professional_summary="Claims 10 years Python experience",
            experience=[
                WorkExperience(
                    position="Junior Developer",  # Junior but claiming senior experience
                    company="TechCorp",
                    location="San Francisco, CA",
                    start_date=date(2023, 1, 1),  # Only 1 year actual experience
                    end_date=None,
                    description="Learning Python development",
                    achievements=["Completed basic Python tutorials"],
                    technologies=["Python"],
                ),
            ],
            education=[],
            skills=[
                Skill(
                    name="Python",
                    category=SkillCategory.TECHNICAL,
                    proficiency=5,  # Claims expert level
                    years_experience=10,  # Claims 10 years but only 1 year work experience
                ),
            ],
        )

        agent = ProfileMatchingAgent()
        agent = agent.override(model=TestModel())

        result = await agent.run(
            user_profile=conflicting_profile,
            job_analysis=senior_python_job_analysis,
        )

        # Should handle conflicting data gracefully
        assert isinstance(result.output, MatchingResult)

        # Should have lower confidence due to conflicting information
        assert result.output.confidence_score < 0.8, "Should have lower confidence for conflicting data"

        # Should still provide reasonable match score based on available evidence
        assert 0 <= result.output.overall_match_score <= 1

    async def test_minimal_job_requirements(self, high_match_profile):
        """Test handling of job analysis with minimal requirements."""
        # This test will FAIL until Profile Matching Agent is implemented
        from src.agents.profile_matching import ProfileMatchingAgent

        minimal_job = JobAnalysis(
            company_name="MinimalCorp",
            job_title="Developer",
            location="Remote",
            requirements=[
                JobRequirement(
                    skill="Programming",
                    importance=3,
                    category=SkillCategory.TECHNICAL,
                    is_required=True,
                    context="Any programming language",
                ),
            ],
            key_responsibilities=["Write code"],
            company_culture="Flexible",
            role_level=ResponsibilityLevel.JUNIOR,
            industry="Technology",
            analysis_timestamp="2025-09-18T12:00:00Z",
        )

        agent = ProfileMatchingAgent()
        agent = agent.override(model=TestModel())

        result = await agent.run(
            user_profile=high_match_profile,
            job_analysis=minimal_job,
        )

        # Should handle minimal job requirements
        assert isinstance(result.output, MatchingResult)

        # High-skilled profile should match well with minimal requirements
        assert result.output.overall_match_score > 0.7, "Skilled profile should match minimal requirements well"

        # Should have reasonable confidence
        assert result.output.confidence_score > 0.6, "Should have reasonable confidence"