-- Migration 004: Admin Support and Role-Based Access Control
-- Adds role column and initializes first admin

ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user' CHECK(role IN ('user','admin','moderator'));

-- Initialize demo user as admin if it exists
UPDATE users SET role = 'admin' WHERE id = 'demo' OR email = 'demo@teamgenie.app';

-- Index for role lookups
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
