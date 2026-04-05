"""
Test configuration — Fixtures for FastAPI testing.
"""

from __future__ import annotations

import os
import sys

# Ensure the api directory is on Python's path (needed for CI runners)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Force safe test mode BEFORE any app imports
os.environ["PYTHON_ENV"] = "test"
os.environ["ENABLE_AI_FIREWALL"] = "false"
os.environ["ENABLE_SELF_HEALING"] = "false"
os.environ["SUPABASE_JWT_SECRET"] = "test-jwt-secret-for-ci"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402
from unittest.mock import AsyncMock, patch  # noqa: E402


@pytest.fixture
def client():
    """Create test client with lifespan events."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers():
    """Mock auth headers for protected-route testing."""
    return {"Authorization": "Bearer test_token_dev"}


@pytest.fixture(autouse=True)
def mock_scraper_service():
    """Mock the scraper globally in tests to prevent CI network hangs."""
    with patch("services.scraper_service.scraper_service.get_match_context", new_callable=AsyncMock) as mock_scrape:
        mock_scrape.return_value = "Mocked Pitch, Weather, and Injury Context"
        yield mock_scrape
