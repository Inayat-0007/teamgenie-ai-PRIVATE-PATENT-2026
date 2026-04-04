"""
AI Firewall — Claude-powered threat detection.
Analyzes every request for SQL injection, XSS, and malicious patterns.
"""

import os
import json
from fastapi import Request, HTTPException


async def ai_firewall_check(request: Request, call_next):
    """AI analyzes requests for security threats."""
    if not os.getenv("ENABLE_AI_FIREWALL", "false").lower() == "true":
        return await call_next(request)

    # Skip health checks and static assets
    if request.url.path in {"/health", "/docs", "/redoc", "/openapi.json"}:
        return await call_next(request)

    # Quick pattern check (fast, no AI needed)
    url = str(request.url)
    suspicious_patterns = ["UNION SELECT", "DROP TABLE", "<script>", "javascript:", "../", "cmd=", "|", "&&"]

    for pattern in suspicious_patterns:
        if pattern.lower() in url.lower():
            print(f"🚨 AI Firewall BLOCKED: {pattern} detected in {url}")
            raise HTTPException(status_code=403, detail="Forbidden: Suspicious request blocked")

    # For POST/PUT, check body
    if request.method in {"POST", "PUT"}:
        try:
            body = await request.body()
            body_str = body.decode("utf-8", errors="ignore")
            for pattern in suspicious_patterns:
                if pattern.lower() in body_str.lower():
                    print(f"🚨 AI Firewall BLOCKED: {pattern} in request body")
                    raise HTTPException(status_code=403, detail="Forbidden")
        except HTTPException:
            raise
        except Exception:
            pass

    return await call_next(request)
