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
# Metrics — prometheus_client middleware + /metrics endpoint (issue #3/#9 fix)
# ---------------------------------------------------------------------------
try:
    from middleware.metrics import metrics_middleware, metrics_endpoint
    _metrics_middleware_available = True
except Exception:
    _metrics_middleware_available = False
    metrics_middleware = None  # type: ignore[assignment]
    metrics_endpoint = None  # type: ignore[assignment]

try:
    from routers import metrics as metrics_router
except ImportError:
    metrics_router = None  # type: ignore

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

# 4. Self-healing (experimental — opt-in, disabled by default)
if os.getenv("ENABLE_SELF_HEALING", "false").lower() == "true":
    from middleware.self_healing import self_healing_middleware
    app.middleware("http")(self_healing_middleware)

# 5. Auth — JWT verification
from middleware.auth import verify_jwt
app.middleware("http")(verify_jwt)

# 6. AI Firewall — block malicious payloads (opt-in, disabled by default)
if os.getenv("ENABLE_AI_FIREWALL", "false").lower() == "true":
    from security.ai_firewall import ai_firewall_check
    app.middleware("http")(ai_firewall_check)

# 7. Rate limiter
from middleware.rate_limit import rate_limit_middleware
app.middleware("http")(rate_limit_middleware)

# 8. Prometheus metrics — record every request (no-op if prometheus_client not installed)
if _metrics_middleware_available and metrics_middleware is not None:
    app.middleware("http")(metrics_middleware)


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(team.router, prefix="/api/team", tags=["Team Generation"])
app.include_router(player.router, prefix="/api/player", tags=["Player Insights"])
app.include_router(match.router, prefix="/api/match", tags=["Match Data"])
app.include_router(user.router, prefix="/api/user", tags=["User Management"])

# /metrics — prefer the prometheus_client (generate_latest) version; fall back to in-memory
if _metrics_middleware_available and metrics_endpoint is not None:
    from fastapi import APIRouter as _APIRouter
    _metrics_api_router = _APIRouter()
    _metrics_api_router.add_api_route("/metrics", metrics_endpoint, methods=["GET"], tags=["Monitoring"])
    app.include_router(_metrics_api_router)
elif metrics_router:
    app.include_router(metrics_router.router, tags=["Monitoring"])


# ---------------------------------------------------------------------------
# Health, Readiness & Diagnostics (Upgrade #3)
# ---------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "version": API_VERSION,
        "service": "teamgenie-api",
        "timestamp": time.time(),
    }


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Detailed dependency readiness check."""
    from core.settings import settings as app_settings

    checks = {
        "mode": app_settings.APP_MODE.value,
        "llm_available": app_settings.has_real_llm(),
        "database_configured": app_settings.has_real_db(),
        "vector_db_configured": app_settings.has_vector_db(),
        "redis_configured": app_settings.UPSTASH_REDIS_URL is not None,
    }
    return {
        "ready": True,  # App is always ready in DEMO mode
        "checks": checks,
        "version": API_VERSION,
        "timestamp": time.time(),
    }


@app.get("/diagnostics", tags=["Health"], include_in_schema=False)
async def diagnostics():
    """Dev-only deep introspection endpoint."""
    from core.settings import settings as app_settings
    from core.version import get_version_info

    if app_settings.APP_MODE.value == "production":
        return JSONResponse(status_code=403, content={"error": "Diagnostics disabled in production"})

    return {
        "version_info": get_version_info(),
        "mode": app_settings.APP_MODE.value,
        "middleware_stack": ["cors", "request_metadata", "error_handler", "self_healing", "auth", "ai_firewall", "rate_limit"],
        "feature_flags": {
            "ai_firewall": app_settings.ENABLE_AI_FIREWALL,
            "self_healing": app_settings.ENABLE_SELF_HEALING,
            "rag": app_settings.ENABLE_RAG,
        },
        "providers": {
            "gemini": app_settings.GEMINI_API_KEY is not None,
            "claude": app_settings.CLAUDE_API_KEY is not None,
            "pinecone": app_settings.has_vector_db(),
            "turso": app_settings.has_real_db(),
            "redis": app_settings.UPSTASH_REDIS_URL is not None,
        },
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
