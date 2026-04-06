"""
Auth Service — Supabase GoTrue REST API wrapper (zero SDK dependencies).
Uses httpx for direct HTTP calls to Supabase Auth endpoints.

This is the most reliable approach — no SDK version mismatches.
"""

from __future__ import annotations

import os
import re
from typing import Any

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from core.exceptions import AuthenticationError, ValidationError, ExternalServiceError, QuotaExceededError

_EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
_MIN_PASSWORD_LENGTH = 8
_MAX_PASSWORD_LENGTH = 128


def _validate_email(email: str) -> None:
    if not email or not email.strip():
        raise ValidationError("Email is required")
    if len(email) > 254:
        raise ValidationError("Email address is too long")
    if not _EMAIL_PATTERN.match(email):
        raise ValidationError("Invalid email format")


def _validate_password(password: str) -> None:
    if not password:
        raise ValidationError("Password is required")
    if len(password) < _MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Password must be at least {_MIN_PASSWORD_LENGTH} characters")
    if len(password) > _MAX_PASSWORD_LENGTH:
        raise ValidationError(f"Password must be at most {_MAX_PASSWORD_LENGTH} characters")


class AuthService:
    """Supabase Auth via direct REST API calls (httpx)."""

    def __init__(self):
        self.url = os.getenv("SUPABASE_URL", "").rstrip("/")
        self.key = os.getenv("SUPABASE_ANON_KEY", "")
        self.service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

        if not self.url or not self.key:
            logger.warning("auth.missing_config", has_url=bool(self.url), has_key=bool(self.key))

    def _headers(self, use_service_role: bool = False) -> dict:
        """Build Supabase Auth API headers."""
        key = self.service_key if (use_service_role and self.service_key) else self.key
        return {
            "apikey": self.key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        }

    def _auth_url(self, path: str) -> str:
        return f"{self.url}/auth/v1/{path}"

    def _ensure_configured(self):
        if not self.url or not self.key:
            raise ExternalServiceError("Authentication service not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY.")
        if httpx is None:
            raise ExternalServiceError("httpx package not installed. Run: pip install httpx")

    async def sign_in(self, email: str, password: str) -> dict[str, Any]:
        """Sign in with email/password via Supabase GoTrue REST API."""
        _validate_email(email)
        _validate_password(password)
        self._ensure_configured()

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    self._auth_url("token?grant_type=password"),
                    headers=self._headers(),
                    json={"email": email, "password": password},
                )

            data = resp.json()

            if resp.status_code != 200:
                msg = data.get("error_description") or data.get("msg") or data.get("message", "Login failed")
                logger.warning("auth.sign_in_failed", email=email[:3] + "***", error=msg)

                if "invalid" in msg.lower() or "credentials" in msg.lower():
                    raise AuthenticationError("Invalid email or password.")
                elif "not confirmed" in msg.lower():
                    raise AuthenticationError("Please confirm your email before signing in. Check your inbox.")
                elif "rate" in msg.lower():
                    raise QuotaExceededError("Too many login attempts. Please wait a minute and try again.")
                else:
                    raise AuthenticationError(msg)

            logger.info("auth.sign_in_success", email=email[:3] + "***")
            user = data.get("user", {})
            return {
                "access_token": data.get("access_token", ""),
                "refresh_token": data.get("refresh_token", ""),
                "expires_in": data.get("expires_in", 3600),
                "user": {
                    "id": user.get("id", ""),
                    "email": user.get("email", email),
                    "full_name": user.get("user_metadata", {}).get("full_name", ""),
                    "tier": "free",
                },
            }
        except (AuthenticationError, ValidationError, ExternalServiceError, QuotaExceededError):
            raise
        except Exception as exc:
            logger.warning("auth.sign_in_error", error=str(exc)[:200])
            raise AuthenticationError("Login failed. Please try again.")

    async def sign_up(self, email: str, password: str, full_name: str = "") -> dict[str, Any]:
        """Register new user via Supabase Admin API (auto-confirms, bypasses rate limits)."""
        _validate_email(email)
        _validate_password(password)
        self._ensure_configured()

        if full_name:
            full_name = full_name.strip()[:200]

        try:
            # Use Admin API if service role key is available (bypasses email rate limits)
            if self.service_key:
                return await self._admin_sign_up(email, password, full_name)
            else:
                return await self._regular_sign_up(email, password, full_name)
        except (AuthenticationError, ValidationError, ExternalServiceError, QuotaExceededError):
            raise
        except Exception as exc:
            logger.warning("auth.sign_up_error", error=str(exc)[:200])
            raise AuthenticationError("Registration failed. Please try again.")

    async def _admin_sign_up(self, email: str, password: str, full_name: str) -> dict[str, Any]:
        """Create user via Supabase Admin API (service role key). Auto-confirms email."""
        async with httpx.AsyncClient(timeout=15) as client:
            # Step 1: Create user via admin endpoint
            resp = await client.post(
                self._auth_url("admin/users"),
                headers=self._headers(use_service_role=True),
                json={
                    "email": email,
                    "password": password,
                    "email_confirm": True,
                    "user_metadata": {"full_name": full_name},
                },
            )

        data = resp.json()

        if resp.status_code == 422:
            msg = data.get("msg", "")
            if "already" in msg.lower():
                raise AuthenticationError("An account with this email already exists. Try signing in.")
            raise AuthenticationError(msg or "Invalid registration data.")

        if resp.status_code == 429:
            raise QuotaExceededError("Too many signup attempts. Please wait and try again.")

        if resp.status_code not in (200, 201):
            msg = data.get("msg") or data.get("message", "Registration failed")
            logger.warning("auth.admin_sign_up_failed", email=email[:3] + "***", error=msg)
            raise AuthenticationError(msg)

        user_id = data.get("id", "")
        logger.info("auth.admin_sign_up_success", email=email[:3] + "***", user_id=user_id[:8])

        # Step 2: Auto sign-in to get tokens
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                sign_in_resp = await client.post(
                    self._auth_url("token?grant_type=password"),
                    headers=self._headers(),
                    json={"email": email, "password": password},
                )
            si_data = sign_in_resp.json()
            if sign_in_resp.status_code == 200:
                return {
                    "message": "Account created successfully!",
                    "email_confirmation_required": False,
                    "user": {"id": user_id, "email": email, "full_name": full_name},
                    "access_token": si_data.get("access_token", ""),
                    "refresh_token": si_data.get("refresh_token", ""),
                }
        except Exception:
            pass  # Token retrieval failed, but user is created

        return {
            "message": "Account created successfully!",
            "email_confirmation_required": False,
            "user": {"id": user_id, "email": email, "full_name": full_name},
            "access_token": "",
            "refresh_token": "",
        }

    async def _regular_sign_up(self, email: str, password: str, full_name: str) -> dict[str, Any]:
        """Create user via regular Supabase signup (may require email confirmation)."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                self._auth_url("signup"),
                headers=self._headers(),
                json={
                    "email": email,
                    "password": password,
                    "data": {"full_name": full_name},
                },
            )

        data = resp.json()

        if resp.status_code not in (200, 201):
            msg = data.get("error_description") or data.get("msg") or data.get("message", "Registration failed")
            logger.warning("auth.sign_up_failed", email=email[:3] + "***", error=msg)

            if "already registered" in msg.lower() or "already been registered" in msg.lower():
                raise AuthenticationError("An account with this email already exists. Try signing in.")
            elif "rate" in msg.lower():
                raise QuotaExceededError("Too many signup attempts. Please wait a few minutes and try again.")
            elif "password" in msg.lower():
                raise AuthenticationError("Password is too weak. Use at least 8 characters.")
            else:
                raise AuthenticationError(msg)

        user = data.get("user", data)
        identities = user.get("identities", [])

        if isinstance(identities, list) and len(identities) == 0:
            raise AuthenticationError("An account with this email already exists. Try signing in.")

        logger.info("auth.sign_up_success", email=email[:3] + "***")
        return {
            "message": "Account created successfully!",
            "email_confirmation_required": not bool(data.get("access_token")),
            "user": {"id": user.get("id", ""), "email": user.get("email", email)},
            "access_token": data.get("access_token", ""),
            "refresh_token": data.get("refresh_token", ""),
        }

    async def refresh(self, refresh_token: str) -> dict[str, Any]:
        """Refresh an expired access token."""
        if not refresh_token or not refresh_token.strip():
            raise ValidationError("Refresh token is required")
        if len(refresh_token) > 4096:
            raise ValidationError("Invalid refresh token")
        self._ensure_configured()

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    self._auth_url("token?grant_type=refresh_token"),
                    headers=self._headers(),
                    json={"refresh_token": refresh_token},
                )

            data = resp.json()

            if resp.status_code != 200:
                msg = data.get("error_description") or data.get("msg", "Token refresh failed")
                raise AuthenticationError("Session expired. Please log in again.")

            logger.info("auth.token_refreshed")
            return {
                "access_token": data.get("access_token", ""),
                "refresh_token": data.get("refresh_token", ""),
                "expires_in": data.get("expires_in", 3600),
            }
        except (AuthenticationError, ValidationError, ExternalServiceError, QuotaExceededError):
            raise
        except Exception as exc:
            logger.warning("auth.refresh_error", error=str(exc)[:200])
            raise AuthenticationError("Token refresh failed. Please log in again.")

    async def reset_password(self, email: str) -> None:
        """Send password reset email. Never reveals whether email exists."""
        _validate_email(email)
        self._ensure_configured()

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(
                    self._auth_url("recover"),
                    headers=self._headers(),
                    json={"email": email},
                )
            if resp.status_code == 200:
                logger.info("auth.password_reset_sent", email=email[:3] + "***")
            else:
                data = resp.json()
                logger.warning("auth.password_reset_issue", status=resp.status_code,
                               error=str(data)[:200])
        except Exception as exc:
            logger.warning("auth.password_reset_error", error=str(exc)[:200])
