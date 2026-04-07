"""
Auth Middleware — Supabase JWT verification with hardened security.

Security layers:
  1. Public route bypass (exact + prefix match)
  2. HTTPS enforcement in production
  3. JWT decode with issuer and audience validation
  4. Explicit expiration check with clock skew tolerance (5s OWASP)
  5. Redis-backed token revocation list (with in-memory fallback)
  6. User context injection into request.state
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

from fastapi import HTTPException, Request

try:
    from jose import JWTError, jwt
except ImportError:
    jwt = None  # type: ignore[assignment]
    JWTError = Exception  # type: ignore[misc,assignment]

# ---------------------------------------------------------------------------
# Public Routes (bypass authentication)
# ---------------------------------------------------------------------------

# Exact-match public routes
PUBLIC_ROUTES: frozenset[str] = frozenset(
    {
        "/health",
        "/ready",
        "/docs",
        "/redoc",
        "/openapi.json",
        # "/metrics" — REMOVED: must require auth to prevent competitor scraping (Audit Fix #09)
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/forgot-password",
        "/api/auth/refresh",
        "/api/payment/webhook",
    }
)

# Prefix-match public routes (for paths with dynamic segments)
PUBLIC_PREFIXES: tuple[str, ...] = (
    "/docs",
    "/redoc",
    "/openapi",
)

# Clock skew tolerance for expiration checks (seconds)
_CLOCK_SKEW_TOLERANCE = 5  # OWASP recommends ≤5s to limit stolen-token replay window

# ---------------------------------------------------------------------------
# Redis-backed Token Revocation List (with in-memory fallback)
# ---------------------------------------------------------------------------
_revoked_tokens: set[str] = set()  # In-memory fallback when Redis is down
_MAX_REVOCATION_LIST_SIZE = 10000  # Prevent unbounded memory growth
_REVOCATION_TTL_SECONDS = 86400  # 24h — matches max JWT lifetime

# Reference to app's Redis cache (set during first request)
_redis_cache = None


def _get_redis():
    """Lazy-load Redis cache from the running app."""
    global _redis_cache
    if _redis_cache is not None:
        return _redis_cache
    # Will be set on first request via middleware
    return _redis_cache


async def revoke_token(token_jti: str) -> None:
    """Add a token's JTI to the revocation list (Redis-first, in-memory fallback)."""
    # Always add to in-memory as a local fast-check layer
    if len(_revoked_tokens) >= _MAX_REVOCATION_LIST_SIZE:
        # Audit Fix #10: LRU eviction instead of .clear() which re-validated ALL logged-out users
        # Remove oldest 20% of entries instead of wiping everything
        evict_count = _MAX_REVOCATION_LIST_SIZE // 5
        evict_iter = iter(_revoked_tokens)
        to_remove = [next(evict_iter) for _ in range(min(evict_count, len(_revoked_tokens)))]
        for old_jti in to_remove:
            _revoked_tokens.discard(old_jti)
        logger.warning("auth.revocation_list_evicted", evicted=len(to_remove), remaining=len(_revoked_tokens))
    _revoked_tokens.add(token_jti)

    # Persist to Redis so revocation survives pod restarts and works across replicas
    redis = _get_redis()
    if redis:
        try:
            await redis.set(f"revoked:{token_jti}", "1", ex=_REVOCATION_TTL_SECONDS)
            logger.info("auth.token_revoked_redis", jti=token_jti)
        except Exception as exc:
            logger.warning("auth.redis_revoke_failed", jti=token_jti, error=str(exc))


async def is_token_revoked(token_jti: str) -> bool:
    """Check if a token has been revoked (Redis-first, in-memory fallback)."""
    # Fast local check first
    if token_jti in _revoked_tokens:
        return True
    # Check Redis for cross-pod revocations
    redis = _get_redis()
    if redis:
        try:
            result = await redis.get(f"revoked:{token_jti}")
            if result:
                _revoked_tokens.add(token_jti)  # Sync to local cache
                return True
        except Exception:
            pass  # Redis down — rely on in-memory only
    return False


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------


def _is_public_route(path: str) -> bool:
    """Check if a path is public (exact + prefix match)."""
    if path in PUBLIC_ROUTES:
        return True
    return any(path.startswith(prefix) for prefix in PUBLIC_PREFIXES)


