"""
Pydantic models for Player, Team, Match, and User entities.
Strict validation with enums for domain safety.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class PlayerRole(str, Enum):
    """Valid cricket player roles."""
    BATSMAN = "batsman"
    BOWLER = "bowler"
    ALL_ROUNDER = "all_rounder"
    WICKET_KEEPER = "wicket_keeper"


class MatchType(str, Enum):
    """Valid cricket match formats."""
    T20 = "T20"
    ODI = "ODI"
    TEST = "Test"
    T10 = "T10"


class MatchStatus(str, Enum):
    """Match lifecycle status."""
    SCHEDULED = "scheduled"
    LIVE = "live"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class UserTier(str, Enum):
    """Subscription tiers."""
    FREE = "free"
    PER_MATCH = "per_match"
    MONTHLY = "monthly"
    API = "api"


class RiskLevel(str, Enum):
    """User risk tolerance for team generation."""
    SAFE = "safe"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


class PlayerModel(BaseModel):
    """Player entity with career statistics."""
    id: str
    name: str = Field(min_length=1, max_length=200)
    team: str = Field(min_length=1, max_length=100)
    role: PlayerRole
    current_price: float = Field(gt=0, le=20, description="Player credit price")
    batting_style: Optional[str] = None
    bowling_style: Optional[str] = None
    career_average: float = Field(default=0.0, ge=0)
    strike_rate: float = Field(default=0.0, ge=0)
    is_active: bool = True


class TeamModel(BaseModel):
    """Generated team with exactly 11 players."""
    id: str
    user_id: str
    match_id: str
    players: List[str] = Field(min_length=11, max_length=11, description="Exactly 11 player IDs")
    captain_id: str
    vice_captain_id: str
    total_cost: float = Field(le=100, description="Must be within ₹100 budget")
    risk_score: float = Field(ge=0, le=1, default=0.5)
    predicted_points: Optional[float] = None
    actual_points: Optional[float] = None

    @field_validator("vice_captain_id")
    @classmethod
    def captain_and_vice_must_differ(cls, v: str, info) -> str:
        if v == info.data.get("captain_id"):
            raise ValueError("Captain and vice-captain must be different players")
        return v


class MatchModel(BaseModel):
    """Cricket match entity."""
    id: str
    team_a: str
    team_b: str
    venue: str
    match_date: datetime
    match_type: MatchType
    status: MatchStatus = MatchStatus.SCHEDULED

    @field_validator("team_b")
    @classmethod
    def teams_must_differ(cls, v: str, info) -> str:
        if v == info.data.get("team_a"):
            raise ValueError("team_a and team_b must be different")
        return v


class UserModel(BaseModel):
    """User profile entity."""
    id: str
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    tier: UserTier = UserTier.FREE
    teams_created: int = Field(default=0, ge=0)
    accuracy_rate: float = Field(default=0.0, ge=0, le=100)
