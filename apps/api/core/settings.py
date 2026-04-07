"""
Application Mode & Settings — Upgrade #1 from Master Doctrine v2.0.
Provides tri-modal runtime: DEMO → HYBRID → PRODUCTION.
Zero breaking changes — every existing feature defaults to its current behavior.
"""

from __future__ import annotations

import os
from enum import StrEnum
from functools import lru_cache


class AppMode(StrEnum):
    """Three distinct runtime modes."""

    DEMO = "demo"  # Sample data, no external deps, dev auth
    HYBRID = "hybrid"  # Real DB maybe, fallback to heuristics
    PRODUCTION = "production"  # All real, strict validation


class Settings:
    """Lightweight settings that read from os.environ (already loaded by dotenv)."""

    @property
    def APP_MODE(self) -> AppMode:
        raw = os.getenv("APP_MODE", "demo").lower()
        try:
            return AppMode(raw)
        except ValueError:
            return AppMode.DEMO

    # --- Feature Flags ---
    @property
    def ENABLE_AI_FIREWALL(self) -> bool:
        return os.getenv("ENABLE_AI_FIREWALL", "false").lower() == "true"

    @property
    def ENABLE_SELF_HEALING(self) -> bool:
        return os.getenv("ENABLE_SELF_HEALING", "false").lower() == "true"

    @property
    def ENABLE_RAG(self) -> bool:
        return os.getenv("ENABLE_RAG", "false").lower() == "true"

    # --- LLM Provider Keys ---
    @property
    def GEMINI_API_KEY(self) -> str | None:
        v = os.getenv("GEMINI_API_KEY", "")
        return v if v and not v.startswith("AIzaSyXXXX") else None

    @property
    def CLAUDE_API_KEY(self) -> str | None:
        v = os.getenv("CLAUDE_API_KEY", "")
        return v if v and v != "your_anthropic_key_here" else None

    # --- Databases ---
    @property
    def TURSO_DATABASE_URL(self) -> str | None:
        v = os.getenv("TURSO_DATABASE_URL", "")
        return v if v and "XXXXX" not in v else None

    @property
    def UPSTASH_REDIS_URL(self) -> str | None:
        v = os.getenv("UPSTASH_REDIS_URL", "")
        return v if v and "xxxxx" not in v else None

    @property
    def PINECONE_API_KEY(self) -> str | None:
        v = os.getenv("PINECONE_API_KEY", "")
        return v if v and "xxxx" not in v else None

    def has_real_llm(self) -> bool:
        """Check if any real LLM provider is configured."""
        return bool(self.GEMINI_API_KEY or self.CLAUDE_API_KEY)

    def has_real_db(self) -> bool:
        """Check if a real database is configured."""
        return bool(self.TURSO_DATABASE_URL)

    def has_vector_db(self) -> bool:
        """Check if vector search is available."""
        return bool(self.PINECONE_API_KEY)


@lru_cache
def get_settings() -> Settings:
    """Cached singleton."""
    return Settings()


settings = get_settings()
