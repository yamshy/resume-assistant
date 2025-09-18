"""
Job Analysis Agent for extracting structured requirements from job postings.

This agent uses GPT-4o to analyze raw job posting text and extract structured
job requirements, company information, and other relevant data for resume tailoring.
Follows agent-chain architecture with structured output and retry logic for robustness.
"""

from datetime import datetime
from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelRetry

from models.job_analysis import JobAnalysis, JobRequirement, ResponsibilityLevel
from models.profile import SkillCategory


class JobAnalysisAgent:
    """
    Job Analysis Agent for extracting structured job requirements from raw job postings.

    Uses GPT-4o model for comprehensive understanding with structured output.
    Designed for <5 second performance per constitutional requirement.
    """

    def __init__(self):
        """Initialize Job Analysis Agent with lazy loading to avoid API key issues."""
        self._agent = None

    def _get_agent(self):
        """Get or create the agent instance."""
        if self._agent is None:
            self._agent = Agent(
                'openai:gpt-4o',
                output_type=JobAnalysis,
                instructions="""
You are an expert job posting analyst. Your task is to analyze raw job posting text
and extract structured information with high accuracy.

Extract the following information:
1. Company details (name, industry, culture)
2. Job details (title, department, location, remote policy)
3. Requirements with importance scoring (1-5 scale)
4. Key responsibilities
5. Role seniority level
6. Salary and benefits if mentioned
7. Preferred qualifications

For requirements:
- Score importance 1-5 (5 = critical, 1 = nice-to-have)
- Categorize skills properly (technical, soft, language, certification)
- Mark as required vs preferred
- Include context where requirement was mentioned

For role level assessment:
- junior: 0-2 years experience, entry-level tasks
- mid: 3-5 years experience, independent work
- senior: 6+ years experience, complex projects, mentoring
- lead: team leadership, technical decisions
- executive: strategic leadership, business decisions

Be accurate and comprehensive. If information is unclear or missing,
use reasonable inference based on context.
                """
            )
        return self._agent

    def override(self, **kwargs):
        """Override agent configuration for testing."""
        # Create a new instance
        new_instance = JobAnalysisAgent()

        # For testing, we need to pass the model directly
        model = kwargs.get('model')
        if model is not None:
            # Create agent with the test model
            new_instance._agent = Agent(
                model,
                output_type=JobAnalysis,
                instructions="""
You are an expert job posting analyst. Your task is to analyze raw job posting text
and extract structured information with high accuracy.

Extract the following information:
1. Company details (name, industry, culture)
2. Job details (title, department, location, remote policy)
3. Requirements with importance scoring (1-5 scale)
4. Key responsibilities
5. Role seniority level
6. Salary and benefits if mentioned
7. Preferred qualifications

For requirements:
- Score importance 1-5 (5 = critical, 1 = nice-to-have)
- Categorize skills properly (technical, soft, language, certification)
- Mark as required vs preferred
- Include context where requirement was mentioned

For role level assessment:
- junior: 0-2 years experience, entry-level tasks
- mid: 3-5 years experience, independent work
- senior: 6+ years experience, complex projects, mentoring
- lead: team leadership, technical decisions
- executive: strategic leadership, business decisions

Be accurate and comprehensive. If information is unclear or missing,
use reasonable inference based on context.
                """
            )
        else:
            # Standard override without model change
            agent = self._get_agent()
            new_instance._agent = agent.override(**kwargs)

        return new_instance

    @classmethod
    def _create_with_agent(cls, agent):
        """Create JobAnalysisAgent instance with custom agent (for testing)."""
        instance = cls.__new__(cls)
        instance._agent = agent
        return instance

    async def run(self, job_posting_text: str) -> JobAnalysis:
        """
        Analyze a raw job posting and extract structured job requirements.

        Args:
            job_posting_text: Raw text from job posting

        Returns:
            JobAnalysis: Structured analysis with requirements and company info

        Raises:
            ValueError: If job posting text is empty
            ModelRetry: If analysis output is incomplete or invalid
        """
        if not job_posting_text or not job_posting_text.strip():
            raise ValueError("Job posting content cannot be empty")

        try:
            agent = self._get_agent()
            result = await agent.run(job_posting_text.strip())

            # Validate output completeness
            self._validate_analysis_output(result.output)

            return result.output

        except Exception as e:
            # Re-raise with context for debugging
            raise Exception(f"Job analysis failed: {str(e)}") from e

    def _validate_analysis_output(self, analysis: JobAnalysis) -> None:
        """Validate that analysis output is complete and valid."""

        # Check required fields are not empty
        if not analysis.company_name.strip():
            raise ModelRetry("Company name cannot be empty")

        if not analysis.job_title.strip():
            raise ModelRetry("Job title cannot be empty")

        # Location is optional for resume tailoring - set default if not specified
        if not analysis.location or not analysis.location.strip():
            analysis.location = "Not specified"

        # Set analysis timestamp if not already set
        if not hasattr(analysis, 'analysis_timestamp') or not analysis.analysis_timestamp:
            from datetime import datetime
            analysis.analysis_timestamp = datetime.now().isoformat()

        # Validate requirements
        if not analysis.requirements:
            raise ModelRetry("At least one job requirement must be extracted")

        for req in analysis.requirements:
            if not 1 <= req.importance <= 5:
                raise ModelRetry(f"Importance score must be 1-5, got {req.importance}")

            if not req.skill.strip():
                raise ModelRetry("Skill name cannot be empty")

            if not req.context.strip():
                raise ModelRetry("Requirement context cannot be empty")

        # Validate responsibilities
        if not analysis.key_responsibilities:
            raise ModelRetry("At least one key responsibility must be extracted")

        for resp in analysis.key_responsibilities:
            if not resp.strip():
                raise ModelRetry("Key responsibility cannot be empty")


# Public interface function for agent creation
def create_job_analysis_agent() -> JobAnalysisAgent:
    """
    Create a new Job Analysis Agent instance.

    Returns:
        JobAnalysisAgent configured with GPT-4o model
    """
    return JobAnalysisAgent()


# Export the main classes for testing and usage
__all__ = ['JobAnalysisAgent', 'create_job_analysis_agent']