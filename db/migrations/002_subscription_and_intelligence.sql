-- TeamGenie AI — Migration 002: Subscription Quota & Intelligence Tables
-- Required for: Payment/subscription enforcement, harvester intelligence storage
-- Author: Mohammed Inayat Hussain Qureshi
-- Date: 2026-04-07

-- =============================================
-- daily_usage: Per-user generation quota tracking
-- Used by: services/subscription_service.py
-- =============================================
CREATE TABLE IF NOT EXISTS daily_usage (
    user_id TEXT NOT NULL,
    usage_date TEXT NOT NULL DEFAULT (date('now')),
    generations_count INTEGER NOT NULL DEFAULT 0 CHECK(generations_count >= 0),
    api_calls INTEGER NOT NULL DEFAULT 0 CHECK(api_calls >= 0),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, usage_date)
);

CREATE INDEX IF NOT EXISTS idx_daily_usage_user ON daily_usage(user_id);
CREATE INDEX IF NOT EXISTS idx_daily_usage_date ON daily_usage(usage_date);

-- =============================================
-- match_intelligence: Harvested intelligence cache
-- Used by: workers/harvester.py
-- =============================================
CREATE TABLE IF NOT EXISTS match_intelligence (
    id TEXT PRIMARY KEY,
    match_id TEXT NOT NULL,
    intel_type TEXT NOT NULL CHECK(intel_type IN ('pitch_report','injuries','weather','news','social')),
    content TEXT NOT NULL,
    source TEXT DEFAULT 'duckduckgo',
    fetched_at TEXT DEFAULT '',
    FOREIGN KEY (match_id) REFERENCES matches(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_intel_match ON match_intelligence(match_id);
CREATE INDEX IF NOT EXISTS idx_intel_type ON match_intelligence(intel_type);
CREATE INDEX IF NOT EXISTS idx_intel_match_type ON match_intelligence(match_id, intel_type);

-- =============================================
-- subscriptions: SaaS tier management
-- Used by: future Razorpay webhook handler
-- =============================================
CREATE TABLE IF NOT EXISTS subscriptions (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT NOT NULL,
    tier TEXT NOT NULL DEFAULT 'free' CHECK(tier IN ('free','pro','elite')),
    razorpay_subscription_id TEXT,
    razorpay_plan_id TEXT,
    status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active','cancelled','past_due','expired')),
    current_period_start DATETIME,
    current_period_end DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_subs_user ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subs_status ON subscriptions(status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_subs_razorpay ON subscriptions(razorpay_subscription_id);

-- =============================================
-- payment_history: Razorpay transaction log
-- =============================================
CREATE TABLE IF NOT EXISTS payment_history (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    user_id TEXT NOT NULL,
    razorpay_payment_id TEXT UNIQUE,
    razorpay_order_id TEXT,
    amount_paise INTEGER NOT NULL CHECK(amount_paise > 0),
    currency TEXT NOT NULL DEFAULT 'INR',
    status TEXT NOT NULL DEFAULT 'created' CHECK(status IN ('created','authorized','captured','refunded','failed')),
    tier TEXT NOT NULL,
    receipt_url TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_payments_user ON payment_history(user_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payment_history(status);

-- =============================================
-- audit_log: Generation audit trail
-- Used by: services/audit_service.py
-- =============================================
CREATE TABLE IF NOT EXISTS audit_log (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
    request_id TEXT NOT NULL,
    user_id TEXT,
    match_id TEXT NOT NULL,
    action TEXT NOT NULL DEFAULT 'team_generation',
    request_data JSON,
    response_summary JSON,
    generation_time_ms INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_match ON audit_log(match_id);
CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_log(created_at);
