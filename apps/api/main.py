"""
TeamGenie AI — FastAPI Backend
Production-grade async API with self-healing middleware.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import os
import sentry_sdk

from routers import auth, team, player, match, user
from middleware.rate_limit import RateLimitMiddleware
from middleware.error_handler import error_handler_middleware

# Sentry (error tracking)
if os.getenv("SENTRY_DSN"):
    sentry_sdk.init(
        dsn=os.getenv("SENTRY_DSN"),
        traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
        environment=os.getenv("SENTRY_ENVIRONMENT", "development"),
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    print("🚀 Starting TeamGenie API v1.0.0...")
    # Startup: init connections
    from services.cache_service import CacheService
    app.state.cache = CacheService()
    await app.state.cache.connect()
    print("✅ Redis connected")
    print("✅ Ready to serve requests")
    yield
    # Shutdown
    print("👋 Shutting down gracefully...")
    await app.state.cache.disconnect()


app = FastAPI(
    title="TeamGenie AI API",
    description="AI-powered fantasy sports intelligence platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# --- MIDDLEWARE STACK (order matters!) ---

# 1. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://teamgenie.app",
        "https://www.teamgenie.app",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 2. Request ID + Timing middleware
@app.middleware("http")
async def add_request_metadata(request: Request, call_next):
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start = time.perf_counter()

    response = await call_next(request)

    duration_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time"] = f"{duration_ms:.0f}ms"
    return response


# 3. Error handler
app.middleware("http")(error_handler_middleware)


# --- ROUTERS ---
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(team.router, prefix="/api/team", tags=["Team Generation"])
app.include_router(player.router, prefix="/api/player", tags=["Player Insights"])
app.include_router(match.router, prefix="/api/match", tags=["Match Data"])
app.include_router(user.router, prefix="/api/user", tags=["User Management"])


# --- HEALTH CHECK ---
@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "teamgenie-api",
        "timestamp": time.time(),
    }


# --- GLOBAL EXCEPTION HANDLER ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if os.getenv("SENTRY_DSN"):
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
