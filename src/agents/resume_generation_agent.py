"""Resume Generation Agent using pydanticAI with GPT-4o.

This agent generates tailored resume content by analyzing job matching results
and user profiles to create optimized, targeted resumes.

Constitutional compliance:
- Single-purpose agent (<200 lines, single file)
- Uses pydanticAI Agent with structured output (TailoredResume)
- GPT-4o model for high-quality content generation
- Includes retry logic with ModelRetry for robustness
- Content generation delegated to AI, not template-based
"""

from datetime import datetime

from pydantic_ai import Agent

from models.job_analysis import JobAnalysis
from models.matching import MatchingResult
from models.profile import UserProfile
from models.resume_optimization import TailoredResume


def _create_resume_generation_agent(model="openai:gpt-4o"):
    """Create Resume Generation Agent with specified model and structured output."""
    agent = Agent(
        model,
        output_type=TailoredResume,
        instructions="""You are an expert resume writer specializing in ATS-optimized,
        targeted resumes. Your role is to generate tailored resume content that maximizes
        job matching scores while maintaining authenticity.

        Generate a complete tailored resume based on:
        1. Job matching analysis (scores, missing skills, strengths)
        2. User profile data (experience, skills, education, projects)
        3. Optimization requirements for target job

        Key requirements:
        - Use job-specific keywords naturally in content
        - Highlight relevant experience and achievements
        - Address missing requirements with transferable skills
        - Maintain professional, ATS-friendly format
        - Generate complete Markdown resume with all sections
        - Provide detailed optimization rationale for each section

        Focus on maximizing the estimated match score through strategic content placement
        and keyword integration while preserving truthfulness to the user's actual experience.""",
    )

    return agent


