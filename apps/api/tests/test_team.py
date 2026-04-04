"""
Tests for team generation endpoint + Master Doctrine v2.0 upgrades.
Tests: health, readiness, diagnostics, team generation, timing, versioning.
"""

from unittest.mock import AsyncMock, patch


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_readiness_check(client):
    """Upgrade #3: Readiness endpoint."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert "ready" in data
    assert "checks" in data
    assert "mode" in data["checks"]


def test_diagnostics_in_dev_mode(client):
    """Upgrade #3: Diagnostics available in dev/test mode."""
    response = client.get("/diagnostics")
    assert response.status_code == 200
    data = response.json()
    assert "version_info" in data
    assert "mode" in data
    assert "middleware_stack" in data
    assert "feature_flags" in data
    assert "providers" in data


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
    # Upgrade #5: Engine versioning
    assert "model_version" in data
    # Upgrade #1: Mode awareness
    assert "mode" in data


@patch('services.ai_service.generate_team_with_agents', new_callable=AsyncMock)
def test_generate_team_has_timing_info(mock_generate, client):
    """Upgrade #2: Stage timing instrumentation."""
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
        json={"match_id": "test-match-001", "budget": 100, "risk_level": "balanced"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "timings" in data
    if data["timings"]:
        assert "total_ms" in data["timings"]


def test_explain_team_endpoint(client):
    """Upgrade #9: Separate explanation endpoint."""
    response = client.post("/api/team/explain?team_id=last")
    assert response.status_code == 200
    data = response.json()
    assert "reasoning" in data
    assert "confidence" in data


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
