-- ====================================================================
-- TeamGenie AI - Initial Turso Edge SQLite Database Schema
-- Focus: Performance, User Quotas, Subscription Management, Audit Logs
-- ====================================================================

-- 1. USERS TABLE (Synched partially with Supabase Auth)
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,                       -- Supabase UUID
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    tier TEXT DEFAULT 'free' CHECK(tier IN ('free', 'pro', 'elite')),
    stripe_customer_id TEXT,                   -- Or Razorpay customer ID
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 2. SUBSCRIPTIONS TABLE (Pricing/Payment Webhook state)
CREATE TABLE IF NOT EXISTS subscriptions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    gateway TEXT DEFAULT 'razorpay' CHECK(gateway IN ('razorpay', 'stripe')),
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'canceled', 'past_due')),
    current_period_end DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    cancel_at_period_end BOOLEAN DEFAULT 0
);

-- 3. GENERATION HISTORY (Links AI payload back to User Profile UI History)
CREATE TABLE IF NOT EXISTS generations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    match_id TEXT NOT NULL,
    budget REAL NOT NULL,
    toss_winner TEXT,
    risk_level TEXT DEFAULT 'balanced',
    team_payload JSON NOT NULL,                -- The resulting 11-player squad JSON
    predicted_points REAL,                     -- Total predicted sum
    generation_time_ms INTEGER NOT NULL,       -- Latency benchmarking
    mode TEXT DEFAULT 'live',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 4. QUOTA TRACKING (Deters abuse, enforces Pricing Tiers)
CREATE TABLE IF NOT EXISTS daily_usage (
    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    usage_date DATE NOT NULL,
    generations_count INTEGER DEFAULT 0,
    api_calls INTEGER DEFAULT 0,
    PRIMARY KEY(user_id, usage_date)
);

-- 5. MATCH CACHE (JIT intelligence, scraped pitches/weather)
CREATE TABLE IF NOT EXISTS match_intelligence (
    match_id TEXT PRIMARY KEY,
    weather_data JSON,
    pitch_report TEXT,
    toss_data JSON,
    last_fetched DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for lightning fast queries across millions of rows
CREATE INDEX IF NOT EXISTS idx_generations_user_id ON generations(user_id);
CREATE INDEX IF NOT EXISTS idx_generations_match_id ON generations(match_id);
CREATE INDEX IF NOT EXISTS idx_daily_usage_date ON daily_usage(usage_date);
