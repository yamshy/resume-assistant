"""
Integration tests for Job Analysis Agent performance and accuracy.

This test suite validates the Job Analysis Agent's ability to:
1. Process various job posting formats within <5 second performance requirement
2. Extract structured JobAnalysis data accurately
3. Handle edge cases and malformed inputs gracefully
4. Maintain consistent performance across different complexities

As per TDD principles, these tests will FAIL initially until the Job Analysis Agent is implemented.
"""

import time

import pytest
from pydantic_ai.models.test import TestModel

# These imports will fail until the agent is implemented - this is expected for TDD
try:
    from resume_core.agents.job_analysis_agent import JobAnalysisAgent
    from resume_core.models.job_analysis import JobAnalysis, JobRequirement, ResponsibilityLevel
except ImportError:
    # Expected to fail in TDD - agents and models don't exist yet
    pytest.skip("Job Analysis Agent and models not implemented yet", allow_module_level=True)


class TestJobAnalysisAgentPerformance:
    """Integration tests for Job Analysis Agent performance and accuracy."""

    @pytest.fixture
    def job_analysis_agent(self):
        """Create a Job Analysis Agent with TestModel for integration testing."""
        # This will fail until agent is implemented - expected for TDD
        agent = JobAnalysisAgent()
        # Use TestModel to mock LLM responses for deterministic testing
        return agent.override(model=TestModel())

    @pytest.fixture
    def standard_job_posting(self) -> str:
        """Standard job posting with clear requirements structure."""
        return """
        Software Engineer - Backend Development
        TechCorp Inc.
        San Francisco, CA

        We are seeking a skilled Backend Software Engineer to join our growing team.

        Requirements:
        - 3+ years of Python development experience
        - Experience with FastAPI and SQLAlchemy
        - Knowledge of PostgreSQL and Redis
        - Understanding of microservices architecture
        - Experience with Docker and Kubernetes

        Preferred Qualifications:
        - AWS cloud platform experience
        - GraphQL API development
        - Test-driven development practices

        Responsibilities:
        - Design and implement scalable backend services
        - Collaborate with frontend teams on API design
        - Optimize database performance and queries
        - Participate in code reviews and technical discussions

        We offer competitive salary ($120,000 - $160,000), comprehensive health benefits,
        and flexible remote work options.
        """

    @pytest.fixture
    def complex_job_posting(self) -> str:
        """Complex job posting with multiple sections and detailed requirements."""
        return """
        SENIOR FULL-STACK ENGINEER | AI/ML PLATFORM
        InnovateAI Solutions | Remote (US) | $140K-$200K

        🚀 ABOUT THE ROLE
        Join our cutting-edge AI platform team as a Senior Full-Stack Engineer! You'll architect
        and build the next generation of machine learning infrastructure serving millions of users.

        💻 TECHNICAL REQUIREMENTS (MUST HAVE):
        ✓ 5+ years full-stack development (React, Node.js, Python)
        ✓ Deep expertise in TypeScript/JavaScript ES6+
        ✓ Production experience with ML frameworks (TensorFlow, PyTorch, scikit-learn)
        ✓ Cloud platforms: AWS (required), GCP or Azure (nice-to-have)
        ✓ Database expertise: PostgreSQL, MongoDB, Redis, Elasticsearch
        ✓ Container orchestration: Docker, Kubernetes in production
        ✓ API design: REST, GraphQL, gRPC protocols

        🎯 PREFERRED SKILLS:
        • DevOps: Terraform, Jenkins, GitLab CI/CD
        • Message queues: Apache Kafka, RabbitMQ
        • Monitoring: DataDog, Prometheus, Grafana
        • Security: OAuth2, JWT, RBAC implementation
        • Frontend: Next.js, Redux Toolkit, Material-UI

        📋 RESPONSIBILITIES:
        → Lead architecture decisions for scalable ML inference pipelines
        → Mentor junior developers and conduct technical interviews
        → Design real-time data processing systems handling 1M+ requests/day
        → Collaborate with data scientists on model deployment strategies
        → Optimize system performance for sub-100ms API response times

        🏆 WHAT WE OFFER:
        💰 Salary: $140,000 - $200,000 + equity package
        🏥 Premium health/dental/vision insurance
        🏖️ Unlimited PTO policy
        💻 $3,000 annual learning & development budget
        🏠 Remote-first culture with quarterly team meetups

        APPLY NOW: Send your GitHub profile and portfolio showcasing ML projects!
        """

    @pytest.fixture
    def minimal_job_posting(self) -> str:
        """Minimal job posting with limited information."""
        return """
        Python Developer Needed

        Small startup looking for Python developer.
        Experience with web development.
        Remote work available.

        Contact: jobs@startup.com
        """

    @pytest.fixture
    def malformed_job_posting(self) -> str:
        """Job posting with unusual formatting and scattered information."""
        return """
        *** URGENT HIRING *** DEVELOPER POSITION ***

        company: mega corp solutions ltd
        location: new york / remote hybrid
        salary: COMPETITIVE + BONUSES!!!

        we need someone with:
        python (5 years minimum!!!)
        sql databases
        some frontend stuff maybe react???
        apis and microservices
        cloud (aws preferred)

        responsibilities include but not limited to:
        - coding
        - debugging
        - meetings
        - other duties as assigned

        benefits:
        health insurance
        401k
        free coffee
        ping pong table

        send resume to hr@megacorp.com ASAP!!!
        NO RECRUITERS!!!
        """

    @pytest.mark.asyncio
    async def test_standard_job_posting_analysis(self, job_analysis_agent, standard_job_posting):
        """Test analysis of standard job posting format within performance constraints."""
        start_time = time.time()

        # This will fail until JobAnalysisAgent is implemented
        result = await job_analysis_agent.run(standard_job_posting)

        execution_time = time.time() - start_time

        # Performance requirement: <5 seconds per constitution
        assert execution_time < 5.0, f"Analysis took {execution_time:.2f}s, exceeds 5s limit"

        # Validate structured output
        assert isinstance(result, JobAnalysis)
        assert result.company_name == "TechCorp Inc."
        assert result.job_title == "Software Engineer - Backend Development"
        assert result.location == "San Francisco, CA"
        assert result.role_level in [ResponsibilityLevel.MID, ResponsibilityLevel.SENIOR]

        # Validate extracted requirements
        assert len(result.requirements) >= 5
        python_req = next((req for req in result.requirements if "python" in req.skill.lower()), None)
        assert python_req is not None
        assert python_req.is_required is True
        assert python_req.importance >= 4

        # Validate responsibilities extraction
        assert len(result.key_responsibilities) >= 3
        assert any("backend" in resp.lower() for resp in result.key_responsibilities)

    @pytest.mark.asyncio
    async def test_complex_job_posting_analysis(self, job_analysis_agent, complex_job_posting):
        """Test analysis of complex job posting with multiple sections and detailed requirements."""
        start_time = time.time()

        result = await job_analysis_agent.run(complex_job_posting)

        execution_time = time.time() - start_time

        # Performance requirement must still be met for complex postings
        assert execution_time < 5.0, f"Complex analysis took {execution_time:.2f}s, exceeds 5s limit"

        # Validate complex extraction
        assert isinstance(result, JobAnalysis)
        assert result.company_name == "InnovateAI Solutions"
        assert "full-stack" in result.job_title.lower() or "full stack" in result.job_title.lower()
        assert result.role_level == ResponsibilityLevel.SENIOR
        assert result.salary_range is not None
        assert "$140" in result.salary_range and "$200" in result.salary_range

        # Should extract more requirements from complex posting
        assert len(result.requirements) >= 10

        # Validate specific technology extraction
        tech_skills = [req.skill.lower() for req in result.requirements]
        assert any("react" in skill for skill in tech_skills)
        assert any("python" in skill for skill in tech_skills)
        assert any("typescript" in skill for skill in tech_skills)
        assert any("aws" in skill for skill in tech_skills)

        # Validate benefits extraction
        assert len(result.benefits) >= 3
        assert any("health" in benefit.lower() for benefit in result.benefits)

    @pytest.mark.asyncio
    async def test_minimal_job_posting_analysis(self, job_analysis_agent, minimal_job_posting):
        """Test analysis of minimal job posting with limited information."""
        start_time = time.time()

        result = await job_analysis_agent.run(minimal_job_posting)

        execution_time = time.time() - start_time

        # Performance requirement applies even to minimal postings
        assert execution_time < 5.0, f"Minimal analysis took {execution_time:.2f}s, exceeds 5s limit"

        # Should still extract basic information
        assert isinstance(result, JobAnalysis)
        assert "python" in result.job_title.lower()
        assert len(result.requirements) >= 1

        # Should handle missing information gracefully
        python_req = next((req for req in result.requirements if "python" in req.skill.lower()), None)
        assert python_req is not None

    @pytest.mark.asyncio
    async def test_malformed_job_posting_analysis(self, job_analysis_agent, malformed_job_posting):
        """Test analysis of job posting with unusual formatting."""
        start_time = time.time()

        result = await job_analysis_agent.run(malformed_job_posting)

        execution_time = time.time() - start_time

        # Performance requirement must be maintained even for malformed input
        assert execution_time < 5.0, f"Malformed analysis took {execution_time:.2f}s, exceeds 5s limit"

        # Should normalize and extract meaningful data despite poor formatting
        assert isinstance(result, JobAnalysis)
        assert "mega corp" in result.company_name.lower() or "megacorp" in result.company_name.lower()
        assert "new york" in result.location.lower() or "remote" in result.location.lower()

        # Should still extract technical requirements
        assert len(result.requirements) >= 3
        tech_skills = [req.skill.lower() for req in result.requirements]
        assert any("python" in skill for skill in tech_skills)
        assert any("sql" in skill for skill in tech_skills)

    @pytest.mark.asyncio
    async def test_performance_consistency_across_complexities(self, job_analysis_agent):
        """Test that performance remains consistent across different job posting complexities."""
        job_postings = [
            "Python Developer - 2 years experience required.",
            """Software Engineer at TechCorp
            Requirements: Python, FastAPI, PostgreSQL
            Location: San Francisco, CA
            Salary: $100k-$140k""",
            self.complex_job_posting.__wrapped__(self)  # Get fixture value directly
        ]

        execution_times = []

        for posting in job_postings:
            start_time = time.time()
            result = await job_analysis_agent.run(posting)
            execution_time = time.time() - start_time
            execution_times.append(execution_time)

            # Each analysis must meet performance requirement
            assert execution_time < 5.0, f"Analysis took {execution_time:.2f}s, exceeds 5s limit"
            assert isinstance(result, JobAnalysis)

        # Performance should be relatively consistent (variance < 3x)
        min_time = min(execution_times)
        max_time = max(execution_times)
        variance_ratio = max_time / min_time if min_time > 0 else float('inf')

        assert variance_ratio < 3.0, f"Performance variance too high: {variance_ratio:.2f}x"

    @pytest.mark.asyncio
    async def test_error_handling_empty_input(self, job_analysis_agent):
        """Test error handling for empty or whitespace-only input."""
        start_time = time.time()

        with pytest.raises(ValueError, match="Job posting content cannot be empty"):
            await job_analysis_agent.run("")

        execution_time = time.time() - start_time

        # Error handling should also be fast
        assert execution_time < 1.0, f"Error handling took {execution_time:.2f}s, too slow"

    @pytest.mark.asyncio
    async def test_error_handling_invalid_input(self, job_analysis_agent):
        """Test error handling for non-job-posting content."""
        start_time = time.time()

        # Should handle non-job content gracefully or raise appropriate error
        invalid_content = "This is just random text that has nothing to do with jobs or hiring."

        result = await job_analysis_agent.run(invalid_content)

        execution_time = time.time() - start_time

        # Should still complete within time limit
        assert execution_time < 5.0, f"Invalid input handling took {execution_time:.2f}s"

        # Should either return minimal JobAnalysis or raise appropriate error
        if isinstance(result, JobAnalysis):
            # If it attempts to analyze, should have very low confidence
            assert len(result.requirements) == 0 or all(req.importance <= 2 for req in result.requirements)

    @pytest.mark.asyncio
    async def test_batch_processing_performance(self, job_analysis_agent):
        """Test performance when processing multiple job postings in sequence."""
        job_postings = [
            "Python Developer - Entry Level",
            "Senior Backend Engineer - 5+ years Python, FastAPI",
            "Full Stack Developer - React, Node.js, PostgreSQL"
        ]

        start_time = time.time()

        results = []
        for posting in job_postings:
            result = await job_analysis_agent.run(posting)
            results.append(result)

        total_execution_time = time.time() - start_time

        # Batch processing should scale linearly, not exponentially
        expected_max_time = len(job_postings) * 5.0  # 5s per posting
        assert total_execution_time < expected_max_time, \
            f"Batch processing took {total_execution_time:.2f}s for {len(job_postings)} postings"

        # All results should be valid
        assert len(results) == len(job_postings)
        for result in results:
            assert isinstance(result, JobAnalysis)
            assert len(result.requirements) > 0


