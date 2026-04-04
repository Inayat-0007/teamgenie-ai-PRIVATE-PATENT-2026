"""
Auth Middleware — Supabase JWT verification.
Validates Bearer token on protected routes.
"""

from fastapi import Request, HTTPException
from jose import jwt, JWTError
import os
import time

# Public routes that don't require auth
PUBLIC_ROUTES = {"/health", "/docs", "/redoc", "/openapi.json", "/api/auth/login", "/api/auth/register", "/api/auth/forgot-password"}


async def verify_jwt(request: Request, call_next):
    """Verify Supabase JWT token."""
    if request.url.path in PUBLIC_ROUTES or request.method == "OPTIONS":
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        # Allow unauthenticated access in development
        if os.getenv("PYTHON_ENV") == "development":
            request.state.user_id = "dev_user"
            return await call_next(request)
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = auth_header.split(" ")[1]

    try:
        secret = os.getenv("SUPABASE_JWT_SECRET", "dev-secret")
        payload = jwt.decode(token, secret, algorithms=["HS256"])

        if payload.get("exp", 0) < time.time():
            raise HTTPException(status_code=401, detail="Token expired")

        request.state.user_id = payload.get("sub", "")
        request.state.user_role = payload.get("role", "authenticated")

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    return await call_next(request)
