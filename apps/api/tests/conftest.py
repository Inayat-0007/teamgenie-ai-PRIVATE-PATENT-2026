"""
Test configuration — Fixtures for FastAPI testing.
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# Force development mode for tests
os.environ.setdefault("PYTHON_ENV", "development")
os.environ.setdefault("ENABLE_AI_FIREWALL", "false")
os.environ.setdefault("ENABLE_SELF_HEALING", "false")

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
