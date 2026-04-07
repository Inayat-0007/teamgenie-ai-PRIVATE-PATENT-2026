"""
Subscription Service — Tier-based quota enforcement.

Phase 6: Enforces generation limits per subscription tier:
  - Free (Peasant):  2 generations / week
  - Pro (₹199):      3 generations / day
  - Elite (₹999):    Unlimited

Uses in-memory tracking for demo mode. Production would query Turso.
"""

from __future__ import annotations

try:
    import structlog

    logger = structlog.get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)

from core.exceptions import ExternalServiceError, QuotaExceededError

# ---------------------------------------------------------------------------
# Tier Configuration
# ---------------------------------------------------------------------------

TIER_LIMITS: dict[str, tuple[int, int]] = {
    # tier: (max_generations, window_seconds)
    "free": (2, 7 * 86400),  # 2 per week
    "pro": (3, 86400),  # 3 per day
    "elite": (999999, 86400),  # Unlimited
    # Legacy tiers from models/team.py UserTier
    "per_match": (5, 86400),
    "monthly": (10, 86400),
    "api": (999999, 86400),
}


# ---------------------------------------------------------------------------
# Turso Quota Tracker (Production)
# ---------------------------------------------------------------------------


class SubscriptionService:
    """Tier-based quota enforcement and monetization engine using Turso."""

    async def check_generation_quota(self, user_id: str, tier: str = "free") -> None:
        """
        Check if user has remaining generation quota.
        Raises Exception if quota exceeded.
        """
        from db.connection import execute_query

        tier = tier.lower()
        limit, window = TIER_LIMITS.get(tier, TIER_LIMITS["free"])

        # Determine usage based on window vs database
        # For simplicity, we track generations by CURRENT_DATE.
        # If it's a 7-day window, sum the past 7 days. If 1 day (86400), check today's only.
        days_to_check = 7 if window > 86400 else 1

        # Query total usage over the window window
        query = """
            SELECT SUM(generations_count)
            FROM daily_usage
            WHERE user_id = ?
            AND usage_date >= date('now', ?)
        """
        modifier = f"-{days_to_check - 1} days"

        try:
            rows = await execute_query(query, (user_id, modifier))
            current_count = rows[0][0] if rows and rows[0][0] is not None else 0
        except Exception as e:
            # Fail CLOSED when DB is unreachable — raise ExternalServiceError so callers
            # can distinguish "DB down" from an actual quota breach.
            logger.error("turso.quota_query_failed", user_id=user_id, error=str(e))
            raise ExternalServiceError(
                "Service temporarily unavailable. Please try again in a few moments. "
                "Your generation quota could not be verified."
            )

        if current_count >= limit:
            logger.warning(
                "quota.exceeded",
                user_id=user_id,
                tier=tier,
                used=current_count,
                limit=limit,
            )
            if tier == "free":
                raise QuotaExceededError(
                    f"Free tier limit reached ({limit} teams/week). "
                    f"Upgrade to Pro (₹199/mo) for 3 teams/day or Elite (₹999/mo) for unlimited."
                )
            elif tier == "pro":
                raise QuotaExceededError(
                    f"Pro tier limit reached ({limit} teams/day). Upgrade to Elite (₹999/mo) for unlimited generations."
                )
            else:
                raise QuotaExceededError(f"Generation limit reached for tier '{tier}'.")

        # Record usage
        try:
            upsert_query = """
                INSERT INTO daily_usage(user_id, usage_date, generations_count, api_calls)
                VALUES (?, date('now'), 1, 1)
                ON CONFLICT(user_id, usage_date)
                DO UPDATE SET
                  generations_count = generations_count + 1,
                  api_calls = api_calls + 1
            """
            await execute_query(upsert_query, (user_id,))
        except Exception as e:
            logger.error("turso.quota_update_failed", user_id=user_id, error=str(e))

        logger.info(
            "quota.passed",
            user_id=user_id,
            tier=tier,
            used=current_count + 1,
            limit=limit,
            remaining=max(0, limit - current_count - 1),
        )

    async def get_usage_stats(self, user_id: str, tier: str = "free") -> dict:
        """Return current usage statistics for a user from Turso."""
        from db.connection import execute_query

        tier = tier.lower()
        limit, window = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
        days_to_check = 7 if window > 86400 else 1

        query = """
            SELECT SUM(generations_count)
            FROM daily_usage
            WHERE user_id = ?
            AND usage_date >= date('now', ?)
        """
        modifier = f"-{days_to_check - 1} days"

        try:
            rows = await execute_query(query, (user_id, modifier))
            current = rows[0][0] if rows and rows[0][0] is not None else 0
        except Exception as e:
            logger.error("turso.quota_query_failed", user_id=user_id, error=str(e))
            current = 0

        return {
            "user_id": user_id,
            "tier": tier,
            "used": current,
            "limit": limit,
            "remaining": max(0, limit - current),
            "window_hours": window / 3600,
            "upgrade_url": "/pricing" if tier in ("free", "pro") else None,
        }

    async def reset_quota(self, user_id: str) -> None:
        """Admin: reset a user's quota in Turso (for testing/support)."""
        from db.connection import execute_query

        try:
            await execute_query("DELETE FROM daily_usage WHERE user_id = ?", (user_id,))
            logger.info("quota.reset", user_id=user_id)
        except Exception as e:
            logger.error("turso.quota_reset_failed", user_id=user_id, error=str(e))


subscription_service = SubscriptionService()
