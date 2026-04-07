"""
TeamGenie AI — FastAPI Backend
Production-grade async API with self-healing middleware.
"""

from __future__ import annotations

import asyncio
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

# --- Sentry (optional — explicit import guard with warning) ---
_sentry_dsn = os.getenv("SENTRY_DSN")
_sentry_available = False
try:
    import sentry_sdk
    _sentry_available = True
    if _sentry_dsn:
        sentry_sdk.init(
            dsn=_sentry_dsn,
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            environment=os.getenv("SENTRY_ENVIRONMENT", "development"),
        )
        logger.info("sentry.initialized", environment=os.getenv("SENTRY_ENVIRONMENT", "development"))
    else:
        logger.info("sentry.skipped", reason="SENTRY_DSN not set")
except ImportError:
    sentry_sdk = None  # type: ignore[assignment]
    logger.warning("sentry.unavailable", reason="sentry_sdk package not installed — error tracking disabled")

from routers import auth, match, player, team, user, payment

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

    # ── Security Fix 1.3: Block DEMO mode in production ──
    if not IS_DEV and os.getenv("APP_MODE", "").upper() == "DEMO":
        logger.critical(
            "FATAL: APP_MODE=DEMO is not allowed when PYTHON_ENV=production. "
            "This would serve fake/hallucinated data to real users. "
            "Set APP_MODE=production or APP_MODE=hybrid to start."
        )
        raise RuntimeError("APP_MODE=DEMO is forbidden in production environment")

    # Startup — warm connections (graceful)
    try:
        from services.cache_service import CacheService
        cache = CacheService()
        await cache.connect()
        app.state.cache = cache
    except Exception as exc:
        logger.warning("redis.connect_failed", error=str(exc)) if hasattr(logger, 'warning') else None
        app.state.cache = None

    # Startup — Intelligence Harvester background scheduler (Agent 0)
    # Runs every 30 minutes: scrapes live data → Turso DB + Redis → WebSocket
    try:
        from workers.harvester import start_background_harvester
        await start_background_harvester(interval_minutes=30)
        logger.info("harvester.background_scheduled", interval_min=30)
    except Exception as exc:
        logger.warning("harvester.startup_failed", error=str(exc))

    yield

    # Shutdown — stop harvester
    try:
        from workers.harvester import stop_background_harvester
        await stop_background_harvester()
    except Exception:
        pass

    # Shutdown — close Redis
    if hasattr(app.state, "cache") and app.state.cache:
        try:
            await app.state.cache.disconnect()
        except Exception:
            pass


# ---------------------------------------------------------------------------
# App instance — Disable docs/redoc in production
# ---------------------------------------------------------------------------
app = FastAPI(
    title="TeamGenie AI API",
    description="AI-powered fantasy sports intelligence platform",
    version=API_VERSION,
    docs_url="/docs" if IS_DEV else None,
    redoc_url="/redoc" if IS_DEV else None,
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Middleware stack — CRITICAL: FastAPI executes in REVERSE registration order
# (LIFO). The LAST middleware added is the FIRST to execute on incoming
# requests.  The correct EXECUTION order we want is:
#
#   REQUEST →
#     1. Prometheus Metrics (outermost — times everything)
#     2. Rate Limiter (block abuse before expensive work)
#     3. AI Firewall (drop malicious payloads before auth)
#     4. Auth / JWT (verify identity)
#     5. Self-Healing (catch + diagnose errors from downstream)
#     6. Error Handler (normalize exceptions to clean JSON)
#     7. Request Metadata + Security Headers (inject UUID + timing + CSP)
#     8. CORS (innermost class-based middleware)
#   → ROUTER
#
# Therefore we REGISTER them in REVERSE of the above (bottom-to-top):
# ---------------------------------------------------------------------------

# CORS will be registered at the very end to be the outermost middleware


# ── 7. Request ID + timing + security headers (decorates every response) ──
@app.middleware("http")
async def add_request_metadata(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start = time.perf_counter()

    response = await call_next(request)

    duration_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration_ms:.0f}ms"

    # Security headers (defense-in-depth)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if not IS_DEV:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"

    return response


# ── 6. Error handler (catch-all for unhandled exceptions → clean JSON) ──
from middleware.error_handler import error_handler_middleware
app.middleware("http")(error_handler_middleware)

# ── 5. Self-healing (experimental — opt-in, disabled by default) ──
if os.getenv("ENABLE_SELF_HEALING", "false").lower() == "true":
    from middleware.self_healing import self_healing_middleware
    app.middleware("http")(self_healing_middleware)

# ── 4. Auth — JWT verification (AFTER error handler so auth failures → clean JSON) ──
from middleware.auth import verify_jwt
app.middleware("http")(verify_jwt)

# ── 3. AI Firewall — block malicious payloads BEFORE auth (opt-in) ──
if os.getenv("ENABLE_AI_FIREWALL", "false").lower() == "true":
    from security.ai_firewall import ai_firewall_check
    app.middleware("http")(ai_firewall_check)

# ── 2. Rate limiter (block abuse before expensive JWT verify) ──
from middleware.rate_limit import rate_limit_middleware
app.middleware("http")(rate_limit_middleware)

# ── 1. Prometheus metrics — outermost, times everything (no-op if not installed) ──
if _metrics_middleware_available and metrics_middleware is not None:
    app.middleware("http")(metrics_middleware)

# ── 0. CORS (registered last = executes first / outermost) ──
# This MUST be the outermost middleware so it can attach headers to ALL responses,
# including early error returns from the firewall, rate limiter, or error handler.
_allowed_origins = os.getenv(
    "CORS_ORIGINS", os.getenv("ALLOWED_ORIGINS", "http://localhost:3000")
).split(",")

# ── Security Fix 1.5: Block wildcard CORS in production ──
if not IS_DEV and "*" in [o.strip() for o in _allowed_origins]:
    logger.critical(
        "FATAL: CORS_ORIGINS=* is not allowed in production. "
        "This disables all cross-origin protection. "
        "Set CORS_ORIGINS to your specific frontend domains."
    )
    raise RuntimeError("CORS_ORIGINS=* is forbidden in production environment")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _allowed_origins],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID", "X-Response-Time", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
)




# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(team.router, prefix="/api/team", tags=["Team Generation"])
app.include_router(player.router, prefix="/api/player", tags=["Player Insights"])
app.include_router(match.router, prefix="/api/match", tags=["Match Data"])
app.include_router(user.router, prefix="/api/user", tags=["User Management"])
app.include_router(payment.router, prefix="/api/payment", tags=["Payments"])

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
async def health_check(request: Request):
    """Real health check — verifies critical dependencies are reachable.
    
    Audit Fix: Previously returned 200 unconditionally even when
    Turso and Redis were both down. K8s had no idea the pod was broken.
    """
    checks = {}
    overall_healthy = True

    # Check Turso DB (500ms timeout)
    try:
        from db.connection import execute_query
        await asyncio.wait_for(
            execute_query("SELECT 1"),
            timeout=0.5,
        )
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "degraded"
        # DB being down degrades but doesn't kill the pod (demo mode still works)

    # Check Redis cache (500ms timeout)
    try:
        cache = getattr(request.app.state, "cache", None)
        if cache and hasattr(cache, "ping"):
            await asyncio.wait_for(cache.ping(), timeout=0.5)
            checks["cache"] = "ok"
        else:
            checks["cache"] = "not_configured"
    except Exception:
        checks["cache"] = "degraded"

    return {
        "status": "healthy" if overall_healthy else "degraded",
        "version": API_VERSION,
        "service": "teamgenie-api",
        "timestamp": time.time(),
        "checks": checks,
    }


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Dependency readiness check. Sanitized in production."""
    from core.settings import settings as app_settings

    if IS_DEV:
        # Development: show full infrastructure status
        checks = {
            "mode": app_settings.APP_MODE.value,
            "llm_available": app_settings.has_real_llm(),
            "database_configured": app_settings.has_real_db(),
            "vector_db_configured": app_settings.has_vector_db(),
            "redis_configured": app_settings.UPSTASH_REDIS_URL is not None,
            "sentry_configured": _sentry_available and bool(_sentry_dsn),
        }
    else:
        # Production: minimal response — no infrastructure details
        checks = {
            "mode": "production",
        }

    return {
        "ready": True,
        "checks": checks,
        "version": API_VERSION,
        "timestamp": time.time(),
    }


@app.get("/diagnostics", tags=["Health"], include_in_schema=False)
async def diagnostics(request: Request):
    """Dev-only deep introspection endpoint. Blocked in production."""
    from core.settings import settings as app_settings
    from core.version import get_version_info

    # Block in production entirely
    if not IS_DEV:
        return JSONResponse(status_code=403, content={"error": "Diagnostics disabled in production"})

    return {
        "version_info": get_version_info(),
        "mode": app_settings.APP_MODE.value,
        "middleware_stack": [
            "prometheus_metrics",
            "rate_limit",
            "ai_firewall",
            "auth",
            "self_healing",
            "error_handler",
            "request_metadata + security_headers",
            "cors",
        ],
        "feature_flags": {
            "ai_firewall": app_settings.ENABLE_AI_FIREWALL,
            "self_healing": app_settings.ENABLE_SELF_HEALING,
            "rag": app_settings.ENABLE_RAG,
            "sentry": _sentry_available and bool(_sentry_dsn),
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
# Custom exception handler — maps TeamGenieError → correct HTTP status + code
# ---------------------------------------------------------------------------
from core.exceptions import TeamGenieError

@app.exception_handler(TeamGenieError)
async def teamgenie_exception_handler(request: Request, exc: TeamGenieError):
    """Handle all custom TeamGenie exceptions with proper status codes."""
    request_id = getattr(request.state, "request_id", "unknown")

    logger.warning(
        "handled_error",
        error_code=exc.error_code,
        message=exc.message[:200],
        status_code=exc.status_code,
        request_id=request_id,
        path=request.url.path,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "request_id": request_id,
            }
        },
    )


# ---------------------------------------------------------------------------
# Global exception handler (catch-all for untyped exceptions)
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "unknown")

    # Forward to Sentry if available and configured
    if _sentry_available and _sentry_dsn:
        try:
            sentry_sdk.capture_exception(exc)
        except Exception:
            pass  # Never let Sentry reporting crash the error handler

    # Truncate error message for logging (prevents log bloat from giant payloads)
    error_msg = str(exc)[:500]

    logger.error(
        "global.unhandled_exception",
        error=error_msg,
        error_type=type(exc).__name__,
        request_id=request_id,
        path=request.url.path,
    )

    # Environment-aware response: show error type in dev, generic in production
    if IS_DEV:
        user_message = f"An unexpected error occurred ({type(exc).__name__}). Our team has been notified."
    else:
        user_message = "An unexpected error occurred. Our team has been notified."

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "internal_server_error",
                "message": user_message,
                "request_id": request_id,
            }
        },
    )
