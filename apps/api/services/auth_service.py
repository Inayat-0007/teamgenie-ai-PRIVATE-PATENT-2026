"""
Auth Service — Supabase authentication wrapper.
Singleton-style service for sign-in, sign-up, and token refresh.
"""

from __future__ import annotations

import os
from typing import Any

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


class AuthService:
    """Supabase authentication service with structured error handling."""

    def __init__(self):
        self.url = os.getenv("SUPABASE_URL", "")
        self.key = os.getenv("SUPABASE_ANON_KEY", "")

        if not self.url or not self.key:
            logger.warning("auth.missing_config", has_url=bool(self.url), has_key=bool(self.key))

    def _get_client(self):
        """Lazily create a Supabase client."""
        from supabase import create_client
        return create_client(self.url, self.key)

    async def sign_in(self, email: str, password: str) -> dict[str, Any]:
        """Sign in with email/password via Supabase."""
        try:
            supabase = self._get_client()
            result = supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            logger.info("auth.sign_in_success", email=email)
            return {
                "access_token": result.session.access_token,
                "refresh_token": result.session.refresh_token,
                "expires_in": result.session.expires_in or 3600,
                "user": {
                    "id": result.user.id,
                    "email": result.user.email,
                    "tier": "free",
                },
            }
        except Exception as exc:
            logger.warning("auth.sign_in_failed", email=email, error=str(exc))
            raise ValueError(f"Login failed: {exc}")

    async def sign_up(
        self, email: str, password: str, full_name: str = ""
    ) -> dict[str, Any]:
        """Register new user account."""
        try:
            supabase = self._get_client()
            result = supabase.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {"data": {"full_name": full_name}},
                }
            )
            logger.info("auth.sign_up_success", email=email)
            return {
                "user": {
                    "id": result.user.id,
                    "email": result.user.email,
                },
                "access_token": (
                    result.session.access_token if result.session else ""
                ),
                "refresh_token": (
                    result.session.refresh_token if result.session else ""
                ),
            }
        except Exception as exc:
            logger.warning("auth.sign_up_failed", email=email, error=str(exc))
            raise ValueError(f"Registration failed: {exc}")

    async def refresh(self, refresh_token: str) -> dict[str, Any]:
        """Refresh an expired access token."""
        try:
            supabase = self._get_client()
            result = supabase.auth.refresh_session(refresh_token)
            logger.info("auth.token_refreshed")
            return {
                "access_token": result.session.access_token,
                "refresh_token": result.session.refresh_token,
                "expires_in": result.session.expires_in or 3600,
            }
        except Exception as exc:
            logger.warning("auth.refresh_failed", error=str(exc))
            raise ValueError(f"Token refresh failed: {exc}")
