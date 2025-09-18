"""
Integration tests for Validation Agent effectiveness.

This is a TDD integration test that MUST FAIL initially since the Validation Agent doesn't exist yet.
Tests validate agent accuracy, error detection, and performance timing per constitution requirements.
"""

import time
from unittest.mock import patch

import pytest
from pydantic_ai.models.test import TestModel

# This import will fail initially - that's expected for TDD
try:
    from resume_core.agents.validation_agent import ValidationAgent, ValidationResult
except ImportError:
    # Expected to fail - agent doesn't exist yet
    ValidationAgent = None
    ValidationResult = None


class TestValidationAgentIntegration:
    """Integration tests for Validation Agent effectiveness and performance."""

    @pytest.fixture
    def mock_validation_agent(self):
        """Mock Validation Agent using TestModel for testing without external API dependencies."""
        if ValidationAgent is None:
            pytest.skip("ValidationAgent not implemented yet - TDD test")

        # Override with TestModel for testing (GPT-4o-mini used in production)
        agent = ValidationAgent()
        return agent.override(model=TestModel())

    @pytest.fixture
    def valid_resume_sample(self):
        """Sample resume with accurate content for validation testing."""
        return {
            "personal_info": {
                "name": "John Smith",
                "email": "john.smith@email.com",
                "phone": "+1-555-0123",
                "location": "San Francisco, CA"
            },
            "experience": [
                {
                    "company": "TechCorp Inc",
                    "position": "Senior Software Engineer",
                    "start_date": "2020-01-15",
                    "end_date": "2023-06-30",
                    "responsibilities": [
                        "Led team of 5 developers in building scalable web applications",
                        "Implemented CI/CD pipelines reducing deployment time by 40%"
                    ]
                }
            ],
            "education": [
                {
                    "institution": "Stanford University",
                    "degree": "Bachelor of Science in Computer Science",
                    "graduation_date": "2019-06-15",
                    "gpa": 3.8
                }
            ],
            "skills": ["Python", "JavaScript", "React", "Node.js", "AWS"]
        }

    @pytest.fixture
    def source_profile_data(self):
        """Source profile data for validation comparison."""
        return {
            "personal_info": {
                "name": "John Smith",
                "email": "john.smith@email.com",
                "phone": "+1-555-0123",
                "location": "San Francisco, CA"
            },
            "work_history": [
                {
                    "company": "TechCorp Inc",
                    "position": "Senior Software Engineer",
                    "start_date": "2020-01-15",
                    "end_date": "2023-06-30",
                    "achievements": [
                        "Led team of 5 developers in building scalable web applications",
                        "Implemented CI/CD pipelines reducing deployment time by 40%",
                        "Mentored 3 junior developers"
                    ]
                }
            ],
            "education": [
                {
                    "institution": "Stanford University",
                    "degree": "Bachelor of Science in Computer Science",
                    "graduation_date": "2019-06-15",
                    "gpa": 3.8
                }
            ],
            "technical_skills": ["Python", "JavaScript", "React", "Node.js", "AWS", "Docker"]
        }

    @pytest.fixture
    def resume_with_factual_errors(self):
        """Resume with factual errors for validation testing."""
        return {
            "personal_info": {
                "name": "John Smith",
                "email": "john.smith@email.com",
                "phone": "+1-555-0123",
                "location": "San Francisco, CA"
            },
            "experience": [
                {
                    "company": "WrongCorp Ltd",  # Wrong company name
                    "position": "Senior Software Engineer",
                    "start_date": "2019-01-15",  # Wrong start date
                    "end_date": "2024-06-30",    # Wrong end date (future)
                    "responsibilities": [
                        "Led team of 10 developers",  # Wrong team size
                        "Implemented CI/CD pipelines reducing deployment time by 80%"  # Exaggerated
                    ]
                }
            ],
            "education": [
                {
                    "institution": "Harvard University",  # Wrong institution
                    "degree": "Master of Science in Computer Science",  # Wrong degree
                    "graduation_date": "2018-06-15",  # Wrong date
                    "gpa": 4.0  # Wrong GPA
                }
            ],
            "skills": ["Python", "JavaScript", "React", "Node.js", "AWS", "Quantum Computing"]  # Added fake skill
        }

    @pytest.fixture
    def resume_with_inconsistencies(self):
        """Resume with inconsistent information for validation testing."""
        return {
            "personal_info": {
                "name": "John Smith",
                "email": "john.smith@email.com",
                "phone": "+1-555-0123",
                "location": "San Francisco, CA"
            },
            "experience": [
                {
                    "company": "TechCorp Inc",
                    "position": "Senior Software Engineer",
                    "start_date": "2020-01-15",
                    "end_date": "2019-06-30",  # End date before start date
                    "responsibilities": [
                        "Led team of 5 developers in building scalable web applications"
                    ]
                }
            ],
            "education": [
                {
                    "institution": "Stanford University",
                    "degree": "Bachelor of Science in Computer Science",
                    "graduation_date": "2021-06-15",  # Graduation after work start
                    "gpa": 3.8
                }
            ]
        }

    @pytest.fixture
    def resume_with_formatting_issues(self):
        """Resume with formatting issues for validation testing."""
        return {
            "personal_info": {
                "name": "john smith",  # Lowercase name
                "email": "JOHN.SMITH@EMAIL.COM",  # Uppercase email
                "phone": "555-0123",  # Missing country code
                "location": "san francisco, ca"  # Inconsistent capitalization
            },
            "experience": [
                {
                    "company": "techcorp inc",  # Lowercase company
                    "position": "senior software engineer",  # Lowercase position
                    "start_date": "01/15/2020",  # Wrong date format
                    "end_date": "06/30/2023",    # Wrong date format
                    "responsibilities": [
                        "led team of 5 developers in building scalable web applications",  # Lowercase
                        "implemented ci/cd pipelines reducing deployment time by 40%"
                    ]
                }
            ]
        }

    @pytest.fixture
    def resume_missing_critical_sections(self):
        """Resume with missing critical sections for validation testing."""
        return {
            "personal_info": {
                "name": "John Smith",
                # Missing email, phone, location
            },
            # Missing experience section entirely
            "education": [
                {
                    "institution": "Stanford University",
                    # Missing degree, graduation_date
                }
            ]
            # Missing skills section
        }

    @pytest.mark.asyncio
    async def test_valid_resume_validation(self, mock_validation_agent, valid_resume_sample, source_profile_data):
        """Test validation of accurate resume content."""
        if ValidationAgent is None:
            pytest.skip("ValidationAgent not implemented yet - TDD test")

        start_time = time.time()

        result = await mock_validation_agent.run(
            resume_data=valid_resume_sample,
            source_profile=source_profile_data
        )

        validation_time = time.time() - start_time

        # Test performance requirement (<5 seconds per constitution)
        assert validation_time < 5.0, f"Validation took {validation_time:.2f}s, exceeds 5s limit"

        # Test validation result structure
        assert isinstance(result.output, ValidationResult)
        assert result.output.is_valid is True
        assert result.output.confidence > 0.8  # High confidence for valid content
        assert len(result.output.errors) == 0
        assert len(result.output.warnings) == 0

    @pytest.mark.asyncio
    async def test_factual_errors_detection(self, mock_validation_agent, resume_with_factual_errors, source_profile_data):
        """Test detection of factual errors in resume content."""
        if ValidationAgent is None:
            pytest.skip("ValidationAgent not implemented yet - TDD test")

        start_time = time.time()

        result = await mock_validation_agent.run(
            resume_data=resume_with_factual_errors,
            source_profile=source_profile_data
        )

        validation_time = time.time() - start_time
        assert validation_time < 5.0

        # Test error detection
        assert isinstance(result.output, ValidationResult)
        assert result.output.is_valid is False
        assert result.output.confidence < 0.6  # Low confidence due to errors
        assert len(result.output.errors) > 0

        # Check specific error types are detected
        error_types = [error.error_type for error in result.output.errors]
        assert "factual_inconsistency" in error_types
        assert "data_mismatch" in error_types

    @pytest.mark.asyncio
    async def test_inconsistent_information_detection(self, mock_validation_agent, resume_with_inconsistencies, source_profile_data):
        """Test detection of inconsistent information in resume."""
        if ValidationAgent is None:
            pytest.skip("ValidationAgent not implemented yet - TDD test")

        start_time = time.time()

        result = await mock_validation_agent.run(
            resume_data=resume_with_inconsistencies,
            source_profile=source_profile_data
        )

        validation_time = time.time() - start_time
        assert validation_time < 5.0

        # Test inconsistency detection
        assert isinstance(result.output, ValidationResult)
        assert result.output.is_valid is False
        assert len(result.output.errors) > 0

        # Check for logical inconsistency errors
        error_types = [error.error_type for error in result.output.errors]
        assert "logical_inconsistency" in error_types

    @pytest.mark.asyncio
    async def test_formatting_issues_detection(self, mock_validation_agent, resume_with_formatting_issues, source_profile_data):
        """Test detection of formatting issues in resume."""
        if ValidationAgent is None:
            pytest.skip("ValidationAgent not implemented yet - TDD test")

        start_time = time.time()

        result = await mock_validation_agent.run(
            resume_data=resume_with_formatting_issues,
            source_profile=source_profile_data
        )

        validation_time = time.time() - start_time
        assert validation_time < 5.0

        # Test formatting issue detection
        assert isinstance(result.output, ValidationResult)
        assert len(result.output.warnings) > 0  # Formatting issues should be warnings

        # Check for formatting warnings
        warning_types = [warning.warning_type for warning in result.output.warnings]
        assert "formatting_inconsistency" in warning_types

    @pytest.mark.asyncio
    async def test_missing_critical_sections_detection(self, mock_validation_agent, resume_missing_critical_sections, source_profile_data):
        """Test detection of missing critical sections in resume."""
        if ValidationAgent is None:
            pytest.skip("ValidationAgent not implemented yet - TDD test")

        start_time = time.time()

        result = await mock_validation_agent.run(
            resume_data=resume_missing_critical_sections,
            source_profile=source_profile_data
        )

        validation_time = time.time() - start_time
        assert validation_time < 5.0

        # Test missing section detection
        assert isinstance(result.output, ValidationResult)
        assert result.output.is_valid is False
        assert len(result.output.errors) > 0

        # Check for missing section errors
        error_types = [error.error_type for error in result.output.errors]
        assert "missing_required_field" in error_types

    @pytest.mark.asyncio
    async def test_performance_timing_validation(self, mock_validation_agent, valid_resume_sample, source_profile_data):
        """Test that validation consistently meets <5 second performance requirement."""
        if ValidationAgent is None:
            pytest.skip("ValidationAgent not implemented yet - TDD test")

        # Run multiple validations to test consistency
        times = []
        for _ in range(3):
            start_time = time.time()

            await mock_validation_agent.run(
                resume_data=valid_resume_sample,
                source_profile=source_profile_data
            )

            validation_time = time.time() - start_time
            times.append(validation_time)

            # Each individual run must be under 5 seconds
            assert validation_time < 5.0, f"Validation took {validation_time:.2f}s, exceeds 5s limit"

        # Average time should also be well under limit
        avg_time = sum(times) / len(times)
        assert avg_time < 4.0, f"Average validation time {avg_time:.2f}s too close to 5s limit"

    @pytest.mark.asyncio
    async def test_confidence_scoring_accuracy(self, mock_validation_agent, source_profile_data):
        """Test confidence scoring accuracy across different resume qualities."""
        if ValidationAgent is None:
            pytest.skip("ValidationAgent not implemented yet - TDD test")

        # Test with perfect resume (should have high confidence >0.8)
        valid_resume = {
            "personal_info": {"name": "John Smith", "email": "john.smith@email.com"},
            "experience": [{"company": "TechCorp Inc", "position": "Engineer", "start_date": "2020-01-15", "end_date": "2023-06-30"}],
            "education": [{"institution": "Stanford University", "degree": "BS Computer Science"}],
            "skills": ["Python", "JavaScript"]
        }

        result_valid = await mock_validation_agent.run(
            resume_data=valid_resume,
            source_profile=source_profile_data
        )

        # Test with poor resume (should have low confidence <0.6)
        poor_resume = {
            "personal_info": {"name": "Wrong Name"},
            "experience": [{"company": "Fake Corp", "position": "Fake Role"}],
            "education": [],
            "skills": []
        }

        result_poor = await mock_validation_agent.run(
            resume_data=poor_resume,
            source_profile=source_profile_data
        )

        # Verify confidence scoring
        assert result_valid.output.confidence > 0.8, "Valid resume should have high confidence"
        assert result_poor.output.confidence < 0.6, "Poor resume should have low confidence"
        assert result_valid.output.confidence > result_poor.output.confidence, "Valid resume should have higher confidence than poor resume"

    @pytest.mark.asyncio
    async def test_validation_agent_import_failure(self):
        """Test that validates the TDD approach - agent doesn't exist yet."""
        # This test should pass because we expect the import to fail initially
        assert ValidationAgent is None, "ValidationAgent should not exist yet - this is a TDD test"
        assert ValidationResult is None, "ValidationResult should not exist yet - this is a TDD test"