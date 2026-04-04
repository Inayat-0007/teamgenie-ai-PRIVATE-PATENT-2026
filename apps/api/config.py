"""
Application Settings — Pydantic Settings with .env support.
Single source of truth for all configuration values.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    python_env: str = "development"
    api_version: str = "1.0.0"
    debug: bool = False

    # --- Security ---
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    allowed_origins: str = "http://localhost:3000"

    # --- Database ---
    turso_database_url: str = ""
    turso_auth_token: str = ""

    # --- Cache ---
    upstash_redis_url: str = "redis://localhost:6379"

    # --- AI / LLM ---
    gemini_api_key: str = ""
    claude_api_key: str = ""
    openai_api_key: str = ""
    cohere_api_key: str = ""
    primary_llm: str = "gemini-2.0-flash"
    reasoning_llm: str = "claude-haiku-4"

    # --- Vector DB ---
    pinecone_api_key: str = ""
    pinecone_index_name: str = "player-embeddings"

    # --- Scraping ---
    tavily_api_key: str = ""

    # --- Monitoring ---
    sentry_dsn: str = ""
    sentry_traces_sample_rate: float = 0.1
    sentry_environment: str = "development"
    posthog_api_key: str = ""

    # --- Rate Limiting ---
    rate_limit_free_tier: int = 100
    rate_limit_paid_tier: int = 1000

    # --- Feature Flags ---
    enable_ai_firewall: bool = False
    enable_self_healing: bool = False

    @property
    def is_production(self) -> bool:
        return self.python_env == "production"

    @property
    def is_development(self) -> bool:
        return self.python_env == "development"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Cached singleton settings instance."""
    return Settings()
