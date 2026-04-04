"""
Auth Middleware — Supabase JWT verification.
Validates Bearer token on protected routes.
"""

from __future__ import annotations

import os
import time

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from fastapi import Request, HTTPException

try:
    from jose import jwt, JWTError
except ImportError:
    jwt = None  # type: ignore[assignment]
    JWTError = Exception  # type: ignore[misc,assignment]

# Public routes that bypass authentication
PUBLIC_ROUTES: frozenset[str] = frozenset({
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/auth/login",
    "/api/auth/register",
    "/api/auth/forgot-password",
})


async def verify_jwt(request: Request, call_next):
    """Verify Supabase JWT token from Authorization header."""
    # Skip public routes and CORS preflight
    if request.url.path in PUBLIC_ROUTES or request.method == "OPTIONS":
        return await call_next(request)

    auth_header = request.headers.get("Authorization")

    if not auth_header or not auth_header.startswith("Bearer "):
        # Allow unauthenticated access in development/test mode
        if os.getenv("PYTHON_ENV") in ("development", "test"):
            request.state.user_id = "dev_user"
            request.state.user_role = "authenticated"
            request.state.user_tier = "free"
            return await call_next(request)
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = auth_header.split(" ", maxsplit=1)[1]

    try:
        secret = os.getenv("SUPABASE_JWT_SECRET")
        if not secret:
            raise HTTPException(status_code=500, detail="JWT secret not configured")

        algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        payload = jwt.decode(token, secret, algorithms=[algorithm])

        # Expiry check (belt-and-suspenders; jose does this but we log it)
        exp = payload.get("exp", 0)
        if exp < time.time():
            logger.info("auth.token_expired", sub=payload.get("sub"))
            raise HTTPException(status_code=401, detail="Token expired")

        request.state.user_id = payload.get("sub", "")
        request.state.user_role = payload.get("role", "authenticated")
        request.state.user_tier = payload.get("user_metadata", {}).get("tier", "free")

    except JWTError as exc:
        logger.warning("auth.invalid_token", error=str(exc))
        raise HTTPException(status_code=401, detail="Invalid token")

    return await call_next(request)
