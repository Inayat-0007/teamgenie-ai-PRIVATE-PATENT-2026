"""
Tests for Payment Router — create-order, verify, webhook, status.
Sprint 3 Fix 3.1: Revenue-critical payment paths need 100% test coverage.
"""

from __future__ import annotations

import os
import sys
import json
import hmac
import hashlib
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["PYTHON_ENV"] = "test"
os.environ["ENABLE_AI_FIREWALL"] = "false"
os.environ["ENABLE_SELF_HEALING"] = "false"
os.environ["SUPABASE_JWT_SECRET"] = "test-jwt-secret-for-ci"

from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# POST /api/payment/create-order
# ---------------------------------------------------------------------------

def test_create_order_pro_plan(client):
    """Valid 'pro' plan should return an order with amount 19900 paise."""
    response = client.post("/api/payment/create-order", json={"plan_id": "pro"})
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 19900
    assert data["currency"] == "INR"
    assert data["plan"] == "pro"
    assert "order_id" in data


def test_create_order_elite_plan(client):
    """Valid 'elite' plan should return an order with amount 99900 paise."""
    response = client.post("/api/payment/create-order", json={"plan_id": "elite"})
    assert response.status_code == 200
    data = response.json()
    assert data["amount"] == 99900
    assert data["plan"] == "elite"


def test_create_order_invalid_plan(client):
    """Invalid plan_id should be rejected by Pydantic validation."""
    response = client.post("/api/payment/create-order", json={"plan_id": "hacker"})
    assert response.status_code == 422  # Pydantic validation error


def test_create_order_missing_plan(client):
    """Missing plan_id should return 422."""
    response = client.post("/api/payment/create-order", json={})
    assert response.status_code == 422


def test_create_order_simulated_mode(client):
    """Without Razorpay configured, should return simulated order."""
    response = client.post("/api/payment/create-order", json={"plan_id": "pro"})
    data = response.json()
    assert data.get("simulated") is True
    assert data["order_id"].startswith("order_sim_")


# ---------------------------------------------------------------------------
# POST /api/payment/verify
# ---------------------------------------------------------------------------

def test_verify_payment_requires_all_fields(client):
    """Missing fields should be rejected."""
    response = client.post("/api/payment/verify", json={"plan_id": "pro"})
    assert response.status_code == 422


def test_verify_payment_invalid_plan(client):
    """Invalid plan in verify should be rejected."""
    response = client.post("/api/payment/verify", json={
        "razorpay_order_id": "order_123",
        "razorpay_payment_id": "pay_123",
        "razorpay_signature": "sig_123",
        "plan_id": "invalid",
    })
    assert response.status_code == 422


def test_verify_payment_simulated_success(client):
    """In test mode without Razorpay, simulated verification should work."""
    response = client.post("/api/payment/verify", json={
        "razorpay_order_id": "order_sim_123",
        "razorpay_payment_id": "pay_sim_123",
        "razorpay_signature": "simulated_signature",
        "plan_id": "pro",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["plan"] == "pro"


# ---------------------------------------------------------------------------
# POST /api/payment/webhook
# ---------------------------------------------------------------------------

def test_webhook_payment_captured(client):
    """Webhook for payment.captured should return ok."""
    payload = {
        "event": "payment.captured",
        "account_id": "acc_123",
        "payload": {
            "payment": {"entity": {"id": "pay_test_001"}}
        },
    }
    response = client.post("/api/payment/webhook", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_webhook_idempotency_guard(client):
    """Replaying the same event_id should return duplicate=True (Security Fix 1.2)."""
    # Clear the processed events first
    from routers.payment import _processed_webhook_events
    _processed_webhook_events.clear()

    payload = {
        "event": "payment.captured",
        "account_id": "acc_idempotency",
        "payload": {
            "payment": {"entity": {"id": "pay_idem_001"}}
        },
    }

    # First call — should process normally
    r1 = client.post("/api/payment/webhook", json=payload)
    assert r1.status_code == 200
    assert r1.json().get("duplicate") is not True

    # Second call — same event_id — should be flagged as duplicate
    r2 = client.post("/api/payment/webhook", json=payload)
    assert r2.status_code == 200
    assert r2.json()["duplicate"] is True


def test_webhook_invalid_signature(client):
    """Invalid webhook signature should return 401."""
    # Set a webhook secret temporarily
    original = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")
    os.environ["RAZORPAY_WEBHOOK_SECRET"] = "test_webhook_secret"

    try:
        response = client.post(
            "/api/payment/webhook",
            json={"event": "payment.captured"},
            headers={"X-Razorpay-Signature": "invalid_signature"},
        )
        assert response.status_code == 401
    finally:
        if original:
            os.environ["RAZORPAY_WEBHOOK_SECRET"] = original
        else:
            os.environ.pop("RAZORPAY_WEBHOOK_SECRET", None)


def test_webhook_subscription_cancelled(client):
    """subscription.cancelled event should be processed without error."""
    payload = {
        "event": "subscription.cancelled",
        "account_id": "acc_cancel",
        "payload": {
            "subscription": {"entity": {"id": "sub_cancel_001"}}
        },
    }
    # Clear idempotency set for fresh test
    from routers.payment import _processed_webhook_events
    _processed_webhook_events.discard("acc_cancel:subscription.cancelled:sub_cancel_001")

    response = client.post("/api/payment/webhook", json=payload)
    assert response.status_code == 200


# ---------------------------------------------------------------------------
# GET /api/payment/status
# ---------------------------------------------------------------------------

def test_payment_status_free_user(client):
    """Unauthenticated/free user should return free tier."""
    response = client.get("/api/payment/status")
    assert response.status_code == 200
    data = response.json()
    assert data["tier"] == "free"
    assert data["active"] is True


def test_payment_status_returns_correct_fields(client):
    """Status response should include tier, status, expires, active."""
    response = client.get("/api/payment/status")
    data = response.json()
    assert "tier" in data
    assert "status" in data
    assert "active" in data
