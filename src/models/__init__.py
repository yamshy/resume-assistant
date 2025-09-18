"""
Data models for resume assistant.

Contains profile models as specified in data-model.md.
"""

# Export profile models from this package
from models.profile import (
    ContactInfo,
    WorkExperience,
    Education,
    SkillCategory,
    Skill,
    Project,
    Publication,
    Award,
    VolunteerWork,
    Language,
    UserProfile,
)

# Re-export validation models for test compatibility (when available)
try:
    from models.validation import (
        ValidationIssue,
        ValidationResult,
    )
    _validation_models = [
        "ValidationIssue",
        "ValidationResult",
    ]
except ImportError:
    _validation_models = []

# Re-export resume optimization models for test compatibility (when available)
try:
    from models.resume_optimization import (
        ContentOptimization,
        TailoredResume,
    )
    _resume_optimization_models = [
        "ContentOptimization",
        "TailoredResume",
    ]
except ImportError:
    _resume_optimization_models = []

# Re-export approval models for test compatibility (when available)
try:
    from models.approval import (
        ApprovalStatus,
        ApprovalRequest,
        ReviewDecision,
        ApprovalWorkflow,
        ResumeSection,
    )
    _approval_models = [
        "ApprovalStatus",
        "ApprovalRequest",
        "ReviewDecision",
        "ApprovalWorkflow",
        "ResumeSection",
    ]
except ImportError:
    # resume_core models not available yet
    _approval_models = []

__all__ = [
    # Profile models
    "ContactInfo",
    "WorkExperience",
    "Education",
    "SkillCategory",
    "Skill",
    "Project",
    "Publication",
    "Award",
    "VolunteerWork",
    "Language",
    "UserProfile",
] + _validation_models + _resume_optimization_models + _approval_models