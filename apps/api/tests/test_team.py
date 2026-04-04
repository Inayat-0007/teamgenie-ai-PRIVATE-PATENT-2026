"""Tests for team generation endpoint."""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_generate_team_requires_match_id():
    response = client.post(
        "/api/team/generate",
        json={"budget": 100, "risk_level": "balanced"},
    )
    assert response.status_code == 422  # Validation error (missing match_id)


def test_generate_team_valid_request():
    response = client.post(
        "/api/team/generate",
        json={
            "match_id": "test-match-001",
            "budget": 100,
            "risk_level": "balanced",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "team" in data
    assert "reasoning" in data
    assert data["generation_time_ms"] >= 0
    assert len(data["team"]["players"]) == 11


def test_generate_team_invalid_risk_level():
    response = client.post(
        "/api/team/generate",
        json={
            "match_id": "test-match-001",
            "budget": 100,
            "risk_level": "extreme",  # Invalid
        },
    )
    assert response.status_code == 422


def test_generate_team_budget_exceeded():
    response = client.post(
        "/api/team/generate",
        json={
            "match_id": "test-match-001",
            "budget": 150,  # Over 100 limit
            "risk_level": "balanced",
        },
    )
    assert response.status_code == 422
