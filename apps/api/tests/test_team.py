"""Tests for team generation endpoint."""

from unittest.mock import AsyncMock, patch


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@patch('services.ai_service.generate_team_with_agents', new_callable=AsyncMock)
def test_generate_team_requires_match_id(mock_generate, client):
    response = client.post(
        "/api/team/generate",
        json={"budget": 100, "risk_level": "balanced"},
    )
    assert response.status_code == 422  # Validation error (missing match_id)


@patch('services.ai_service.generate_team_with_agents', new_callable=AsyncMock)
def test_generate_team_valid_request(mock_generate, client):
    mock_generate.return_value = {
        "team": {
            "players": [
                {"id": f"p{i}", "name": "Player", "role": "BAT", "price": 9.0,
                 "predicted_points": 50.0, "confidence": 0.8, "ownership_pct": 5.0, "form_trend": "stable"}
                for i in range(11)
            ],
            "captain": "p0",
            "vice_captain": "p1",
            "total_cost": 99.0,
            "predicted_total": 550.0,
            "risk_score": 0.5
        },
        "reasoning": {
            "budget_agent": "mock",
            "differential_agent": "mock",
            "risk_agent": "mock"
        }
    }
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


def test_generate_team_invalid_risk_level(client):
    response = client.post(
        "/api/team/generate",
        json={
            "match_id": "test-match-001",
            "budget": 100,
            "risk_level": "extreme",  # Invalid
        },
    )
    assert response.status_code == 422


def test_generate_team_budget_exceeded(client):
    response = client.post(
        "/api/team/generate",
        json={
            "match_id": "test-match-001",
            "budget": 150,  # Over 100 limit
            "risk_level": "balanced",
        },
    )
    assert response.status_code == 422
