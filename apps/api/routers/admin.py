import os

import structlog
from fastapi import APIRouter, Depends, HTTPException, Request

from db.connection import execute_query

logger = structlog.get_logger(__name__)
router = APIRouter()


async def admin_only(request: Request):
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")

    # Allow dev_user in development
    if user_id == "dev_user" and os.getenv("PYTHON_ENV") == "development":
        return

    try:
        rows = await execute_query("SELECT role, tier FROM users WHERE id = ?", (user_id,))
        if not rows:
            raise HTTPException(status_code=403, detail="User record not found")

        role, tier = rows[0]
        if role != "admin" and tier != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
    except Exception as e:
        logger.error("admin.auth_check_failed", error=str(e), user_id=user_id)
        raise HTTPException(status_code=403, detail="Administrative verification failed")


@router.get("/quotas", dependencies=[Depends(admin_only)])
async def get_all_quotas():
    try:
        rows = await execute_query("""
            SELECT u.email, d.usage_date, d.generations_count, d.api_calls
            FROM daily_usage d
            JOIN users u ON d.user_id = u.id
            ORDER BY d.usage_date DESC, d.generations_count DESC
            LIMIT 100
        """)
        return [{"email": r[0], "date": r[1], "generations": r[2], "api_calls": r[3]} for r in rows]
    except Exception as e:
        logger.error("admin.quotas_failed", error=str(e))
        return []


@router.get("/stats", dependencies=[Depends(admin_only)])
async def get_system_stats():
    try:
        user_count = await execute_query("SELECT COUNT(*) FROM users")
        team_count = await execute_query("SELECT COUNT(*) FROM teams")
        sub_count = await execute_query("SELECT COUNT(*) FROM subscriptions WHERE status='active'")

        return {
            "total_users": user_count[0][0] if user_count else 0,
            "total_teams": team_count[0][0] if team_count else 0,
            "active_subscriptions": sub_count[0][0] if sub_count else 0,
        }
    except Exception as e:
        logger.error("admin.stats_failed", error=str(e))
        return {"total_users": 0, "total_teams": 0, "active_subscriptions": 0}
