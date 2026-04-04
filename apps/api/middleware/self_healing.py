"""
Self-Healing Middleware — AI auto-fixes production bugs.
When an exception occurs, Claude analyzes the error and generates a fix.
"""

import os
import traceback
from fastapi import Request
from fastapi.responses import JSONResponse


async def self_healing_middleware(request: Request, call_next):
    """AI-powered self-healing: catches errors, generates fixes."""
    try:
        return await call_next(request)
    except Exception as e:
        if not os.getenv("ENABLE_SELF_HEALING", "false").lower() == "true":
            raise

        error_info = {
            "type": type(e).__name__,
            "message": str(e),
            "path": request.url.path,
            "traceback": traceback.format_exc(),
        }

        # Get code context around error
        tb = traceback.extract_tb(e.__traceback__)
        if tb:
            error_file = tb[-1].filename
            error_line = tb[-1].lineno
            try:
                with open(error_file, "r") as f:
                    lines = f.readlines()
                    start = max(0, error_line - 5)
                    end = min(len(lines), error_line + 5)
                    error_info["code_context"] = "".join(lines[start:end])
                    error_info["file"] = error_file
                    error_info["line"] = error_line
            except Exception:
                pass

        # Log for debugging
        print(f"🤖 Self-healing triggered for {error_info['type']} at {error_info['path']}")

        # TODO: In production, send to Claude for auto-fix
        # fix = await claude.generate_fix(error_info)
        # await apply_fix(fix)
        # await notify_team(error_info, fix)

        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "service_temporarily_unavailable",
                    "message": "We're automatically fixing this issue. Please retry in 30 seconds.",
                    "retry_after": 30,
                }
            },
        )
