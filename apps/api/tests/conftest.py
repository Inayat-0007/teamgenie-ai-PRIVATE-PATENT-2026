"""
Test configuration — Fixtures for FastAPI testing.
"""

from __future__ import annotations

import os

# Force safe test mode BEFORE any app imports
os.environ["PYTHON_ENV"] = "test"
os.environ["ENABLE_AI_FIREWALL"] = "false"
os.environ["ENABLE_SELF_HEALING"] = "false"
os.environ["SUPABASE_JWT_SECRET"] = "test-jwt-secret-for-ci"

import pytest
from fastapi.testclient import TestClient

from main import app  # noqa: E402 — must import after env setup


@pytest.fixture
def client():
    """Create test client with lifespan events."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers():
    """Mock auth headers for protected-route testing."""
    return {"Authorization": "Bearer test_token_dev"}
