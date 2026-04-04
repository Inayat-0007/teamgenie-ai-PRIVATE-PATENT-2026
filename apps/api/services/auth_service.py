"""
Auth Service — Supabase authentication wrapper.
"""

import os


class AuthService:
    """Supabase authentication service."""

    def __init__(self):
        self.url = os.getenv("SUPABASE_URL", "")
        self.key = os.getenv("SUPABASE_ANON_KEY", "")

    async def sign_in(self, email: str, password: str) -> dict:
        """Sign in with email/password."""
        try:
            from supabase import create_client
            supabase = create_client(self.url, self.key)
            result = supabase.auth.sign_in_with_password({"email": email, "password": password})
            return {
                "access_token": result.session.access_token,
                "refresh_token": result.session.refresh_token,
                "expires_in": 3600,
                "user": {"id": result.user.id, "email": result.user.email, "tier": "free"},
            }
        except Exception as e:
            raise ValueError(f"Login failed: {str(e)}")

    async def sign_up(self, email: str, password: str, full_name: str = "") -> dict:
        """Register new user."""
        try:
            from supabase import create_client
            supabase = create_client(self.url, self.key)
            result = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {"data": {"full_name": full_name}},
            })
            return {
                "user": {"id": result.user.id, "email": result.user.email},
                "access_token": result.session.access_token if result.session else "",
                "refresh_token": result.session.refresh_token if result.session else "",
            }
        except Exception as e:
            raise ValueError(f"Registration failed: {str(e)}")

    async def refresh(self, refresh_token: str) -> dict:
        """Refresh access token."""
        try:
            from supabase import create_client
            supabase = create_client(self.url, self.key)
            result = supabase.auth.refresh_session(refresh_token)
            return {
                "access_token": result.session.access_token,
                "refresh_token": result.session.refresh_token,
                "expires_in": 3600,
            }
        except Exception as e:
            raise ValueError(f"Token refresh failed: {str(e)}")
