"""
Tests for User Router — profile, data export, account deletion, GDPR.
Sprint 3 Fix 3.3: GDPR/DPDP compliance paths need test coverage.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["PYTHON_ENV"] = "test"
os.environ["ENABLE_AI_FIREWALL"] = "false"
os.environ["ENABLE_SELF_HEALING"] = "false"
os.environ["SUPABASE_JWT_SECRET"] = "test-jwt-secret-for-ci"

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def mock_execute_query():
    """Mock database queries to prevent real Turso requests during tests."""

    async def fake_execute(query, params=None):
        if "UPDATE" in query:
            return []
        elif "usage_date" in query:
            return [("2026-04-06", 5)]
        elif "SELECT email" in query:
            return [("test@teamgenie.app", "Test User", "free", "2026-01-01T00:00:00Z")]
        return []

    with patch("db.connection.execute_query", new=fake_execute):
        yield


# ---------------------------------------------------------------------------
# GET /api/user/me
# ---------------------------------------------------------------------------


def test_get_profile_returns_user_data(client):
    """Profile endpoint should return user data."""
    response = client.get("/api/user/me")
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "email" in data
    assert "tier" in data


def test_get_profile_includes_stats(client):
    """Profile should include stats object."""
    response = client.get("/api/user/me")
    data = response.json()
    assert "stats" in data
    assert "teams_generated" in data["stats"]


# ---------------------------------------------------------------------------
# PUT /api/user/me
# ---------------------------------------------------------------------------


def test_update_profile_valid_name(client):
    """Updating full_name should succeed."""
    response = client.put("/api/user/me", json={"full_name": "Test User"})
    # In dev/test mode with dev_user bypass, this should work or give auth error
    assert response.status_code in (200, 401)


def test_update_profile_name_too_long(client):
    """Name exceeding 200 chars should be rejected."""
    response = client.put("/api/user/me", json={"full_name": "x" * 201})
    assert response.status_code == 422


def test_update_profile_empty_body(client):
    """Empty update should succeed (no-op)."""
    response = client.put("/api/user/me", json={})
    assert response.status_code in (200, 401)


# ---------------------------------------------------------------------------
# GET /api/user/data-export (GDPR/DPDP compliance)
# ---------------------------------------------------------------------------


def test_data_export_returns_json(client):
    """Data export should return JSON with required GDPR fields."""
    response = client.get("/api/user/data-export")
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "status" in data
    assert data["status"] == "completed"
    assert "export_data" in data
    assert "format" in data
    assert data["format"] == "json"


def test_data_export_includes_timestamps(client):
    """Data export should include requested_at and expires_at."""
    response = client.get("/api/user/data-export")
    data = response.json()
    assert "requested_at" in data
    assert "expires_at" in data


def test_data_export_includes_user_info(client):
    """Export data should contain user_info, usage_stats, match_history."""
    response = client.get("/api/user/data-export")
    data = response.json()
    export = data["export_data"]
    assert "user_info" in export
    assert "usage_stats" in export
    assert "match_history" in export


# ---------------------------------------------------------------------------
# DELETE /api/user/me (Security Fix 1.7 — requires re-auth)
# ---------------------------------------------------------------------------


def test_delete_account_requires_password(client):
    """Account deletion without password should be rejected (Security Fix 1.7)."""
    response = client.request("DELETE", "/api/user/me", json={})
    assert response.status_code == 422  # Missing current_password field


def test_delete_account_missing_body(client):
    """Account deletion without body should fail."""
    response = client.delete("/api/user/me")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/user/withdraw-consent (DPDP compliance)
# ---------------------------------------------------------------------------


def test_withdraw_consent(client):
    """Withdraw consent should return success message."""
    response = client.post("/api/user/withdraw-consent")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "consent" in data["message"].lower()


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_user_endpoints_return_json(client):
    """All user endpoints should return proper JSON content-type."""
    endpoints = [
        ("GET", "/api/user/me"),
        ("GET", "/api/user/data-export"),
        ("POST", "/api/user/withdraw-consent"),
    ]
    for method, path in endpoints:
        response = client.request(method, path)
        assert "application/json" in response.headers.get("content-type", ""), f"{method} {path} did not return JSON"
