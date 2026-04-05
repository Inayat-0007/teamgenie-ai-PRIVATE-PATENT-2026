"""
Subscription Service — Tier-based quota enforcement.

Phase 6: Enforces generation limits per subscription tier:
  - Free (Peasant):  2 generations / week
  - Pro (₹199):      3 generations / day
  - Elite (₹999):    Unlimited

Uses in-memory tracking for demo mode. Production would query Turso.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, Tuple

try:
    import structlog
    logger = structlog.get_logger(__name__)
except ImportError:
    import logging
    logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tier Configuration
# ---------------------------------------------------------------------------

TIER_LIMITS: Dict[str, Tuple[int, int]] = {
    # tier: (max_generations, window_seconds)
    "free":  (2,  7 * 86400),   # 2 per week
    "pro":   (3,  86400),       # 3 per day
    "elite": (999999, 86400),   # Unlimited
    # Legacy tiers from models/team.py UserTier
    "per_match": (5, 86400),
    "monthly":   (10, 86400),
    "api":       (999999, 86400),
}


# ---------------------------------------------------------------------------
# In-Memory Quota Tracker (replaced by Turso in production)
# ---------------------------------------------------------------------------

_usage: Dict[str, list] = defaultdict(list)


class SubscriptionService:
    """Tier-based quota enforcement and monetization engine."""

    def check_generation_quota(self, user_id: str, tier: str = "free") -> None:
        """
        Check if user has remaining generation quota.
        Raises Exception if quota exceeded.
        """
        tier = tier.lower()
        limit, window = TIER_LIMITS.get(tier, TIER_LIMITS["free"])

        now = time.time()
        cutoff = now - window

        # Prune old entries
        _usage[user_id] = [ts for ts in _usage[user_id] if ts > cutoff]

        current_count = len(_usage[user_id])

        if current_count >= limit:
            logger.warning(
                "quota.exceeded",
                user_id=user_id,
                tier=tier,
                used=current_count,
                limit=limit,
            )
            if tier == "free":
                raise Exception(
                    f"Free tier limit reached ({limit} teams/week). "
                    f"Upgrade to Pro (₹199/mo) for 3 teams/day or Elite (₹999/mo) for unlimited."
                )
            elif tier == "pro":
                raise Exception(
                    f"Pro tier limit reached ({limit} teams/day). "
                    f"Upgrade to Elite (₹999/mo) for unlimited generations."
                )
            else:
                raise Exception(f"Generation limit reached for tier '{tier}'.")

        # Record usage
        _usage[user_id].append(now)

        logger.info(
            "quota.passed",
            user_id=user_id,
            tier=tier,
            used=current_count + 1,
            limit=limit,
            remaining=limit - current_count - 1,
        )

    def get_usage_stats(self, user_id: str, tier: str = "free") -> dict:
        """Return current usage statistics for a user."""
        tier = tier.lower()
        limit, window = TIER_LIMITS.get(tier, TIER_LIMITS["free"])
        now = time.time()
        cutoff = now - window
        current = len([ts for ts in _usage.get(user_id, []) if ts > cutoff])

        return {
            "user_id": user_id,
            "tier": tier,
            "used": current,
            "limit": limit,
            "remaining": max(0, limit - current),
            "window_hours": window / 3600,
            "upgrade_url": "/pricing" if tier in ("free", "pro") else None,
        }

    def reset_quota(self, user_id: str) -> None:
        """Admin: reset a user's quota (for testing/support)."""
        _usage[user_id] = []
        logger.info("quota.reset", user_id=user_id)


subscription_service = SubscriptionService()
