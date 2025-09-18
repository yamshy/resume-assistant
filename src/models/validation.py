"""
Validation models for resume quality and accuracy validation.

These models represent the structured output from the Validation Agent,
providing detailed feedback on resume accuracy, quality, and potential issues.
"""

from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    """Individual validation issue identified in resume content.

    Represents a specific problem found during validation with details
    about severity, category, location, and suggested resolution.
    """

    severity: str = Field(description="low, medium, high, critical")
    category: str = Field(description="accuracy, consistency, formatting, content")
    description: str = Field(description="Issue description")
    location: str = Field(description="Where in resume this issue occurs")
    suggestion: str = Field(description="How to fix this issue")
    error_type: str = Field(description="Type of error for categorization")


class ValidationWarning(BaseModel):
    """Individual validation warning for non-critical issues."""

    severity: str = Field(description="low, medium, high")
    category: str = Field(description="formatting, style, optimization")
    description: str = Field(description="Warning description")
    location: str = Field(description="Where in resume this warning occurs")
    suggestion: str = Field(description="How to improve this issue")
    warning_type: str = Field(description="Type of warning for categorization")


class ValidationResult(BaseModel):
    """Complete validation results for a generated resume.

    Contains overall validation status, quality scores, identified issues,
    and strengths from the Validation Agent analysis.
    """

    is_valid: bool = Field(description="Overall validation result")
    accuracy_score: float = Field(ge=0, le=1, description="Accuracy against source profile")
    readability_score: float = Field(ge=0, le=1, description="Content readability and flow")
    keyword_optimization_score: float = Field(ge=0, le=1, description="Keyword usage effectiveness")
    issues: list[ValidationIssue] = Field(description="Identified issues")
    strengths: list[str] = Field(description="Validation strengths identified")
    overall_quality_score: float = Field(ge=0, le=1, description="Overall quality rating")
    validation_timestamp: str = Field(description="When validation was performed")

    # Additional fields expected by tests
    confidence: float = Field(ge=0, le=1, description="Confidence in validation results")
    errors: list[ValidationIssue] = Field(description="Critical validation errors")
    warnings: list[ValidationWarning] = Field(description="Non-critical validation warnings")


__all__ = ["ValidationIssue", "ValidationWarning", "ValidationResult"]