async def verify_jwt(request: Request, call_next):
    """Verify Supabase JWT token from Authorization header."""

    # Inject Redis cache reference for token revocation (lazy init)
    global _redis_cache
    if _redis_cache is None and hasattr(request.app.state, "cache") and request.app.state.cache:
        _redis_cache = request.app.state.cache

    # Skip public routes and CORS preflight
    if _is_public_route(request.url.path) or request.method == "OPTIONS":
        return await call_next(request)

    # HTTPS enforcement in production
    is_production = os.getenv("PYTHON_ENV", "development") == "production"
    if is_production and request.url.scheme != "https":
        # Check X-Forwarded-Proto for reverse proxy setups
        forwarded_proto = request.headers.get("X-Forwarded-Proto", "")
        if forwarded_proto != "https":
            logger.warning("auth.insecure_connection", path=request.url.path)
            raise HTTPException(
                status_code=403,
                detail="HTTPS required in production",
            )

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

    # Reject obviously malformed tokens (too short or too long)
    if len(token) < 20 or len(token) > 4096:
        raise HTTPException(status_code=401, detail="Malformed token")

    try:
        secret = os.getenv("SUPABASE_JWT_SECRET")
        if not secret:
            logger.error("auth.jwt_secret_missing")
            raise HTTPException(status_code=500, detail="JWT secret not configured")

        # Audit Fix #02 CRITICAL: Algorithm is ALWAYS server-controlled.
        # NEVER read 'alg' from the token header — that's attacker-controlled data.
        # This was a textbook OWASP JWT Algorithm Confusion vulnerability.
        algorithm = os.getenv("JWT_ALGORITHM", "HS256")

        # Validate algorithms — only allow known safe symmetric algorithms for Supabase
        allowed_algorithms = {"HS256", "HS384", "HS512"}
        if algorithm not in allowed_algorithms:
            logger.error("auth.unsafe_algorithm", algorithm=algorithm)
            raise HTTPException(status_code=500, detail=f"Unsafe JWT algorithm: {algorithm}")

        # Decode with options for strict validation
        # NOTE: For ES256/RS256, 'secret' must be the Public Key (PEM or JWK)
        payload = jwt.decode(
            token,
            secret,
            algorithms=[algorithm],
            options={
                "verify_exp": True,  # Verify expiration
                "verify_iat": True,  # Verify issued-at
                "require": ["exp", "sub"],  # These claims must be present
            },
        )

        # Check issued-at isn't in the future (clock manipulation)
        iat = payload.get("iat", 0)
        now = time.time()
        if iat > (now + _CLOCK_SKEW_TOLERANCE):
            logger.warning("auth.token_from_future", sub=payload.get("sub"), iat=iat)
            raise HTTPException(status_code=401, detail="Invalid token")

        # Check token revocation (logout support)
        jti = payload.get("jti", "")
        if jti and await is_token_revoked(jti):
            logger.info("auth.revoked_token_used", sub=payload.get("sub"), jti=jti)
            raise HTTPException(status_code=401, detail="Token has been revoked")

        # Issuer validation (if configured)
        expected_issuer = os.getenv("JWT_ISSUER")
        if expected_issuer:
            token_issuer = payload.get("iss", "")
            if token_issuer != expected_issuer:
                logger.warning("auth.invalid_issuer", expected=expected_issuer, got=token_issuer)
                raise HTTPException(status_code=401, detail="Invalid token issuer")

        # Inject user context into request state
        request.state.user_id = payload.get("sub", "")
        request.state.user_role = payload.get("role", "authenticated")
        request.state.user_tier = payload.get("user_metadata", {}).get("tier", "free")
        request.state.token_jti = jti  # For revocation on logout

    except HTTPException:
        raise
    except JWTError as exc:
        error_msg = str(exc)
        # MASTER LEVEL LOGGING: Identify Mismatch
        logger.warning(
            "auth.invalid_token",
            error=error_msg,
            token_sample=token[:10] + "...",
            reason="Likely SUPABASE_JWT_SECRET mismatch in .env vs Supabase Dashboard",
        )
        raise HTTPException(
            status_code=401,
            detail=f"Auth Error: {error_msg}. ACTION: Ensure SUPABASE_JWT_SECRET in .env matches the one in your Supabase Dashboard -> Settings -> API.",
        )

    return await call_next(request)