class TestJobAnalysisAgentAccuracy:
    """Integration tests focused on Job Analysis Agent accuracy and data quality."""

    @pytest.fixture
    def job_analysis_agent(self):
        """Create a Job Analysis Agent with TestModel for accuracy testing."""
        agent = JobAnalysisAgent()
        return agent.override(model=TestModel())

    @pytest.mark.asyncio
    async def test_requirement_importance_ranking(self, job_analysis_agent):
        """Test that agent correctly ranks requirement importance."""
        job_posting = """
        Senior Python Developer - URGENT HIRING

        MUST HAVE (Required):
        - 5+ years Python experience (CRITICAL)
        - FastAPI framework expertise (ESSENTIAL)
        - PostgreSQL database skills (REQUIRED)

        Nice to Have:
        - AWS experience (preferred)
        - GraphQL knowledge (bonus)
        """

        result = await job_analysis_agent.run(job_posting)

        # Required skills should have higher importance scores
        required_skills = [req for req in result.requirements if req.is_required]
        preferred_skills = [req for req in result.requirements if not req.is_required]

        assert len(required_skills) >= 3
        assert len(preferred_skills) >= 2

        # Required skills should have importance 4-5
        for req in required_skills:
            assert req.importance >= 4, f"Required skill '{req.skill}' has low importance: {req.importance}"

        # Preferred skills should have importance 1-3
        for req in preferred_skills:
            assert req.importance <= 3, f"Preferred skill '{req.skill}' has high importance: {req.importance}"

    @pytest.mark.asyncio
    async def test_salary_extraction_accuracy(self, job_analysis_agent):
        """Test accurate salary range extraction from various formats."""
        salary_formats = [
            ("Salary: $80,000 - $120,000", "$80,000 - $120,000"),
            ("80k-120k annually", "80k-120k"),
            ("Compensation range: $80K to $120K", "$80K to $120K"),
            ("Up to $120,000 per year", "$120,000"),
        ]

        for job_text, expected_salary in salary_formats:
            full_posting = f"""
            Software Developer
            Company ABC
            Location: Remote

            {job_text}

            Requirements:
            - Python experience
            - Database knowledge
            """

            result = await job_analysis_agent.run(full_posting)

            assert result.salary_range is not None, f"Failed to extract salary from: {job_text}"
            # Should contain key salary numbers
            if "80" in expected_salary:
                assert "80" in result.salary_range
            if "120" in expected_salary:
                assert "120" in result.salary_range

    @pytest.mark.asyncio
    async def test_role_level_classification_accuracy(self, job_analysis_agent):
        """Test accurate role level classification based on job requirements."""
        role_level_cases = [
            ("Junior Python Developer - 0-2 years experience", ResponsibilityLevel.JUNIOR),
            ("Python Developer - 3-5 years experience", ResponsibilityLevel.MID),
            ("Senior Software Engineer - 5+ years, lead projects", ResponsibilityLevel.SENIOR),
            ("Engineering Manager - manage team of 8+ developers", ResponsibilityLevel.LEAD),
            ("VP of Engineering - strategic leadership", ResponsibilityLevel.EXECUTIVE),
        ]

        for job_description, expected_level in role_level_cases:
            full_posting = f"""
            {job_description}
            TechCorp Inc.
            San Francisco, CA

            Requirements:
            - Python programming
            - Problem solving skills
            """

            result = await job_analysis_agent.run(full_posting)

            assert result.role_level == expected_level, \
                f"Expected {expected_level} for '{job_description}', got {result.role_level}"