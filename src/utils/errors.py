"""Error handling utilities for the Resume Assistant API.

Constitutional compliance: Small utility functions (<30 lines) for mechanical error operations.
No complex logic, focused on structured error responses and logging patterns.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional, Union

from fastapi import HTTPException, status


def format_error_response(
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    status_code: int = 500
) -> Dict[str, Any]:
    """Format standardized error response for API endpoints.

    Args:
        error_code: Machine-readable error identifier (e.g., 'AGENT_TIMEOUT')
        message: Human-readable error message
        details: Optional additional error context
        status_code: HTTP status code

    Returns:
        Standardized error response dictionary
    """
    response = {
        "error": {
            "code": error_code,
            "message": message,
            "status_code": status_code,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }

    if details:
        response["error"]["details"] = sanitize_error_details(details)

    return response


def log_agent_error(
    agent_name: str,
    error: Exception,
    input_data: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """Log agent-specific failures with structured context.

    Args:
        agent_name: Name of the failing agent
        error: The exception that occurred
        input_data: Sanitized input data (optional)
        context: Additional context for debugging (optional)
    """
    log_entry = {
        "level": "ERROR",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "component": "agent",
        "agent_name": agent_name,
        "error_type": type(error).__name__,
        "error_message": str(error),
    }

    if input_data:
        log_entry["input_data"] = sanitize_error_details(input_data)

    if context:
        log_entry["context"] = sanitize_error_details(context)

    print(json.dumps(log_entry), file=sys.stderr)


def create_http_exception(
    status_code: int,
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None
) -> HTTPException:
    """Create HTTPException with standardized error format.

    Args:
        status_code: HTTP status code
        error_code: Machine-readable error identifier
        message: Human-readable error message
        details: Optional additional error context

    Returns:
        FastAPI HTTPException with structured detail
    """
    error_response = format_error_response(error_code, message, details, status_code)
    return HTTPException(status_code=status_code, detail=error_response["error"])


def log_api_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    error: Optional[str] = None
) -> None:
    """Log API request/response for debugging and monitoring.

    Args:
        method: HTTP method (GET, POST, etc.)
        path: API endpoint path
        status_code: HTTP response status code
        duration_ms: Request duration in milliseconds
        error: Optional error message for failed requests
    """
    log_entry = {
        "level": "INFO" if status_code < 400 else "ERROR",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "component": "api",
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": round(duration_ms, 2)
    }

    if error:
        log_entry["error"] = error

    print(json.dumps(log_entry), file=sys.stderr)


def sanitize_error_details(details: Dict[str, Any]) -> Dict[str, Any]:
    """Remove sensitive information from error details.

    Args:
        details: Raw error details dictionary

    Returns:
        Sanitized error details with sensitive data removed
    """
    sensitive_keys = {
        "password", "token", "api_key", "secret", "auth", "authorization",
        "jwt", "session", "cookie", "credentials", "private_key", "ssn",
        "credit_card", "email", "phone", "address"
    }

    sanitized = {}
    for key, value in details.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_error_details(value)
        elif isinstance(value, str) and len(value) > 200:
            sanitized[key] = value[:200] + "...[TRUNCATED]"
        else:
            sanitized[key] = value

    return sanitized


# Common error codes for agent-chain operations
class ErrorCodes:
    """Standard error codes for Resume Assistant operations."""

    # Agent errors
    AGENT_TIMEOUT = "AGENT_TIMEOUT"
    AGENT_VALIDATION_FAILED = "AGENT_VALIDATION_FAILED"
    AGENT_MODEL_ERROR = "AGENT_MODEL_ERROR"
    AGENT_CHAIN_INTERRUPTED = "AGENT_CHAIN_INTERRUPTED"

    # Data errors
    PROFILE_NOT_FOUND = "PROFILE_NOT_FOUND"
    INVALID_JOB_POSTING = "INVALID_JOB_POSTING"
    RESUME_GENERATION_FAILED = "RESUME_GENERATION_FAILED"

    # System errors
    FILE_SYSTEM_ERROR = "FILE_SYSTEM_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"

    # API errors
    INVALID_REQUEST = "INVALID_REQUEST"
    AUTHENTICATION_FAILED = "AUTHENTICATION_FAILED"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"


# Common HTTP exceptions for quick use
def agent_timeout_exception(agent_name: str) -> HTTPException:
    """Quick helper for agent timeout errors."""
    return create_http_exception(
        status.HTTP_504_GATEWAY_TIMEOUT,
        ErrorCodes.AGENT_TIMEOUT,
        f"Agent '{agent_name}' timed out during execution"
    )


def profile_not_found_exception() -> HTTPException:
    """Quick helper for missing profile errors."""
    return create_http_exception(
        status.HTTP_404_NOT_FOUND,
        ErrorCodes.PROFILE_NOT_FOUND,
        "User profile not found or not properly configured"
    )


def invalid_job_posting_exception(reason: str) -> HTTPException:
    """Quick helper for invalid job posting errors."""
    return create_http_exception(
        status.HTTP_422_UNPROCESSABLE_ENTITY,
        ErrorCodes.INVALID_JOB_POSTING,
        f"Invalid job posting format: {reason}"
    )