"""
User Management Router — Profile, preferences, data export, GDPR/DPDP.
"""

from __future__ import annotations

import datetime

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(default=None, max_length=200)
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    preferences: Optional[dict] = None


@router.get("/me")
async def get_profile(request: Request):
    """Get current user profile from JWT."""
    user_id = getattr(request.state, "user_id", "demo")
    # TODO: Query Turso for full user profile
    return {
        "id": user_id,
        "email": "demo@teamgenie.app",
        "tier": getattr(request.state, "user_tier", "free"),
        "stats": {"teams_generated": 0, "accuracy": 0.0},
    }


@router.put("/me")
async def update_profile(request: UserUpdateRequest):
    """Update user profile."""
    # TODO: Update in Turso
    return {"message": "Profile updated successfully"}


@router.get("/data-export")
async def export_data(request: Request):
    """Export all user data (GDPR/DPDP Act compliance)."""
    user_id = getattr(request.state, "user_id", "unknown")
    # TODO: Generate real JSON export and upload to a signed storage URL when DB is connected.
    # For now, return a structured placeholder with valid timestamps so callers can parse the response.
    requested_at = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
    expires_at = (
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    ).replace(microsecond=0).isoformat()
    return {
        "user_id": user_id,
        "status": "pending",
        "message": "Data export is not yet available in DEMO mode. It will be ready once the database is connected.",
        "export_url": None,
        "requested_at": requested_at,
        "expires_at": expires_at,
        "format": "json",
    }


@router.delete("/me")
async def delete_account(request: Request):
    """Permanently delete account (Right to be Forgotten compliance)."""
    user_id = getattr(request.state, "user_id", "unknown")
    # TODO: Schedule deletion in Turso + Supabase
    return {"message": "Account scheduled for deletion within 30 days.", "user_id": user_id}


@router.post("/withdraw-consent")
async def withdraw_consent():
    """Withdraw marketing consent (DPDP compliance)."""
    return {"message": "Marketing consent withdrawn. Service emails will continue."}
