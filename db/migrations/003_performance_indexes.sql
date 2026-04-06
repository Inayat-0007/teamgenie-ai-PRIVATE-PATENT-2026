-- =============================================================================
-- Migration 003: Performance Indexes (Sprint 2, Fix 2.4)
-- 
-- Adds indexes on frequently queried columns to improve
-- paginated team history, subscription lookups, and payment queries.
-- Expected: 10-100x improvement on paginated team history queries.
-- =============================================================================

-- Teams table: frequently filtered by match_id and user_id
CREATE INDEX IF NOT EXISTS idx_teams_match_id ON teams(match_id);
CREATE INDEX IF NOT EXISTS idx_teams_user_id ON teams(user_id);
CREATE INDEX IF NOT EXISTS idx_teams_match_created ON teams(match_id, created_at);

-- Subscriptions: looked up by user_id on every tier check
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);

-- Payment history: queried for transaction records
CREATE INDEX IF NOT EXISTS idx_payment_history_user_id ON payment_history(user_id);

-- Daily usage: checked on every team generation request
CREATE INDEX IF NOT EXISTS idx_daily_usage_user_date ON daily_usage(user_id, usage_date);

-- Intelligence cache: queried by match_id during team generation
CREATE INDEX IF NOT EXISTS idx_intelligence_match ON intelligence_cache(match_id);
