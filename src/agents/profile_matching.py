"""
Profile Matching Agent for analyzing job-profile compatibility.

This agent analyzes the match between a user profile and job requirements,
providing detailed scoring and recommendations for resume tailoring.

Constitutional compliance:
- Single-purpose agent (<200 lines, single file)
- Uses pydanticAI Agent with structured output (MatchingResult)
- GPT-4o model as specified in constitutional requirements
- AI reasoning over hardcoded rules
- Performance target: <5 seconds per constitutional requirement
"""

from pydantic_ai import Agent
from pydantic_ai.exceptions import ModelRetry

from models.matching import MatchingResult, SkillMatch, ExperienceMatch
from models.job_analysis import JobAnalysis, JobRequirement
from models.profile import UserProfile


def _create_profile_matching_agent(model='openai:gpt-4o'):
    """Create Profile Matching Agent with specified model and structured output."""
    agent = Agent(
        model,
        output_type=MatchingResult,
        instructions="""
        You are a Profile Matching Agent that analyzes how well a user's profile matches a job posting.

        Your task is to:
        1. Compare the user's skills, experience, and qualifications against job requirements
        2. Calculate accurate match scores (0-1) for each skill and overall compatibility
        3. Identify missing requirements and transferable skills
        4. Provide specific recommendations for improvement
        5. Assess experience relevance against job responsibilities

        Scoring Guidelines:
        - overall_match_score: 0-1 based on weighted average of skill matches and experience relevance
        - skill match_score: 1.0 for perfect match (user proficiency >= job importance), scale down based on gap
        - experience relevance_score: 0-1 based on how well past experience aligns with job responsibilities
        - confidence_score: 0-1 based on data completeness and consistency

        For transferable skills, identify skills from the user's background that could apply to missing requirements.
        For recommendations, provide specific, actionable advice for improving candidacy.

        Be thorough but efficient - you must complete analysis in under 5 seconds.
        """
    )


    return agent


class ProfileMatchingAgent:
    """
    Profile Matching Agent that analyzes job-profile compatibility.

    Uses pydanticAI with GPT-4o to perform intelligent matching between user profiles
    and job requirements, providing structured analysis and recommendations.
    """

    def __init__(self):
        self._agent = None

    def override(self, **kwargs):
        """Override agent configuration for testing."""
        # Create a new instance
        new_instance = ProfileMatchingAgent()

        # For testing, we need to pass the model directly
        model = kwargs.get('model')
        if model is not None:
            # Create agent with the test model
            new_instance._agent = Agent(
                model,
                output_type=MatchingResult,
                instructions="""
                You are a Profile Matching Agent that analyzes how well a user's profile matches a job posting.

                Your task is to:
                1. Compare the user's skills, experience, and qualifications against job requirements
                2. Calculate accurate match scores (0-1) for each skill and overall compatibility
                3. Identify missing requirements and transferable skills
                4. Provide specific recommendations for improvement
                5. Assess experience relevance against job responsibilities

                Scoring Guidelines:
                - overall_match_score: 0-1 based on weighted average of skill matches and experience relevance
                - skill match_score: 1.0 for perfect match (user proficiency >= job importance), scale down based on gap
                - experience relevance_score: 0-1 based on how well past experience aligns with job responsibilities
                - confidence_score: 0-1 based on data completeness and consistency

                For transferable skills, identify skills from the user's background that could apply to missing requirements.
                For recommendations, provide specific, actionable advice for improving candidacy.

                Be thorough but efficient - you must complete analysis in under 5 seconds.
                """
            )
        else:
            # Standard override without model change
            agent = self._get_agent()
            new_instance._agent = agent.override(**kwargs)

        return new_instance

    def _get_agent(self):
        """Get the agent, creating it if needed."""
        if self._agent is None:
            self._agent = _create_profile_matching_agent()
        return self._agent

    async def run(self, user_profile: UserProfile, job_analysis: JobAnalysis):
        """
        Analyze the match between user profile and job requirements.

        Args:
            user_profile: Complete user profile with skills, experience, education
            job_analysis: Analyzed job posting with requirements and responsibilities

        Returns:
            MatchingResult with detailed analysis and scores
        """
        # Prepare analysis context for the AI agent
        context = self._prepare_analysis_context(user_profile, job_analysis)

        # Run the AI agent with structured output
        agent = self._get_agent()
        result = await agent.run(context)

        return result

    def _prepare_analysis_context(self, user_profile: UserProfile, job_analysis: JobAnalysis) -> str:
        """Prepare structured context for AI analysis."""

        # Extract user skills for easy comparison
        user_skills = {skill.name.lower(): skill for skill in user_profile.skills}
        user_skill_names = list(user_skills.keys())

        # Extract job requirements
        required_skills = [req.skill for req in job_analysis.requirements if req.is_required]
        preferred_skills = [req.skill for req in job_analysis.requirements if not req.is_required]

        # Build experience summary
        experience_summary = []
        for exp in user_profile.experience:
            experience_summary.append(f"{exp.position} at {exp.company}: {exp.description}")

        context = f"""
PROFILE MATCHING ANALYSIS

USER PROFILE SUMMARY:
Name: {user_profile.contact.name}
Professional Summary: {user_profile.professional_summary}

USER SKILLS ({len(user_profile.skills)} total):
{chr(10).join(f"- {skill.name}: Proficiency {skill.proficiency}/5, {skill.years_experience or 0} years" for skill in user_profile.skills)}

USER EXPERIENCE ({len(user_profile.experience)} positions):
{chr(10).join(experience_summary)}

USER TECHNOLOGIES:
{chr(10).join(set(tech for exp in user_profile.experience for tech in exp.technologies))}

JOB ANALYSIS:
Company: {job_analysis.company_name}
Position: {job_analysis.job_title}
Level: {job_analysis.role_level}

REQUIRED SKILLS ({len(required_skills)}):
{chr(10).join(f"- {req.skill} (Importance: {req.importance}/5) - {req.context}" for req in job_analysis.requirements if req.is_required)}

PREFERRED SKILLS ({len(preferred_skills)}):
{chr(10).join(f"- {req.skill} (Importance: {req.importance}/5) - {req.context}" for req in job_analysis.requirements if not req.is_required)}

KEY RESPONSIBILITIES:
{chr(10).join(f"- {resp}" for resp in job_analysis.key_responsibilities)}

ANALYSIS REQUIREMENTS:
1. For each job requirement, find matching user skills and calculate match_score (0-1)
2. Identify user_proficiency (0 if skill not found, 1-5 based on user data)
3. Provide evidence from user profile for each skill match
4. Calculate overall_match_score based on weighted importance of requirements
5. Identify missing_requirements that user lacks
6. Find strength_areas where user exceeds job needs
7. Identify transferable_skills from user background that could apply to missing areas
8. Provide specific improvement recommendations
9. Match user experience against job responsibilities with relevance_score (0-1)
10. Calculate confidence_score based on data completeness and consistency
"""

        return context


# Export function for agent creation (following constitutional patterns)
def create_profile_matching_agent() -> ProfileMatchingAgent:
    """Create a new Profile Matching Agent instance."""
    return ProfileMatchingAgent()


__all__ = ["ProfileMatchingAgent", "create_profile_matching_agent"]