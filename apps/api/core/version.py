"""
Engine Versioning — Upgrade #5 from Master Doctrine v2.0.
Track algorithm versions for reproducibility and A/B testing.
"""

from __future__ import annotations

from core.settings import settings

ENGINE_VERSION = "tg-engine-v2.0.0"
ALGORITHM_HASH = "budget-greedy-v1+timing+audit"


def get_version_info() -> dict:
    """Version metadata included in every team response."""
    return {
        "engine": ENGINE_VERSION,
        "algorithm": ALGORITHM_HASH,
        "mode": settings.APP_MODE.value,
    }
