"""
Auth Router — Supabase JWT authentication.
Uses custom exception types for consistent error responses.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

try:
    import email_validator  # noqa: F401
    from pydantic import EmailStr
except ImportError:
    EmailStr = str  # type: ignore[misc,assignment]

from core.exceptions import TeamGenieError

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=200)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    user: dict


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1, max_length=4096)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login with email/password via Supabase."""
    try:
        from services.auth_service import AuthService

        auth = AuthService()
        result = await auth.sign_in(request.email, request.password)
        return result
    except TeamGenieError as exc:
        # Map custom exception → HTTP status
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.error_code, "message": exc.message},
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail={"code": "internal_error", "message": "An unexpected error occurred."},
        )


@router.post("/register", status_code=201)
async def register(request: RegisterRequest):
    """Register new user account."""
    try:
        from services.auth_service import AuthService

        auth = AuthService()
        return await auth.sign_up(request.email, request.password, request.full_name)
    except TeamGenieError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.error_code, "message": exc.message},
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail={"code": "internal_error", "message": "Registration failed."},
        )


@router.post("/refresh")
async def refresh_token(request: RefreshRequest):
    """Refresh expired access token."""
    try:
        from services.auth_service import AuthService

        auth = AuthService()
        return await auth.refresh(request.refresh_token)
    except TeamGenieError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={"code": exc.error_code, "message": exc.message},
        )
    except Exception:
        raise HTTPException(
            status_code=500,
            detail={"code": "internal_error", "message": "Token refresh failed."},
        )


@router.post("/logout")
async def logout(http_request: Request):
    """Invalidate current session by revoking the token JTI."""
    try:
        from middleware.auth import revoke_token

        jti = getattr(http_request.state, "token_jti", "")
        if jti:
            await revoke_token(jti)

        return {"message": "Successfully logged out", "token_revoked": bool(jti)}
    except Exception:
        # Logout should never fail from user perspective
        return {"message": "Successfully logged out", "token_revoked": False}


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Send password reset email via Supabase."""
    try:
        from services.auth_service import AuthService

        auth = AuthService()
        await auth.reset_password(request.email)
    except Exception:
        pass

    return {"message": "If an account exists with this email, a password reset link has been sent."}
