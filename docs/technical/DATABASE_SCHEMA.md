# 🗄️ TeamGenie Database Schema

**Version:** 1.0.0 | **Last Updated:** January 2026  
**Databases:** Turso (Primary), Supabase (Auth), Pinecone (Vectors)

---

## Schema Overview

| Database | Purpose | Tables |
|---|---|---|
| **Turso (LibSQL)** | Primary data | users, teams, players, matches, predictions, subscriptions, analytics_events |
| **Supabase (Postgres)** | Auth & realtime | profiles, sessions |
| **Pinecone** | Vector embeddings | player_embeddings, match_context, venue_embeddings |
| **Upstash Redis** | Cache & rate limits | player_stats, team_predictions, rate_limit |

---

## Turso Tables

### users
```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE,
    full_name TEXT,
    tier TEXT DEFAULT 'free' CHECK(tier IN ('free','per_match','monthly','api')),
    subscription_id TEXT,
    subscription_status TEXT CHECK(subscription_status IN ('active','canceled','past_due',NULL)),
    subscription_expires_at DATETIME,
    preferences JSON DEFAULT '{}',
    favorite_players JSON DEFAULT '[]',
    risk_profile TEXT DEFAULT 'balanced' CHECK(risk_profile IN ('safe','balanced','aggressive')),
    teams_created INTEGER DEFAULT 0,
    total_winnings INTEGER DEFAULT 0,
    accuracy_rate REAL DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login_at DATETIME,
    is_active BOOLEAN DEFAULT TRUE,
    CONSTRAINT valid_email CHECK(email LIKE '%@%')
);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_tier ON users(tier);
CREATE INDEX idx_users_created_at ON users(created_at);
```

### players
```sql
CREATE TABLE players (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    team TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('batsman','bowler','all_rounder','wicket_keeper')),
    batting_style TEXT,
    bowling_style TEXT,
    current_price REAL NOT NULL,
    price_trend TEXT DEFAULT 'stable' CHECK(price_trend IN ('rising','stable','falling')),
    recent_form JSON DEFAULT '[]',
    career_average REAL DEFAULT 0.0,
    strike_rate REAL DEFAULT 0.0,
    economy_rate REAL DEFAULT 0.0,
    country TEXT,
    date_of_birth DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_match_at DATETIME
);
CREATE INDEX idx_players_team ON players(team);
CREATE INDEX idx_players_role ON players(role);
CREATE INDEX idx_players_price ON players(current_price);
CREATE UNIQUE INDEX idx_players_name_team ON players(name, team);

-- Full-text search
CREATE VIRTUAL TABLE players_fts USING fts5(id UNINDEXED, name, team, content=players, content_rowid=rowid);
```

### matches
```sql
CREATE TABLE matches (
    id TEXT PRIMARY KEY,
    team_a TEXT NOT NULL,
    team_b TEXT NOT NULL,
    venue TEXT NOT NULL,
    venue_city TEXT,
    venue_country TEXT,
    match_date DATETIME NOT NULL,
    match_type TEXT CHECK(match_type IN ('T20','ODI','Test','T10')),
    series_name TEXT,
    match_number INTEGER,
    status TEXT DEFAULT 'scheduled' CHECK(status IN ('scheduled','live','completed','abandoned')),
    toss_winner TEXT,
    toss_decision TEXT CHECK(toss_decision IN ('bat','bowl',NULL)),
    team_a_xi JSON DEFAULT '[]',
    team_b_xi JSON DEFAULT '[]',
    winner TEXT,
    result_margin TEXT,
    weather JSON DEFAULT '{}',
    pitch_report TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT different_teams CHECK(team_a != team_b)
);
CREATE INDEX idx_matches_date ON matches(match_date);
CREATE INDEX idx_matches_status ON matches(status);
CREATE INDEX idx_matches_teams ON matches(team_a, team_b);
```

### teams
```sql
CREATE TABLE teams (
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
    confidence_score REAL,
    ai_reasoning JSON DEFAULT '{}',
    rank INTEGER,
    winnings REAL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_contest_entry BOOLEAN DEFAULT FALSE,
    contest_id TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE,
    CONSTRAINT valid_cost CHECK(total_cost <= 100),
    CONSTRAINT valid_risk CHECK(risk_score BETWEEN 0 AND 1)
);
CREATE INDEX idx_teams_user ON teams(user_id);
CREATE INDEX idx_teams_match ON teams(match_id);
CREATE INDEX idx_teams_user_match ON teams(user_id, match_id);
```

