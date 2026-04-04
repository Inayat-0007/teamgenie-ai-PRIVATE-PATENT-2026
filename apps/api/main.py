"""
TeamGenie AI — FastAPI Backend
Production-grade async API with self-healing middleware.
"""

from __future__ import annotations

import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Final

# Load .env EARLY so all os.getenv() calls in middleware/services see the values
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# --- Structured logging (graceful fallback) ---
try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

# --- Sentry (optional) ---
_sentry_dsn = os.getenv("SENTRY_DSN")
try:
    import sentry_sdk
    if _sentry_dsn:
        sentry_sdk.init(
            dsn=_sentry_dsn,
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            environment=os.getenv("SENTRY_ENVIRONMENT", "development"),
        )
except ImportError:
    sentry_sdk = None  # type: ignore[assignment]

from routers import auth, match, player, team, user

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
API_VERSION: Final[str] = "1.0.0"
IS_DEV = os.getenv("PYTHON_ENV", "development") != "production"


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown hooks
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    logger.info("api.starting", version=API_VERSION) if hasattr(logger, 'info') else None

    # Startup — warm connections (graceful)
    try:
        from services.cache_service import CacheService
        cache = CacheService()
        await cache.connect()
        app.state.cache = cache
    except Exception as exc:
        logger.warning("redis.connect_failed", error=str(exc)) if hasattr(logger, 'warning') else None
        app.state.cache = None

    yield

    # Shutdown
    if hasattr(app.state, "cache") and app.state.cache:
        try:
            await app.state.cache.disconnect()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# App instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title="TeamGenie AI API",
    description="AI-powered fantasy sports intelligence platform",
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Middleware stack (execution order is bottom → top)
# ---------------------------------------------------------------------------

# 1. CORS — outermost
_allowed_origins = os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:3000"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _allowed_origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 2. Request ID + timing (decorates every response)
@app.middleware("http")
async def add_request_metadata(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start = time.perf_counter()

    response = await call_next(request)

    duration_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration_ms:.0f}ms"

    return response


# 3. Error handler
from middleware.error_handler import error_handler_middleware
app.middleware("http")(error_handler_middleware)

# 4. Self-healing (experimental — can be disabled)
if os.getenv("ENABLE_SELF_HEALING", "true").lower() == "true":
    from middleware.self_healing import self_healing_middleware
    app.middleware("http")(self_healing_middleware)

# 5. Auth — JWT verification
from middleware.auth import verify_jwt
app.middleware("http")(verify_jwt)

# 6. AI Firewall — block malicious payloads (can be disabled)
if os.getenv("ENABLE_AI_FIREWALL", "true").lower() == "true":
    from security.ai_firewall import ai_firewall_check
    app.middleware("http")(ai_firewall_check)

# 7. Rate limiter
from middleware.rate_limit import rate_limit_middleware
app.middleware("http")(rate_limit_middleware)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(team.router, prefix="/api/team", tags=["Team Generation"])
app.include_router(player.router, prefix="/api/player", tags=["Player Insights"])
app.include_router(match.router, prefix="/api/match", tags=["Match Data"])
app.include_router(user.router, prefix="/api/user", tags=["User Management"])


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "version": API_VERSION,
        "service": "teamgenie-api",
        "timestamp": time.time(),
    }


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if sentry_sdk and _sentry_dsn:
        sentry_sdk.capture_exception(exc)

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_server_error",
                "message": "An unexpected error occurred. Our team has been notified.",
                "request_id": getattr(request.state, "request_id", "unknown"),
            }
        },
    )
