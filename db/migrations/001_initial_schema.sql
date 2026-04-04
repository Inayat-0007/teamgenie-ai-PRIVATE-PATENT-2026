-- TeamGenie AI — Initial Database Schema (Turso/LibSQL)
-- Migration 001: Core tables

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE,
    full_name TEXT,
    tier TEXT DEFAULT 'free' CHECK(tier IN ('free','per_match','monthly','api')),
    preferences JSON DEFAULT '{}',
    favorite_players JSON DEFAULT '[]',
    risk_profile TEXT DEFAULT 'balanced',
    teams_created INTEGER DEFAULT 0,
    total_winnings INTEGER DEFAULT 0,
    accuracy_rate REAL DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login_at DATETIME,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS players (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    team TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('batsman','bowler','all_rounder','wicket_keeper')),
    current_price REAL NOT NULL,
    recent_form JSON DEFAULT '[]',
    career_average REAL DEFAULT 0.0,
    strike_rate REAL DEFAULT 0.0,
    country TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS matches (
    id TEXT PRIMARY KEY,
    team_a TEXT NOT NULL,
    team_b TEXT NOT NULL,
    venue TEXT NOT NULL,
    match_date DATETIME NOT NULL,
    match_type TEXT CHECK(match_type IN ('T20','ODI','Test','T10')),
    series_name TEXT,
    status TEXT DEFAULT 'scheduled' CHECK(status IN ('scheduled','live','completed','abandoned')),
    toss_winner TEXT,
    toss_decision TEXT,
    team_a_xi JSON DEFAULT '[]',
    team_b_xi JSON DEFAULT '[]',
    weather JSON DEFAULT '{}',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT different_teams CHECK(team_a != team_b)
);

CREATE TABLE IF NOT EXISTS teams (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT NOT NULL,
    match_id TEXT NOT NULL,
    players JSON NOT NULL,
    captain_id TEXT NOT NULL,
    vice_captain_id TEXT NOT NULL,
    total_cost REAL NOT NULL,
    risk_score REAL DEFAULT 0.5,
    predicted_points REAL,
    actual_points REAL,
    ai_reasoning JSON DEFAULT '{}',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS predictions (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    player_id TEXT NOT NULL,
    match_id TEXT NOT NULL,
    predicted_points REAL NOT NULL,
    confidence REAL NOT NULL,
    actual_points REAL,
    model_version TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES players(id),
    FOREIGN KEY (match_id) REFERENCES matches(id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_players_team ON players(team);
CREATE INDEX IF NOT EXISTS idx_players_role ON players(role);
CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date);
CREATE INDEX IF NOT EXISTS idx_matches_status ON matches(status);
CREATE INDEX IF NOT EXISTS idx_teams_user ON teams(user_id);
CREATE INDEX IF NOT EXISTS idx_teams_match ON teams(match_id);
CREATE INDEX IF NOT EXISTS idx_predictions_player ON predictions(player_id);
CREATE INDEX IF NOT EXISTS idx_predictions_match ON predictions(match_id);