### predictions
```sql
CREATE TABLE predictions (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    player_id TEXT NOT NULL,
    match_id TEXT NOT NULL,
    predicted_points REAL NOT NULL,
    confidence REAL NOT NULL CHECK(confidence BETWEEN 0 AND 1),
    model_version TEXT,
    model_features JSON DEFAULT '{}',
    actual_points REAL,
    prediction_error REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    evaluated_at DATETIME,
    FOREIGN KEY (player_id) REFERENCES players(id) ON DELETE CASCADE,
    FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE
);
CREATE INDEX idx_predictions_player ON predictions(player_id);
CREATE INDEX idx_predictions_match ON predictions(match_id);
CREATE INDEX idx_predictions_player_match ON predictions(player_id, match_id);
```

### subscriptions
```sql
CREATE TABLE subscriptions (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT NOT NULL UNIQUE,
    plan_type TEXT NOT NULL CHECK(plan_type IN ('per_match','monthly','annual','api')),
    amount REAL NOT NULL,
    currency TEXT DEFAULT 'INR',
    payment_gateway TEXT CHECK(payment_gateway IN ('razorpay','stripe','cashfree')),
    gateway_subscription_id TEXT,
    gateway_customer_id TEXT,
    status TEXT DEFAULT 'active' CHECK(status IN ('active','canceled','past_due','paused')),
    current_period_start DATETIME,
    current_period_end DATETIME,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    canceled_at DATETIME,
    teams_generated_this_period INTEGER DEFAULT 0,
    api_calls_this_period INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE INDEX idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX idx_subscriptions_status ON subscriptions(status);
```

### analytics_events
```sql
CREATE TABLE analytics_events (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT,
    session_id TEXT,
    anonymous_id TEXT,
    event_name TEXT NOT NULL,
    event_properties JSON DEFAULT '{}',
    user_agent TEXT,
    ip_address TEXT,
    country TEXT,
    city TEXT,
    device_type TEXT CHECK(device_type IN ('mobile','desktop','tablet',NULL)),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);
CREATE INDEX idx_events_user ON analytics_events(user_id);
CREATE INDEX idx_events_name ON analytics_events(event_name);
CREATE INDEX idx_events_created_at ON analytics_events(created_at);
```

---

## Supabase Tables

### profiles (extends auth.users)
```sql
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE, username TEXT UNIQUE, full_name TEXT, avatar_url TEXT,
    phone TEXT, phone_verified BOOLEAN DEFAULT FALSE,
    notification_preferences JSONB DEFAULT '{"email":true,"push":true,"sms":false}'::jsonb,
    is_profile_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(), updated_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own profile" ON public.profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON public.profiles FOR UPDATE USING (auth.uid() = id);
```

### sessions
```sql
CREATE TABLE public.sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    device_name TEXT, device_type TEXT, user_agent TEXT, ip_address INET,
    country TEXT, city TEXT,
    refresh_token_hash TEXT UNIQUE, expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(), last_active_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE public.sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own sessions" ON public.sessions FOR SELECT USING (auth.uid() = user_id);
```

---

## Pinecone Vector Schema

```python
# 3 indexes, 384-dimension vectors (all-MiniLM-L6-v2)
# Indexes: player-embeddings, match-context, venue-embeddings
# Metric: cosine similarity
# Vector structure:
{
    "id": "player_virat_kohli_20260115",
    "values": [0.023, -0.145, ...],  # 384 dimensions
    "metadata": {
        "player_id": "virat_kohli",
        "name": "Virat Kohli",
        "team": "India",
        "role": "batsman",
        "price": 10.5,
        "updated_at": "2026-01-15T10:30:00Z"
    }
}
```

---

## Data Retention Policy

| Table | Retention | Auto-Cleanup |
|---|---|---|
| users | Forever | — |
| players | Forever | — |
| matches | 2 years | Monthly cron |
| teams | 1 year | Monthly cron |
| predictions | 1 year | Monthly cron |
| analytics_events | 90 days | Monthly cron |
| sessions | 30 days | Daily cron |

---

## Backup Strategy

- **Turso:** Point-in-time recovery every 5 minutes (built-in), 30-day retention
- **Supabase:** Daily snapshots, 7-day retention (built-in)
- **Pinecone:** Manual export via API, stored in S3
- **Restore:** `turso db restore teamgenie /backups/latest.db`

---

**Maintained By:** Mohammed Inayat Hussain Qureshi | **Next Review:** March 2026
