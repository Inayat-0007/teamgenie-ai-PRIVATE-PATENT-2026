"""
Pydantic models for Player, Team, Match, and User entities.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class PlayerModel(BaseModel):
    id: str
    name: str
    team: str
    role: str  # batsman, bowler, all_rounder, wicket_keeper
    current_price: float
    batting_style: Optional[str] = None
    bowling_style: Optional[str] = None
    career_average: float = 0.0
    strike_rate: float = 0.0
    is_active: bool = True


class TeamModel(BaseModel):
    id: str
    user_id: str
    match_id: str
    players: List[str]  # Player IDs
    captain_id: str
    vice_captain_id: str
    total_cost: float = Field(le=100)
    risk_score: float = Field(ge=0, le=1, default=0.5)
    predicted_points: Optional[float] = None
    actual_points: Optional[float] = None


class MatchModel(BaseModel):
    id: str
    team_a: str
    team_b: str
    venue: str
    match_date: datetime
    match_type: str  # T20, ODI, Test
    status: str = "scheduled"  # scheduled, live, completed, abandoned


class UserModel(BaseModel):
    id: str
    email: str
    username: Optional[str] = None
    full_name: Optional[str] = None
    tier: str = "free"  # free, per_match, monthly, api
    teams_created: int = 0
    accuracy_rate: float = 0.0