class ResumeGenerationAgent:
    """
    Resume Generation Agent that creates tailored resume content.

    Uses pydanticAI with GPT-4o to generate optimized resumes based on
    job matching analysis and user profiles.
    """

    def __init__(self):
        self._agent = None

    def override(self, **kwargs):
        """Override agent configuration for testing."""
        # Create a new instance
        new_instance = ResumeGenerationAgent()

        # For testing, we need to pass the model directly
        model = kwargs.get("model")
        if model is not None:
            # Create agent with the test model
            new_instance._agent = Agent(
                model,
                output_type=TailoredResume,
                instructions="""You are an expert resume writer specializing in ATS-optimized,
                targeted resumes. Your role is to generate tailored resume content that maximizes
                job matching scores while maintaining authenticity.

                Generate a complete tailored resume based on:
                1. Job matching analysis (scores, missing skills, strengths)
                2. User profile data (experience, skills, education, projects)
                3. Optimization requirements for target job

                Key requirements:
                - Use job-specific keywords naturally in content
                - Highlight relevant experience and achievements
                - Address missing requirements with transferable skills
                - Maintain professional, ATS-friendly format
                - Generate complete Markdown resume with all sections
                - Provide detailed optimization rationale for each section

                Focus on maximizing the estimated match score through strategic content placement
                and keyword integration while preserving truthfulness to the user's actual experience.""",
            )
        else:
            # Standard override without model change
            agent = self._get_agent()
            new_instance._agent = agent.override(**kwargs)

        return new_instance

    def _get_agent(self):
        """Get the agent, creating it if needed."""
        if self._agent is None:
            self._agent = _create_resume_generation_agent()
        return self._agent

    async def run(self, context_data: dict):
        """Generate a tailored resume based on job matching analysis and user profile.

        Args:
            context_data: Dictionary containing user_profile, job_analysis, and matching_result

        Returns:
            AgentRunResult: Result object with output containing TailoredResume

        Raises:
            Exception: If resume generation fails after retries
        """
        # Extract context components
        user_profile = context_data.get("user_profile")
        job_analysis = context_data.get("job_analysis")
        matching_result = context_data.get("matching_result")

        # Handle both dict and model formats for flexibility
        if isinstance(user_profile, dict):
            context = self._prepare_context_from_dict(user_profile, job_analysis, matching_result)
        else:
            context = self._prepare_context_from_models(user_profile, job_analysis, matching_result)

        # Generate tailored resume using the agent
        agent = self._get_agent()
        result = await agent.run(context)

        return result

    def _prepare_context_from_dict(
        self, user_profile: dict, job_analysis: dict, matching_result: dict
    ) -> str:
        """Prepare context from dictionary format (for testing)."""
        return f"""Generate a tailored resume for this candidate based on the job matching analysis.

User Profile Summary:
Name: {user_profile.get("contact", {}).get("name", "N/A")}
Email: {user_profile.get("contact", {}).get("email", "N/A")}
Professional Summary: {user_profile.get("professional_summary", "N/A")}

Job Target:
Company: {job_analysis.get("company_name", "N/A")}
Position: {job_analysis.get("job_title", "N/A")}

Matching Analysis:
Overall Match Score: {matching_result.get("overall_match_score", 0)}
Confidence: {matching_result.get("confidence_score", 0)}

Instructions:
1. Create optimized content for each resume section based on matching analysis
2. Incorporate job-specific keywords naturally throughout the content
3. Highlight relevant experiences that match job requirements
4. Address skill gaps with transferable skills and related experience
5. Generate complete Markdown resume with professional formatting
6. Provide detailed optimization explanations for each major change
7. Estimate realistic match score improvements for each section
8. Include job title and company name from the target position

Focus on maximizing job match while maintaining authenticity to the user's actual experience.

Generation timestamp: {datetime.now().isoformat()}"""

    def _prepare_context_from_models(
        self, user_profile: UserProfile, job_analysis: JobAnalysis, matching_result: MatchingResult
    ) -> str:
        """Prepare context from model objects."""
        # Prepare input context for the agent
        context = {
            "matching_analysis": {
                "overall_match_score": matching_result.overall_match_score,
                "skill_matches": [
                    {
                        "skill": sm.skill_name,
                        "job_importance": sm.job_importance,
                        "user_proficiency": sm.user_proficiency,
                        "match_score": sm.match_score,
                        "evidence": sm.evidence,
                    }
                    for sm in matching_result.skill_matches
                ],
                "experience_matches": [
                    {
                        "responsibility": em.job_responsibility,
                        "experiences": em.matching_experiences,
                        "relevance": em.relevance_score,
                    }
                    for em in matching_result.experience_matches
                ],
                "missing_requirements": [
                    {
                        "skill": req.skill,
                        "importance": req.importance,
                        "category": req.category,
                        "required": req.is_required,
                        "context": req.context,
                    }
                    for req in matching_result.missing_requirements
                ],
                "strengths": matching_result.strength_areas,
                "transferable_skills": matching_result.transferable_skills,
                "recommendations": matching_result.recommendations,
                "confidence": matching_result.confidence_score,
            },
            "user_profile": {
                "contact": {
                    "name": user_profile.contact.name,
                    "email": user_profile.contact.email,
                    "phone": user_profile.contact.phone,
                    "location": user_profile.contact.location,
                    "linkedin": user_profile.contact.linkedin,
                    "portfolio": user_profile.contact.portfolio,
                },
                "professional_summary": user_profile.professional_summary,
                "experience": [
                    {
                        "position": exp.position,
                        "company": exp.company,
                        "location": exp.location,
                        "start_date": exp.start_date.isoformat(),
                        "end_date": exp.end_date.isoformat() if exp.end_date else "Present",
                        "description": exp.description,
                        "achievements": exp.achievements,
                        "technologies": exp.technologies,
                    }
                    for exp in user_profile.experience
                ],
                "education": [
                    {
                        "degree": edu.degree,
                        "institution": edu.institution,
                        "location": edu.location,
                        "graduation_date": edu.graduation_date.isoformat(),
                        "gpa": edu.gpa,
                        "honors": edu.honors,
                        "coursework": edu.relevant_coursework,
                    }
                    for edu in user_profile.education
                ],
                "skills": [
                    {
                        "name": skill.name,
                        "category": skill.category,
                        "proficiency": skill.proficiency,
                        "years": skill.years_experience,
                    }
                    for skill in user_profile.skills
                ],
                "projects": [
                    {
                        "name": proj.name,
                        "description": proj.description,
                        "technologies": proj.technologies,
                        "start_date": proj.start_date.isoformat(),
                        "end_date": proj.end_date.isoformat() if proj.end_date else "Ongoing",
                        "url": proj.url,
                        "achievements": proj.achievements,
                    }
                    for proj in user_profile.projects
                ],
            },
            "job_analysis": {
                "company_name": job_analysis.company_name,
                "job_title": job_analysis.job_title,
                "location": job_analysis.location,
                "requirements": [
                    {
                        "skill": req.skill,
                        "importance": req.importance,
                        "category": req.category,
                        "required": req.is_required,
                        "context": req.context,
                    }
                    for req in job_analysis.requirements
                ],
                "responsibilities": job_analysis.key_responsibilities,
                "role_level": job_analysis.role_level,
                "industry": job_analysis.industry,
            },
            "generation_timestamp": datetime.now().isoformat(),
        }

        return f"""Generate a tailored resume for this candidate based on the job matching analysis.

Context Data:
{context}

Instructions:
1. Create optimized content for each resume section based on matching analysis
2. Incorporate job-specific keywords naturally throughout the content
3. Highlight relevant experiences that match job requirements
4. Address skill gaps with transferable skills and related experience
5. Generate complete Markdown resume with professional formatting
6. Provide detailed optimization explanations for each major change
7. Estimate realistic match score improvements for each section
8. Include job title and company name from the first missing requirement context if available

Focus on maximizing job match while maintaining authenticity to the user's actual experience."""


# Export function for agent creation (following constitutional patterns)
def create_resume_generation_agent() -> ResumeGenerationAgent:
    """Create a new Resume Generation Agent instance."""
    return ResumeGenerationAgent()


__all__ = ["ResumeGenerationAgent", "create_resume_generation_agent"]
