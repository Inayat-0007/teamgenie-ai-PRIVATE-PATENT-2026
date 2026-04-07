"""
Pydantic models for Player, Team, Match, and User entities.
Strict validation with enums for domain safety.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator


class PlayerRole(StrEnum):
    """Valid cricket player roles."""

    BATSMAN = "batsman"
    BOWLER = "bowler"
    ALL_ROUNDER = "all_rounder"
    WICKET_KEEPER = "wicket_keeper"


class MatchType(StrEnum):
    """Valid cricket match formats."""

    T20 = "T20"
    ODI = "ODI"
    TEST = "Test"
    T10 = "T10"


class MatchStatus(StrEnum):
    """Match lifecycle status."""

    SCHEDULED = "scheduled"
    LIVE = "live"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class UserTier(StrEnum):
    """Subscription tiers."""

    FREE = "free"
    PER_MATCH = "per_match"
    MONTHLY = "monthly"
    API = "api"


class RiskLevel(StrEnum):
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
    batting_style: str | None = None
    bowling_style: str | None = None
    career_average: float = Field(default=0.0, ge=0)
    strike_rate: float = Field(default=0.0, ge=0)
    is_active: bool = True


class TeamModel(BaseModel):
    """Generated team with exactly 11 players."""

    id: str
    user_id: str
    match_id: str
    players: list[str] = Field(min_length=11, max_length=11, description="Exactly 11 player IDs")
    captain_id: str
    vice_captain_id: str
    total_cost: float = Field(le=100, description="Must be within ₹100 budget")
    risk_score: float = Field(ge=0, le=1, default=0.5)
    predicted_points: float | None = None
    actual_points: float | None = None

    @model_validator(mode="after")
    def validate_team_integrity(self) -> TeamModel:
        """Cross-field validation that requires access to multiple fields."""
        # Captain and Vice-Captain must be different
        if self.captain_id == self.vice_captain_id:
            raise ValueError("Captain and vice-captain must be different players")

        # Captain must be in the team
        if self.captain_id not in self.players:
            raise ValueError(f"Captain '{self.captain_id}' must be in the players list")

        # Vice-Captain must be in the team
        if self.vice_captain_id not in self.players:
            raise ValueError(f"Vice-captain '{self.vice_captain_id}' must be in the players list")

        # Players list must have unique IDs
        if len(set(self.players)) != len(self.players):
            raise ValueError("Player IDs must be unique — no duplicate selections allowed")

        return self


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
        if "team_a" in info.data and v == info.data["team_a"]:
            raise ValueError("team_a and team_b must be different")
        return v


class UserModel(BaseModel):
    """User profile entity."""

    id: str
    email: str
    username: str | None = None
    full_name: str | None = None
    tier: UserTier = UserTier.FREE
    teams_created: int = Field(default=0, ge=0)
    accuracy_rate: float = Field(default=0.0, ge=0, le=100)
