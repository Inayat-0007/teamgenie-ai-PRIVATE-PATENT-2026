"""
Audit Trail Service — Upgrade #6 from Master Doctrine v2.0.
Complete forensic log of every team generation for reproducibility.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Optional

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)

from core.settings import settings, AppMode
from core.version import ENGINE_VERSION


class AuditService:
    """Store complete generation context for debugging and reproducibility."""

    def __init__(self):
        # Ensure audit directory exists
        os.makedirs("data", exist_ok=True)

    async def log_generation(
        self,
        request_id: str,
        match_id: str,
        request_data: dict,
        team: dict,
        meta: dict,
    ) -> None:
        """Record a full generation audit entry."""
        audit_entry = {
            "request_id": request_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "match_id": match_id,
            "mode": settings.APP_MODE.value,
            "engine_version": ENGINE_VERSION,
            "request": {
                "budget": request_data.get("budget"),
                "risk_level": request_data.get("risk_level"),
            },
            "output": {
                "player_count": len(team.get("players", [])),
                "total_cost": team.get("total_cost"),
                "captain": team.get("captain"),
                "vice_captain": team.get("vice_captain"),
                "predicted_total": team.get("predicted_total"),
            },
            "execution": {
                "timings": meta.get("stages_ms"),
                "total_ms": meta.get("total_ms"),
            },
        }

        try:
            audit_path = os.path.join("data", "audit_log.jsonl")
            with open(audit_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(audit_entry) + "\n")
            logger.info("audit.logged", request_id=request_id)
        except Exception as exc:
            logger.warning("audit.log_failed", error=str(exc))


audit_service = AuditService()
