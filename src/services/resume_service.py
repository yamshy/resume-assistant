"""
Resume Generation Pipeline Service.

Focused service for generating tailored resume content using the Resume Generation Agent.
Handles the core resume creation workflow with input validation and output formatting.

Constitutional compliance:
- Single-purpose service focused on resume generation
- Agent-chain pattern using Resume Generation Agent
- Simple pipeline with structured input/output
- Error handling and validation
"""

import uuid
from datetime import datetime
from typing import Dict, Any

from models.profile import UserProfile
from models.job_analysis import JobAnalysis
from models.matching import MatchingResult
from models.resume_optimization import TailoredResume

from agents.resume_generation_agent import create_resume_generation_agent


class ResumeGenerationService:
    """
    Service for generating tailored resume content.

    Handles the resume generation workflow using the Resume Generation Agent
    with proper input validation and structured output.
    """

    def __init__(self):
        """Initialize service with lazy-loaded resume generation agent."""
        self._resume_agent = None

    def _get_resume_agent(self):
        """Get resume generation agent, creating if needed."""
        if self._resume_agent is None:
            self._resume_agent = create_resume_generation_agent()
        return self._resume_agent

    async def generate_resume(
        self,
        user_profile: UserProfile,
        job_analysis: JobAnalysis,
        matching_result: MatchingResult
    ) -> Dict[str, Any]:
        """
        Generate tailored resume content from profile and job analysis.

        Args:
            user_profile: Complete user profile data
            job_analysis: Analyzed job posting requirements
            matching_result: Profile-job matching analysis

        Returns:
            Dict containing generated resume and metadata

        Raises:
            ValueError: If input validation fails
            Exception: If resume generation fails
        """
        # Validate inputs
        if not user_profile or not job_analysis or not matching_result:
            raise ValueError("All inputs (profile, job_analysis, matching_result) are required")

        generation_id = str(uuid.uuid4())
        start_time = datetime.now()

        try:
            # Prepare context data for resume generation agent
            context_data = {
                "user_profile": user_profile,
                "job_analysis": job_analysis,
                "matching_result": matching_result
            }

            # Generate tailored resume using the agent
            resume_agent = self._get_resume_agent()
            result = await resume_agent.run(context_data)
            tailored_resume = result.output

            # Calculate generation time
            end_time = datetime.now()
            generation_time = (end_time - start_time).total_seconds()

            # Return structured result
            return {
                "generation_id": generation_id,
                "tailored_resume": tailored_resume,
                "generation_time_seconds": generation_time,
                "input_summary": {
                    "job_title": job_analysis.job_title,
                    "company_name": job_analysis.company_name,
                    "match_score": matching_result.overall_match_score,
                    "confidence": matching_result.confidence_score
                },
                "created_at": start_time.isoformat(),
                "completed_at": end_time.isoformat()
            }

        except Exception as e:
            # Add context to error
            error_info = {
                "generation_id": generation_id,
                "error": str(e),
                "error_type": type(e).__name__,
                "failed_at": datetime.now().isoformat()
            }
            raise Exception(f"Resume generation failed: {error_info}") from e

    async def validate_resume_content(self, tailored_resume: TailoredResume) -> Dict[str, Any]:
        """
        Validate generated resume content for basic quality checks.

        Args:
            tailored_resume: Generated resume to validate

        Returns:
            Dict with validation results

        Raises:
            ValueError: If resume is invalid
        """
        if not tailored_resume:
            raise ValueError("Resume content is required for validation")

        validation_result = {
            "is_valid": True,
            "issues": [],
            "warnings": [],
            "content_stats": {}
        }

        # Basic content validation
        if not tailored_resume.resume_content.strip():
            validation_result["is_valid"] = False
            validation_result["issues"].append("Resume content is empty")

        # Check for minimum content length
        content_length = len(tailored_resume.resume_content)
        if content_length < 100:
            validation_result["warnings"].append(f"Resume content is very short ({content_length} characters)")

        # Validate optimizations exist
        if not tailored_resume.content_optimizations:
            validation_result["warnings"].append("No content optimizations provided")

        # Content statistics
        validation_result["content_stats"] = {
            "character_count": content_length,
            "word_count": len(tailored_resume.resume_content.split()),
            "optimization_count": len(tailored_resume.content_optimizations),
            "estimated_match_score": tailored_resume.estimated_match_score
        }

        return validation_result


# Factory function for service creation
def create_resume_generation_service() -> ResumeGenerationService:
    """
    Create a new Resume Generation Service instance.

    Returns:
        ResumeGenerationService configured with Resume Generation Agent
    """
    return ResumeGenerationService()


__all__ = ["ResumeGenerationService", "create_resume_generation_service"]