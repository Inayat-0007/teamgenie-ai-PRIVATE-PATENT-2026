"""
Custom Exception Hierarchy — Centralized error types for TeamGenie AI.

All application errors should use these classes instead of raw ValueError/Exception.
The error_handler middleware maps each type to the correct HTTP status + error code.

Usage:
    from core.exceptions import AuthenticationError, ValidationError, QuotaExceededError
    raise AuthenticationError("Invalid credentials")
    raise ValidationError("match_id is required")
"""

from __future__ import annotations


class TeamGenieError(Exception):
    """Base exception for all TeamGenie application errors."""

    status_code: int = 500
    error_code: str = "internal_error"

    def __init__(self, message: str = "An internal error occurred"):
        self.message = message
        super().__init__(message)


class AuthenticationError(TeamGenieError):
    """Invalid or missing credentials / token."""

    status_code = 401
    error_code = "authentication_failed"


class AuthorizationError(TeamGenieError):
    """User lacks permission for the requested action."""

    status_code = 403
    error_code = "forbidden"


class ValidationError(TeamGenieError):
    """Input data failed validation."""

    status_code = 422
    error_code = "validation_error"


class NotFoundError(TeamGenieError):
    """Requested resource does not exist."""

    status_code = 404
    error_code = "not_found"


class QuotaExceededError(TeamGenieError):
    """User exceeded their rate limit or generation quota."""

    status_code = 429
    error_code = "quota_exceeded"


class ExternalServiceError(TeamGenieError):
    """An external dependency (DB, LLM, vector store) failed."""

    status_code = 502
    error_code = "external_service_error"


class GenerationError(TeamGenieError):
    """AI team generation pipeline failed."""

    status_code = 500
    error_code = "generation_failed"


class FirewallBlockedError(TeamGenieError):
    """Request blocked by AI firewall for suspicious patterns."""

    status_code = 403
    error_code = "firewall_blocked"
