from __future__ import annotations


class ResumeAssistantError(Exception):
    """Base exception for resume assistant domain."""


class ValidationFailure(ResumeAssistantError):
    """Raised when validation rules cannot be satisfied."""


class NotFoundError(ResumeAssistantError):
    """Raised when requested data cannot be located."""
