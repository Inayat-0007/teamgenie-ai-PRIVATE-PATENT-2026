"""
Tests for team generation endpoint + security hardening + architecture fixes.
Tests: health, readiness, diagnostics, team generation, timing, versioning,
       match_id validation, error handling, data validation, constraint checks,
       custom exceptions, security headers, firewall, auth.
"""

from unittest.mock import AsyncMock, patch
import pytest


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


def _mock_team_result():
    """Shared mock result for generate_team_with_agents."""
    return {
        "team": {
            "players": [
                {"id": f"p{i}", "name": "Player", "role": "BAT", "price": 9.0,
                 "predicted_points": 50.0, "confidence": 0.8, "ownership_pct": 5.0,
                 "form_trend": "stable"}
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


@patch('services.ai_service.generate_team_with_agents', new_callable=AsyncMock)
def test_generate_team_valid_request(mock_generate, client):
    mock_generate.return_value = _mock_team_result()
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
    assert "model_version" in data
    assert "mode" in data


@patch('services.ai_service.generate_team_with_agents', new_callable=AsyncMock)
def test_generate_team_has_timing_info(mock_generate, client):
    """Upgrade #2: Stage timing instrumentation."""
    mock_generate.return_value = _mock_team_result()
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
        json={"match_id": "test-match-001", "budget": 100, "risk_level": "extreme"},
    )
    assert response.status_code == 422


def test_generate_team_budget_exceeded(client):
    response = client.post(
        "/api/team/generate",
        json={"match_id": "test-match-001", "budget": 150, "risk_level": "balanced"},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# match_id validation tests
# ---------------------------------------------------------------------------

def test_generate_team_match_id_with_special_chars(client):
    response = client.post(
        "/api/team/generate",
        json={"match_id": "'; DROP TABLE teams; --", "budget": 100, "risk_level": "balanced"},
    )
    assert response.status_code == 422


def test_generate_team_match_id_empty_string(client):
    response = client.post(
        "/api/team/generate",
        json={"match_id": "", "budget": 100, "risk_level": "balanced"},
    )
    assert response.status_code == 422


def test_generate_team_match_id_with_spaces(client):
    response = client.post(
        "/api/team/generate",
        json={"match_id": "ipl 2026 match 1", "budget": 100, "risk_level": "balanced"},
    )
    assert response.status_code == 422


@patch('services.ai_service.generate_team_with_agents', new_callable=AsyncMock)
def test_generate_team_valid_match_id_formats(mock_generate, client):
    mock_generate.return_value = _mock_team_result()
    valid_ids = ["ipl_2026_01", "match-123", "IPL2026CSKvsMI", "t20_world_cup-2026"]
    for match_id in valid_ids:
        response = client.post(
            "/api/team/generate",
            json={"match_id": match_id, "budget": 100, "risk_level": "balanced"},
        )
        assert response.status_code != 422, f"Valid match_id '{match_id}' was rejected: {response.text}"


def test_generate_team_negative_budget(client):
    response = client.post(
        "/api/team/generate",
        json={"match_id": "test-match-001", "budget": -10, "risk_level": "balanced"},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Security headers tests
# ---------------------------------------------------------------------------

def test_request_metadata_headers(client):
    """Every response should have X-Request-ID and X-Response-Time."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert "x-response-time" in response.headers


def test_security_headers_present(client):
    """Responses should include defense-in-depth security headers."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("x-xss-protection") == "1; mode=block"
    assert "strict-origin" in response.headers.get("referrer-policy", "")


# ---------------------------------------------------------------------------
# Data validation tests (anti-hallucination)
# ---------------------------------------------------------------------------

def test_player_data_validation_rejects_malformed():
    """_validate_player_data should reject players with missing/invalid fields."""
    from services.ai_service import _validate_player_data

    malformed_players = [
        {"id": "p1", "name": "NoPrice", "role": "batsman", "predicted_points": 50, "team": "A"},
        {"id": "p2", "name": "ZeroPrice", "role": "batsman", "price": 0, "predicted_points": 50, "team": "A"},
        {"id": "p3", "name": "NegPts", "role": "batsman", "price": 9, "predicted_points": -10, "team": "A"},
        {"id": "p4", "name": "BadRole", "role": "goalkeeper", "price": 9, "predicted_points": 50, "team": "A"},
        {"id": "p5", "name": "Good1", "role": "batsman", "price": 9, "predicted_points": 50, "team": "A"},
        {"id": "p5", "name": "Good1Dup", "role": "batsman", "price": 9, "predicted_points": 50, "team": "A"},
        {"id": "p6", "name": "Expensive", "role": "batsman", "price": 25, "predicted_points": 50, "team": "A"},
        {"id": "p_valid", "name": "ValidPlayer", "role": "bowler", "price": 8.5, "predicted_points": 55, "team": "B"},
    ]
    result = _validate_player_data(malformed_players)
    assert len(result) == 2
    valid_ids = {p["id"] for p in result}
    assert "p_valid" in valid_ids
    assert "p5" in valid_ids


def test_player_data_validation_passes_clean_data():
    from services.ai_service import _validate_player_data

    clean_players = [
        {"id": f"player_{i}", "name": f"Player {i}", "role": "batsman", "price": 8.0,
         "predicted_points": 55.0, "ownership_pct": 30, "team": "CSK"}
        for i in range(11)
    ]
    result = _validate_player_data(clean_players)
    assert len(result) == 11


def test_team_output_constraint_validation():
    from services.ai_service import _validate_team_output

    # Captain not in roster
    bad_team = {
        "players": [{"id": f"p{i}", "role": "batsman", "team": "MI"} for i in range(11)],
        "captain": "not_in_team", "vice_captain": "p0",
        "total_cost": 99, "predicted_total": 500, "risk_score": 0.5,
    }
    warnings = _validate_team_output(bad_team, budget=100)
    assert any("Captain" in w for w in warnings)

    # Budget exceeded
    over_budget = {
        "players": [{"id": f"p{i}", "role": "batsman", "team": "MI"} for i in range(11)],
        "captain": "p0", "vice_captain": "p1",
        "total_cost": 110, "predicted_total": 500, "risk_score": 0.5,
    }
    warnings = _validate_team_output(over_budget, budget=100)
    assert any("Budget" in w for w in warnings)

    # Captain == Vice-Captain
    same_cv = {
        "players": [{"id": f"p{i}", "role": "batsman", "team": "MI"} for i in range(11)],
        "captain": "p0", "vice_captain": "p0",
        "total_cost": 99, "predicted_total": 500, "risk_score": 0.5,
    }
    warnings = _validate_team_output(same_cv, budget=100)
    assert any("same" in w.lower() for w in warnings)


def test_team_output_valid_passes():
    from services.ai_service import _validate_team_output

    valid_team = {
        "players": [
            {"id": f"p{i}", "role": "batsman", "team": "MI" if i < 5 else "CSK"}
            for i in range(11)
        ],
        "captain": "p0", "vice_captain": "p1",
        "total_cost": 99, "predicted_total": 500, "risk_score": 0.5,
    }
    warnings = _validate_team_output(valid_team, budget=100)
    assert len(warnings) == 0


def test_match_id_validator():
    from services.ai_service import _validate_match_id

    _validate_match_id("ipl_2026_01")
    _validate_match_id("match-123")
    _validate_match_id("abc")

    with pytest.raises(ValueError): _validate_match_id("")
    with pytest.raises(ValueError): _validate_match_id("   ")
    with pytest.raises(ValueError): _validate_match_id("match id")
    with pytest.raises(ValueError): _validate_match_id("'; DROP TABLE--")
    with pytest.raises(ValueError): _validate_match_id("../../../etc/passwd")


def test_error_handler_sanitizes_traceback():
    from middleware.error_handler import _sanitize_traceback

    short = "Traceback: line 42 in main.py"
    assert _sanitize_traceback(short) == short

    long_tb = "x" * 10000
    result = _sanitize_traceback(long_tb)
    assert len(result) < 5000
    assert "TRUNCATED" in result

    sensitive = "Error connecting to redis://user:PASSWORD_HERE@host:6379"
    result = _sanitize_traceback(sensitive)
    assert "REDACTED" in result


# ---------------------------------------------------------------------------
# Custom Exception tests
# ---------------------------------------------------------------------------

def test_custom_exceptions_have_correct_status():
    """Each custom exception should carry its own HTTP status code and error code."""
    from core.exceptions import (
        TeamGenieError, AuthenticationError, AuthorizationError,
        ValidationError, NotFoundError, QuotaExceededError,
        ExternalServiceError, GenerationError, FirewallBlockedError,
    )

    assert AuthenticationError("test").status_code == 401
    assert AuthenticationError("test").error_code == "authentication_failed"

    assert AuthorizationError("test").status_code == 403
    assert ValidationError("test").status_code == 422
    assert NotFoundError("test").status_code == 404
    assert QuotaExceededError("test").status_code == 429
    assert ExternalServiceError("test").status_code == 502
    assert GenerationError("test").status_code == 500
    assert FirewallBlockedError("test").status_code == 403


def test_custom_exception_inherits_base():
    """All custom exceptions should inherit from TeamGenieError."""
    from core.exceptions import (
        TeamGenieError, AuthenticationError, ValidationError,
        QuotaExceededError, ExternalServiceError,
    )

    assert issubclass(AuthenticationError, TeamGenieError)
    assert issubclass(ValidationError, TeamGenieError)
    assert issubclass(QuotaExceededError, TeamGenieError)
    assert issubclass(ExternalServiceError, TeamGenieError)


# ---------------------------------------------------------------------------
# Firewall tests
# ---------------------------------------------------------------------------

def test_firewall_attack_detection():
    """Firewall should detect common attack patterns."""
    from security.ai_firewall import _contains_attack

    assert _contains_attack("SELECT * FROM users WHERE 1=1") is True
    assert _contains_attack("'; DROP TABLE users; --") is True
    assert _contains_attack("<script>alert('xss')</script>") is True
    assert _contains_attack("../../etc/passwd") is True
    assert _contains_attack("; rm -rf /") is True
    assert _contains_attack("UNION ALL SELECT * FROM passwords") is True
    assert _contains_attack("http://127.0.0.1/admin") is True  # SSRF

    # Should NOT flag normal content
    assert _contains_attack("Hello World") is False
    assert _contains_attack('{"match_id": "ipl-2026-01"}') is False
    assert _contains_attack("Normal search query about cricket") is False


def test_firewall_ip_tracking():
    """IP violation tracking should work correctly."""
    from security.ai_firewall import _record_violation, _is_ip_banned, _ip_violations

    test_ip = "test_192.168.1.99"
    # Clear any previous state
    _ip_violations[test_ip] = []

    assert _is_ip_banned(test_ip) is False

    for i in range(5):
        _record_violation(test_ip)

    assert _is_ip_banned(test_ip) is True

    # Cleanup
    _ip_violations.pop(test_ip, None)


def test_firewall_header_check():
    """Header injection patterns should be detected."""
    from security.ai_firewall import _HEADER_ATTACK_PATTERNS
    import re

    crlf_pattern = _HEADER_ATTACK_PATTERNS[0]
    assert crlf_pattern.search("normal-header") is None
    assert crlf_pattern.search("header\r\ninjection") is not None


# ---------------------------------------------------------------------------
# Auth middleware tests
# ---------------------------------------------------------------------------

def test_auth_public_routes():
    """Public routes should be accessible without auth."""
    from middleware.auth import _is_public_route

    assert _is_public_route("/health") is True
    assert _is_public_route("/docs") is True
    assert _is_public_route("/api/auth/login") is True
    assert _is_public_route("/api/auth/register") is True
    assert _is_public_route("/api/auth/forgot-password") is True
    assert _is_public_route("/api/auth/refresh") is True
    assert _is_public_route("/metrics") is True

    # Protected routes should NOT be public
    assert _is_public_route("/api/team/generate") is False
    assert _is_public_route("/api/user/profile") is False


def test_auth_token_revocation():
    """Token revocation list should work correctly."""
    from middleware.auth import revoke_token, is_token_revoked, _revoked_tokens

    test_jti = "test_jti_abc123"

    # Ensure clean state
    _revoked_tokens.discard(test_jti)
    assert is_token_revoked(test_jti) is False

    revoke_token(test_jti)
    assert is_token_revoked(test_jti) is True

    # Cleanup
    _revoked_tokens.discard(test_jti)


# ---------------------------------------------------------------------------
# Auth service tests
# ---------------------------------------------------------------------------

def test_auth_service_email_validation():
    """Auth service should validate email format before calling Supabase."""
    from services.auth_service import _validate_email
    from core.exceptions import ValidationError

    _validate_email("user@example.com")
    _validate_email("test.user+tag@domain.co")

    with pytest.raises(ValidationError): _validate_email("")
    with pytest.raises(ValidationError): _validate_email("not-an-email")
    with pytest.raises(ValidationError): _validate_email("@no-local.com")
    with pytest.raises(ValidationError): _validate_email("a" * 255 + "@x.com")


def test_auth_service_password_validation():
    """Auth service should validate password strength."""
    from services.auth_service import _validate_password
    from core.exceptions import ValidationError

    _validate_password("SecurePass123!")

    with pytest.raises(ValidationError): _validate_password("")
    with pytest.raises(ValidationError): _validate_password("short")
    with pytest.raises(ValidationError): _validate_password("a" * 200)


def test_forgot_password_no_email_leak(client):
    """Forgot-password should not reveal whether an email exists."""
    response = client.post(
        "/api/auth/forgot-password",
        json={"email": "nonexistent@example.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "If an account exists" in data["message"]
