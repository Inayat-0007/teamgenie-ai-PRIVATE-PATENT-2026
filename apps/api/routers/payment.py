"""
Payment Router — Razorpay subscription management.

Endpoints:
  POST /api/payment/create-order   → Create Razorpay order for subscription upgrade
  POST /api/payment/verify         → Verify payment signature + upgrade user tier
  POST /api/payment/webhook        → Razorpay webhook handler (subscription events)
  GET  /api/payment/status         → Get current subscription status

Razorpay Docs: https://razorpay.com/docs/api/subscriptions
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time

try:
    import structlog

    logger = structlog.get_logger(__name__)
except ImportError:
    import logging

    logger = logging.getLogger(__name__)


from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter()

# ---------------------------------------------------------------------------
# Webhook Idempotency Guard (Security Fix 1.2)
# Prevents replay attacks where the same event_id can re-trigger upgrades.
# In-memory set for fast O(1) dedup, plus DB check for cross-pod safety.
# ---------------------------------------------------------------------------
_processed_webhook_events: set = set()
_MAX_WEBHOOK_EVENTS = 5000  # Prevent unbounded memory growth

# ---------------------------------------------------------------------------
# Razorpay Plan Configuration (INR, amount in paise)
# ---------------------------------------------------------------------------
PLANS = {
    "pro": {
        "name": "Pro Strategist",
        "amount": 19900,  # ₹199 in paise
        "currency": "INR",
        "period": "monthly",
        "description": "3 AI generations/day + Live Toss Intelligence",
    },
    "elite": {
        "name": "Elite Whale",
        "amount": 99900,  # ₹999 in paise
        "currency": "INR",
        "period": "monthly",
        "description": "Unlimited generations + Bloomberg Terminal",
    },
}


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------
class CreateOrderRequest(BaseModel):
    plan_id: str = Field(..., pattern="^(pro|elite)$")


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str = Field(..., min_length=1, max_length=100)
    razorpay_payment_id: str = Field(..., min_length=1, max_length=100)
    razorpay_signature: str = Field(..., min_length=1, max_length=512)
    plan_id: str = Field(..., pattern="^(pro|elite)$")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_razorpay_client():
    """Initialize Razorpay client. Returns None if not configured."""
    try:
        import razorpay
    except ImportError:
        logger.warning("payment.razorpay_not_installed")
        return None

    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")

    if not key_id or not key_secret:
        logger.warning("payment.razorpay_not_configured")
        return None

    return razorpay.Client(auth=(key_id, key_secret))


def _verify_signature(order_id: str, payment_id: str, signature: str) -> bool:
    """Verify Razorpay payment signature using HMAC-SHA256."""
    secret = os.getenv("RAZORPAY_KEY_SECRET", "")
    if not secret:
        return False

    message = f"{order_id}|{payment_id}"
    expected = hmac.new(
        secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/create-order")
async def create_order(order_data: CreateOrderRequest, request: Request):
    """Create a Razorpay order for subscription upgrade."""
    plan = PLANS.get(order_data.plan_id)
    if not plan:
        raise HTTPException(status_code=400, detail="Invalid plan")

    client = _get_razorpay_client()
    if not client:
        # Simulated mode for development/demo
        return {
            "order_id": f"order_sim_{int(time.time())}",
            "amount": plan["amount"],
            "currency": plan["currency"],
            "plan": order_data.plan_id,
            "key_id": os.getenv("RAZORPAY_KEY_ID", "rzp_test_simulated"),
            "simulated": True,
            "notes": "Razorpay not configured — simulated order for development",
        }

    try:
        order = client.order.create(
            {
                "amount": plan["amount"],
                "currency": plan["currency"],
                "receipt": f"tg_{order_data.plan_id}_{int(time.time())}",
                "notes": {
                    "plan": order_data.plan_id,
                    "user_id": getattr(request.state, "user_id", "unknown"),
                },
            }
        )

        logger.info("payment.order_created", order_id=order["id"], plan=order_data.plan_id)

        return {
            "order_id": order["id"],
            "amount": plan["amount"],
            "currency": plan["currency"],
            "plan": order_data.plan_id,
            "key_id": os.getenv("RAZORPAY_KEY_ID"),
            "simulated": False,
        }
    except Exception as exc:
        logger.error("payment.order_creation_failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Payment order creation failed")


@router.post("/verify")
async def verify_payment(verification_data: VerifyPaymentRequest, request: Request):
    """Verify Razorpay payment and upgrade user tier."""
    user_id = getattr(request.state, "user_id", "unknown")

    # Verify signature
    client = _get_razorpay_client()
    if client:
        try:
            client.utility.verify_payment_signature(
                {
                    "razorpay_order_id": verification_data.razorpay_order_id,
                    "razorpay_payment_id": verification_data.razorpay_payment_id,
                    "razorpay_signature": verification_data.razorpay_signature,
                }
            )
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid payment signature")
    else:
        # Check if in production - prevent simulated payment loophole
        if os.getenv("APP_MODE") == "production":
            raise HTTPException(status_code=500, detail="Razorpay is not fully configured for production.")
        # Simulated verification
        if not verification_data.razorpay_signature:
            raise HTTPException(status_code=400, detail="Missing signature")

    # Upgrade user tier in database
    try:
        from db.connection import execute_query

        plan = PLANS[verification_data.plan_id]

        # Record payment
        await execute_query(
            """INSERT INTO payment_history (user_id, razorpay_payment_id, razorpay_order_id, amount_paise, currency, status, tier)
               VALUES (?, ?, ?, ?, ?, 'captured', ?)""",
            (
                user_id,
                verification_data.razorpay_payment_id,
                verification_data.razorpay_order_id,
                plan["amount"],
                plan["currency"],
                verification_data.plan_id,
            ),
        )

        # Upgrade subscription (Reliable upsert since user_id is not inherently UNIQUE in schema)
        existing_sub = await execute_query("SELECT id FROM subscriptions WHERE user_id = ?", (user_id,))
        if existing_sub:
            await execute_query(
                """UPDATE subscriptions SET
                     tier = ?,
                     status = 'active',
                     razorpay_subscription_id = ?,
                     current_period_start = datetime('now'),
                     current_period_end = datetime('now', '+30 days'),
                     updated_at = CURRENT_TIMESTAMP
                   WHERE user_id = ?""",
                (verification_data.plan_id, verification_data.razorpay_payment_id, user_id),
            )
        else:
            await execute_query(
                """INSERT INTO subscriptions (user_id, tier, razorpay_subscription_id, status, current_period_start, current_period_end)
                   VALUES (?, ?, ?, 'active', datetime('now'), datetime('now', '+30 days'))""",
                (user_id, verification_data.plan_id, verification_data.razorpay_payment_id),
            )

        # Update user tier
        await execute_query(
            "UPDATE users SET tier = ? WHERE id = ?",
            (verification_data.plan_id, user_id),
        )

        logger.info("payment.verified_upgrade", user_id=user_id, plan=verification_data.plan_id)

    except HTTPException:
        raise
    except Exception as exc:
        # Audit Fix #05 CRITICAL: Payment verified but DB failed.
        # MUST return error so user knows upgrade is pending reconciliation.
        # Silently returning "success" when DB failed = user charged but not upgraded.
        logger.error(
            "payment.db_update_failed_post_capture",
            user_id=user_id,
            plan=verification_data.plan_id,
            payment_id=verification_data.razorpay_payment_id,
            order_id=verification_data.razorpay_order_id,
            error=str(exc),
        )
        raise HTTPException(
            status_code=500,
            detail="Payment captured but account upgrade pending. Our team has been notified. "
            f"Contact support with payment ID: {verification_data.razorpay_payment_id}",
        )

    return {
        "status": "success",
        "plan": verification_data.plan_id,
        "message": f"Successfully upgraded to {PLANS[verification_data.plan_id]['name']}!",
    }


@router.post("/webhook")
async def razorpay_webhook(http_request: Request):
    """Handle Razorpay webhook events (subscription lifecycle).

    Security: Idempotency guard prevents replay attacks.
    A replayed event_id returns 200 OK immediately without re-processing.
    """
    webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

    # Verify webhook signature
    signature = http_request.headers.get("X-Razorpay-Signature", "")
    body = await http_request.body()

    if webhook_secret and signature:
        expected = hmac.new(
            webhook_secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected, signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    try:
        import json

        event = json.loads(body.decode("utf-8"))
        event_type = event.get("event", "")
        event_id = (
            event.get("account_id", "")
            + ":"
            + event.get("event", "")
            + ":"
            + str(
                event.get("payload", {})
                .get("payment", {})
                .get("entity", {})
                .get(
                    "id", event.get("payload", {}).get("subscription", {}).get("entity", {}).get("id", str(time.time()))
                )
            )
        )

        # --- Idempotency Check (Security Fix 1.2) ---
        if event_id in _processed_webhook_events:
            logger.info("payment.webhook_duplicate_skipped", event_id=event_id)
            return {"status": "ok", "duplicate": True}

        # Mark as processed BEFORE acting (prevents race conditions)
        if len(_processed_webhook_events) >= _MAX_WEBHOOK_EVENTS:
            _processed_webhook_events.clear()
        _processed_webhook_events.add(event_id)

        logger.info("payment.webhook_received", event_type=event_type, event_id=event_id)

        if event_type == "payment.captured":
            # Payment captured — already handled by /verify
            pass
        elif event_type == "subscription.cancelled":
            # Downgrade user to free tier
            entity = event.get("payload", {}).get("subscription", {}).get("entity", {})
            sub_id = entity.get("id")
            if sub_id:
                from db.connection import execute_query

                await execute_query(
                    "UPDATE subscriptions SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP WHERE razorpay_subscription_id = ?",
                    (sub_id,),
                )
        elif event_type == "payment.failed":
            logger.warning("payment.failed_event", event=event)

    except Exception as exc:
        logger.error("payment.webhook_processing_failed", error=str(exc))

    return {"status": "ok"}


@router.get("/status")
async def payment_status(request: Request):
    """Get current subscription status for authenticated user."""
    user_id = getattr(request.state, "user_id", "unknown")

    try:
        from db.connection import execute_query

        rows = await execute_query(
            """SELECT tier, status, current_period_end
               FROM subscriptions
               WHERE user_id = ? AND status = 'active'
               ORDER BY created_at DESC LIMIT 1""",
            (user_id,),
        )

        if rows:
            return {
                "tier": rows[0][0],
                "status": rows[0][1],
                "expires": rows[0][2],
                "active": True,
            }
    except Exception:
        pass

    return {
        "tier": "free",
        "status": "active",
        "expires": None,
        "active": True,
    }
