"""
Test configuration — Fixtures for FastAPI testing.
"""

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Mock auth headers for testing."""
    return {"Authorization": "Bearer test_token_dev"}
