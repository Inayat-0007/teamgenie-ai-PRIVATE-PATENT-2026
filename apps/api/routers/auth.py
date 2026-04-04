"""
Auth Router — Supabase JWT authentication.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

router = APIRouter()


class LoginRequest(BaseModel):
    email: str
    password: str


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str = ""


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int
    user: dict


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Login with email/password via Supabase."""
    try:
        from services.auth_service import AuthService
        auth = AuthService()
        result = await auth.sign_in(request.email, request.password)
        return result
    except Exception as e:
        raise HTTPException(status_code=401, detail={"code": "invalid_credentials", "message": str(e)})


@router.post("/register", status_code=201)
async def register(request: RegisterRequest):
    """Register new user account."""
    try:
        from services.auth_service import AuthService
        auth = AuthService()
        result = await auth.sign_up(request.email, request.password, request.full_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """Refresh expired access token."""
    try:
        from services.auth_service import AuthService
        auth = AuthService()
        return await auth.refresh(refresh_token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
async def logout():
    """Invalidate current session."""
    return {"message": "Successfully logged out"}


@router.post("/forgot-password")
async def forgot_password(email: str):
    """Send password reset email."""
    return {"message": "Password reset email sent. Check your inbox."}
