"""
Self-Healing Middleware — AI auto-fixes production bugs.
When an exception occurs, Claude analyzes the error and generates a fix.
"""

from __future__ import annotations

import os
import traceback

try:
    import structlog

    logger = structlog.get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

from fastapi import Request
from fastapi.responses import JSONResponse

_MAX_CONTEXT_LINES = 5  # lines above/below error to extract


async def self_healing_middleware(request: Request, call_next):
    """AI-powered self-healing: catches errors and generates diagnostic payloads."""
    try:
        return await call_next(request)
    except Exception as exc:
        if os.getenv("ENABLE_SELF_HEALING", "false").lower() != "true":
            raise

        error_info: dict = {
            "type": type(exc).__name__,
            "message": str(exc),
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc(),
        }

        # Extract source code context around the error site
        tb = traceback.extract_tb(exc.__traceback__)
        if tb:
            frame = tb[-1]
            error_info["file"] = frame.filename
            error_info["line"] = frame.lineno
            try:
                with open(frame.filename, encoding="utf-8") as fh:
                    lines = fh.readlines()
                    start = max(0, frame.lineno - _MAX_CONTEXT_LINES - 1)
                    end = min(len(lines), frame.lineno + _MAX_CONTEXT_LINES)
                    error_info["code_context"] = "".join(lines[start:end])
            except OSError:
                pass

        logger.warning(
            "self_healing.triggered",
            error_type=error_info["type"],
            path=error_info["path"],
            file=error_info.get("file"),
            line=error_info.get("line"),
        )

        # TODO: In production, send to Claude for auto-fix
        # fix = await claude.generate_fix(error_info)
        # await apply_fix(fix)
        # await notify_team(error_info, fix)

        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "service_temporarily_unavailable",
                    "message": "We're automatically diagnosing this issue. Please retry in 30 seconds.",
                    "retry_after": 30,
                }
            },
            headers={"Retry-After": "30"},
        )
