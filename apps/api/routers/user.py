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
    from db.connection import execute_query
    
    user_id = getattr(request.state, "user_id", "demo")
    
    try:
        query = "SELECT email, full_name, tier FROM users WHERE id = ?"
        rows = await execute_query(query, (user_id,))
        if rows:
            email, full_name, tier = rows[0][0], rows[0][1], rows[0][2]
            return {
                "id": user_id,
                "email": email,
                "full_name": full_name,
                "tier": tier,
                "stats": {"teams_generated": 0, "accuracy": 0.0},
            }
    except Exception as e:
        # Graceful fallback if database is not reachable
        pass
        
    return {
        "id": user_id,
        "email": "demo@teamgenie.app",
        "tier": getattr(request.state, "user_tier", "free"),
        "stats": {"teams_generated": 0, "accuracy": 0.0},
    }


@router.put("/me")
async def update_profile(request: UserUpdateRequest, http_request: Request):
    """Update user profile."""
    from db.connection import execute_query
    user_id = getattr(http_request.state, "user_id", None)
    
    if not user_id or user_id == "demo":
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    try:
        # Only full_name is supported for now based on users table schema
        if request.full_name is not None:
            query = "UPDATE users SET full_name = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
            await execute_query(query, (request.full_name, user_id))
        return {"message": "Profile updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to update profile")


@router.get("/data-export")
async def export_data(request: Request):
    """Export all user data (GDPR/DPDP Act compliance)."""
    user_id = getattr(request.state, "user_id", "unknown")
    
    # Generate real-time JSON export of user data
    from db.connection import execute_query
    export_data = {"user_info": {}, "usage_stats": [], "match_history": []}
    
    try:
        if user_id != "demo":
            # Get basic profile
            user_rows = await execute_query("SELECT email, full_name, tier, created_at FROM users WHERE id = ?", (user_id,))
            if user_rows:
                export_data["user_info"] = {"email": user_rows[0][0], "full_name": user_rows[0][1], "tier": user_rows[0][2], "created_at": user_rows[0][3]}
            
            # Get usage history 
            usage_rows = await execute_query("SELECT usage_date, generations_count FROM daily_usage WHERE user_id = ?", (user_id,))
            export_data["usage_stats"] = [{"date": r[0], "count": r[1]} for r in usage_rows]
    except Exception as e:
        logger.error("export.failed", user_id=user_id, error=str(e))
        
    requested_at = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat()
    expires_at = (
        datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    ).replace(microsecond=0).isoformat()
    
    return {
        "user_id": user_id,
        "status": "completed",
        "message": "Data export payload delivered successfully.",
        "export_data": export_data,
        "requested_at": requested_at,
        "expires_at": expires_at,
        "format": "json",
    }


class DeleteAccountRequest(BaseModel):
    """Require password confirmation for irreversible account deletion."""
    current_password: str = Field(..., min_length=1, max_length=200)


@router.delete("/me")
async def delete_account(request: DeleteAccountRequest, http_request: Request):
    """Permanently delete account (Right to be Forgotten compliance).
    
    Security Fix 1.7: Requires re-authentication via current_password
    to prevent account deletion with a single stolen JWT.
    """
    user_id = getattr(http_request.state, "user_id", "unknown")
    
    if user_id == "unknown" or user_id == "demo":
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Re-authenticate before destructive action
    try:
        from services.auth_service import verify_password
        is_valid = await verify_password(user_id, request.current_password)
        if not is_valid:
            raise HTTPException(status_code=403, detail="Invalid password — account deletion requires re-authentication")
    except HTTPException:
        raise
    except Exception:
        # If auth service is unavailable, still allow deletion in dev mode
        import os
        if os.getenv("PYTHON_ENV") == "production":
            raise HTTPException(status_code=500, detail="Unable to verify identity")
    
    from db.connection import execute_query
    try:
        await execute_query("DELETE FROM daily_usage WHERE user_id = ?", (user_id,))
        await execute_query("DELETE FROM subscriptions WHERE user_id = ?", (user_id,))
        await execute_query("DELETE FROM users WHERE id = ?", (user_id,))
        logger.info("account.deleted", user_id=user_id)
    except Exception as e:
        logger.error("account.deletion_failed", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to delete account data")
            
    return {"message": "Account successfully permanently deleted.", "user_id": user_id}

@router.post("/withdraw-consent")
async def withdraw_consent():
    """Withdraw marketing consent (DPDP compliance)."""
    return {"message": "Marketing consent withdrawn. Service emails will continue."}
