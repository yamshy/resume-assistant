"""Input validation and error handling utilities for Resume Assistant API.

Constitutional compliance:
- Small utility functions (<30 lines each)
- Mechanical validation only (no intelligence/reasoning)
- Clear error messages for API responses
- Type hints for all functions
- Support for existing pydantic models
"""

import re
import uuid
from pathlib import Path

# Import will be resolved at runtime when used as part of the main application
try:
    from ..models.profile import UserProfile
except ImportError:
    # For testing purposes, allow import to work without relative path
    try:
        from models.profile import UserProfile
    except ImportError:
        # If neither works, we'll create a stub for type hints
        UserProfile = None


def validate_job_posting_text(text: str) -> tuple[bool, str | None]:
    """Validate job posting text for minimum quality requirements.

    Args:
        text: Raw job posting text to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text or not text.strip():
        return False, "Job posting text cannot be empty"

    cleaned_text = text.strip()

    if len(cleaned_text) < 50:
        return False, "Job posting text must be at least 50 characters long"

    if len(cleaned_text) > 50000:
        return False, "Job posting text must be less than 50,000 characters"

    # Basic content quality checks
    if cleaned_text.count("\n") < 2:
        return False, "Job posting appears to be too simple (needs structure)"

    return True, None


def validate_session_id(session_id: str) -> tuple[bool, str | None]:
    """Validate session ID format (UUID v4).

    Args:
        session_id: Session identifier to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not session_id or not session_id.strip():
        return False, "Session ID cannot be empty"

    try:
        # Validate UUID format and version
        uuid_obj = uuid.UUID(session_id.strip())
        if uuid_obj.version != 4:
            return False, "Session ID must be a valid UUID v4"
        return True, None
    except ValueError:
        return False, "Session ID must be a valid UUID format"


def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """Sanitize filename for safe file system operations.

    Args:
        filename: Raw filename to sanitize
        max_length: Maximum allowed filename length

    Returns:
        Sanitized filename safe for file operations
    """
    if not filename:
        return "untitled"

    # Remove/replace unsafe characters
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", filename.strip())

    # Handle reserved names on Windows
    reserved_names = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }

    name_part = sanitized.split(".")[0].upper()
    if name_part in reserved_names:
        sanitized = f"file_{sanitized}"

    # Limit length and ensure non-empty
    sanitized = sanitized[:max_length] if len(sanitized) > max_length else sanitized
    return sanitized if sanitized else "untitled"


def validate_file_path(file_path: str, allowed_base_dirs: list[str]) -> tuple[bool, str | None]:
    """Validate file path for security (path traversal prevention).

    Args:
        file_path: File path to validate
        allowed_base_dirs: List of allowed base directory paths

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file_path:
        return False, "File path cannot be empty"

    try:
        # Resolve to absolute path to detect traversal attempts
        resolved_path = Path(file_path).resolve()

        # Check if path is within allowed directories
        for base_dir in allowed_base_dirs:
            try:
                resolved_path.relative_to(Path(base_dir).resolve())
                return True, None
            except ValueError:
                continue

        return False, f"File path not within allowed directories: {allowed_base_dirs}"

    except (OSError, ValueError) as e:
        return False, f"Invalid file path: {str(e)}"


def check_profile_completeness(profile) -> tuple[bool, list[str]]:
    """Check profile data completeness for resume generation.

    Args:
        profile: User profile to validate

    Returns:
        Tuple of (is_complete, list_of_missing_fields)
    """
    missing_fields = []

    # Check essential contact info
    if not profile.contact.name.strip():
        missing_fields.append("contact.name")
    if not profile.contact.email:
        missing_fields.append("contact.email")
    if not profile.contact.location.strip():
        missing_fields.append("contact.location")

    # Check professional summary
    if not profile.professional_summary.strip():
        missing_fields.append("professional_summary")

    # Check work experience
    if not profile.experience:
        missing_fields.append("experience (at least one job)")

    # Check education
    if not profile.education:
        missing_fields.append("education (at least one degree)")

    # Check skills
    if not profile.skills:
        missing_fields.append("skills (at least one skill)")

    return len(missing_fields) == 0, missing_fields


def validate_text_length(
    text: str, min_length: int, max_length: int, field_name: str
) -> tuple[bool, str | None]:
    """Validate text field length constraints.

    Args:
        text: Text to validate
        min_length: Minimum required length
        max_length: Maximum allowed length
        field_name: Name of field for error messages

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text:
        return False, f"{field_name} cannot be empty"

    text_length = len(text.strip())

    if text_length < min_length:
        return False, f"{field_name} must be at least {min_length} characters long"

    if text_length > max_length:
        return False, f"{field_name} must be less than {max_length} characters long"

    return True, None


__all__ = [
    "validate_job_posting_text",
    "validate_session_id",
    "sanitize_filename",
    "validate_file_path",
    "check_profile_completeness",
    "validate_text_length",
]
