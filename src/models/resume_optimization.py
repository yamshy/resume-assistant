"""Resume optimization data models for the resume tailoring system.

This module contains pydantic models for resume generation and optimization,
including section-by-section content optimization and tailored resume representation.
"""

from pydantic import BaseModel, Field

from models.approval import ResumeSection


class ContentOptimization(BaseModel):
    """Section-by-section optimization details for resume content.

    Represents how a specific resume section was modified to better match
    job requirements, including the rationale and expected improvements.
    """

    section: ResumeSection = Field(description="Resume section being optimized")
    original_content: str = Field(description="Original content from user profile")
    optimized_content: str = Field(description="Tailored content for this job")
    optimization_reason: str = Field(description="Explanation of changes made")
    keywords_added: list[str] = Field(description="Job-specific keywords incorporated")
    match_improvement: float = Field(ge=0, le=1, description="Expected match score improvement")


class TailoredResume(BaseModel):
    """Complete tailored resume with section-by-section optimizations.

    Represents the final output of the resume generation process, including
    both the complete formatted resume and detailed optimization metadata.
    """

    job_title: str = Field(description="Target job title")
    company_name: str = Field(description="Target company name")
    optimizations: list[ContentOptimization] = Field(description="Section-by-section optimizations")
    full_resume_markdown: str = Field(description="Complete tailored resume in Markdown")
    summary_of_changes: str = Field(description="High-level summary of modifications")
    estimated_match_score: float = Field(ge=0, le=1, description="Estimated overall match score")
    generation_timestamp: str = Field(description="When resume was generated")


__all__ = ["ContentOptimization", "TailoredResume"]
