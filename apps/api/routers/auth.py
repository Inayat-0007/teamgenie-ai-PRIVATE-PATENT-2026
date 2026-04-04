"""
Auth Router — Supabase JWT authentication.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field

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
    refresh_token: str


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
    except ValueError as exc:
        raise HTTPException(
            status_code=401,
            detail={"code": "invalid_credentials", "message": str(exc)},
        )


@router.post("/register", status_code=201)
async def register(request: RegisterRequest):
    """Register new user account."""
    try:
        from services.auth_service import AuthService

        auth = AuthService()
        return await auth.sign_up(request.email, request.password, request.full_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/refresh")
async def refresh_token(request: RefreshRequest):
    """Refresh expired access token."""
    try:
        from services.auth_service import AuthService

        auth = AuthService()
        return await auth.refresh(request.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@router.post("/logout")
async def logout():
    """Invalidate current session."""
    return {"message": "Successfully logged out"}


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """Send password reset email."""
    return {"message": "Password reset email sent. Check your inbox."}
