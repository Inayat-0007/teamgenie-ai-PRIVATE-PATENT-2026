"""
Auth Service — Supabase authentication wrapper.
Singleton-style service for sign-in, sign-up, and token refresh.

Security:
  - Uses custom exception types (no raw ValueError leaks)
  - Email validation before Supabase calls
  - Password strength hints
  - Error messages sanitized (never expose Supabase internals to client)
"""

from __future__ import annotations

import os
import re
from typing import Any

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from core.exceptions import AuthenticationError, ValidationError, ExternalServiceError

# Email regex for basic validation before hitting Supabase
_EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")

# Password requirements
_MIN_PASSWORD_LENGTH = 8
_MAX_PASSWORD_LENGTH = 128


def _validate_email(email: str) -> None:
    """Validate email format before sending to external service."""
    if not email or not email.strip():
        raise ValidationError("Email is required")
    if len(email) > 254:
        raise ValidationError("Email address is too long")
    if not _EMAIL_PATTERN.match(email):
        raise ValidationError("Invalid email format")


def _validate_password(password: str) -> None:
    """Validate password strength."""
    if not password:
        raise ValidationError("Password is required")
    if len(password) < _MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Password must be at least {_MIN_PASSWORD_LENGTH} characters")
    if len(password) > _MAX_PASSWORD_LENGTH:
        raise ValidationError(f"Password must be at most {_MAX_PASSWORD_LENGTH} characters")


class AuthService:
    """Supabase authentication service with structured error handling."""

    def __init__(self):
        self.url = os.getenv("SUPABASE_URL", "")
        self.key = os.getenv("SUPABASE_ANON_KEY", "")

        if not self.url or not self.key:
            logger.warning("auth.missing_config", has_url=bool(self.url), has_key=bool(self.key))

    def _get_client(self):
        """Lazily create a Supabase client."""
        if not self.url or not self.key:
            raise ExternalServiceError("Authentication service not configured")
        try:
            from supabase import create_client
            return create_client(self.url, self.key)
        except ImportError:
            raise ExternalServiceError("Supabase SDK not installed")
        except Exception as exc:
            logger.error("auth.client_creation_failed", error=str(exc)[:200])
            raise ExternalServiceError("Failed to connect to authentication service")

    async def sign_in(self, email: str, password: str) -> dict[str, Any]:
        """Sign in with email/password via Supabase."""
        # Validate inputs BEFORE calling external service
        _validate_email(email)
        _validate_password(password)

        try:
            supabase = self._get_client()
            result = supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            # Defensive: verify session exists
            if not result.session:
                raise AuthenticationError("Login failed: no session returned")

            logger.info("auth.sign_in_success", email=email[:3] + "***")  # Don't log full email
            return {
                "access_token": result.session.access_token,
                "refresh_token": result.session.refresh_token,
                "expires_in": result.session.expires_in or 3600,
                "user": {
                    "id": result.user.id if result.user else "",
                    "email": result.user.email if result.user else email,
                    "tier": "free",
                },
            }
        except (AuthenticationError, ValidationError, ExternalServiceError):
            raise  # Re-raise our custom exceptions
        except Exception as exc:
            # Sanitize: never expose Supabase internals to client
            logger.warning("auth.sign_in_failed", email=email[:3] + "***", error=str(exc)[:200])
            raise AuthenticationError("Invalid email or password")

    async def sign_up(
        self, email: str, password: str, full_name: str = ""
    ) -> dict[str, Any]:
        """Register new user account."""
        _validate_email(email)
        _validate_password(password)

        # Sanitize full_name
        if full_name:
            full_name = full_name.strip()[:200]

        try:
            supabase = self._get_client()
            result = supabase.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {"data": {"full_name": full_name}},
                }
            )
            logger.info("auth.sign_up_success", email=email[:3] + "***")
            return {
                "user": {
                    "id": result.user.id if result.user else "",
                    "email": result.user.email if result.user else email,
                },
                "access_token": (
                    result.session.access_token if result.session else ""
                ),
                "refresh_token": (
                    result.session.refresh_token if result.session else ""
                ),
            }
        except (AuthenticationError, ValidationError, ExternalServiceError):
            raise
        except Exception as exc:
            logger.warning("auth.sign_up_failed", email=email[:3] + "***", error=str(exc)[:200])
            raise AuthenticationError("Registration failed. Please try again.")

    async def refresh(self, refresh_token: str) -> dict[str, Any]:
        """Refresh an expired access token."""
        if not refresh_token or not refresh_token.strip():
            raise ValidationError("Refresh token is required")

        if len(refresh_token) > 4096:
            raise ValidationError("Invalid refresh token")

        try:
            supabase = self._get_client()
            result = supabase.auth.refresh_session(refresh_token)
            if not result.session:
                raise AuthenticationError("Token refresh failed: no session returned")

            logger.info("auth.token_refreshed")
            return {
                "access_token": result.session.access_token,
                "refresh_token": result.session.refresh_token,
                "expires_in": result.session.expires_in or 3600,
            }
        except (AuthenticationError, ValidationError, ExternalServiceError):
            raise
        except Exception as exc:
            logger.warning("auth.refresh_failed", error=str(exc)[:200])
            raise AuthenticationError("Token refresh failed. Please log in again.")
