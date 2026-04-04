/**
 * TeamGenie AI — Shared Constants
 * Single source of truth for all magic numbers and configuration.
 */

import type { RiskLevel, MatchType, PlayerRole } from './types';

// --- API ---
export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.EXPO_PUBLIC_API_URL ||
  'http://localhost:8000';

export const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL ||
  API_BASE_URL.replace('http', 'ws');

export const API_TIMEOUT_MS = 30_000;
export const API_RETRY_COUNT = 3;

// --- Team Constraints ---
export const TEAM_CONSTRAINTS = {
  TOTAL_PLAYERS: 11,
  MAX_BUDGET: 100,
  MIN_BATSMEN: 3,
  MAX_BATSMEN: 6,
  MIN_BOWLERS: 3,
  MAX_BOWLERS: 6,
  MIN_ALL_ROUNDERS: 1,
  MAX_ALL_ROUNDERS: 4,
  MIN_WICKET_KEEPERS: 1,
  MAX_WICKET_KEEPERS: 4,
  MAX_FROM_ONE_TEAM: 7,
} as const;

// --- Risk Levels ---
export const RISK_LEVELS: readonly RiskLevel[] = ['safe', 'balanced', 'aggressive'] as const;

export const RISK_LEVEL_CONFIG = {
  safe: { label: 'Safe', description: 'Low-variance, high-ownership picks', color: '#22c55e' },
  balanced: { label: 'Balanced', description: 'Mix of safe picks and differentials', color: '#6366f1' },
  aggressive: { label: 'Aggressive', description: 'High differential, high reward', color: '#ef4444' },
} as const satisfies Record<RiskLevel, { label: string; description: string; color: string }>;

// --- Match Types ---
export const MATCH_TYPES: readonly MatchType[] = ['T20', 'ODI', 'Test', 'T10'] as const;

export const MATCH_TYPE_CONFIG = {
  T20: { label: 'T20', overs: 20, duration: '3 hours' },
  ODI: { label: 'ODI', overs: 50, duration: '8 hours' },
  Test: { label: 'Test', overs: null, duration: '5 days' },
  T10: { label: 'T10', overs: 10, duration: '90 mins' },
} as const satisfies Record<MatchType, { label: string; overs: number | null; duration: string }>;

// --- Player Roles ---
export const PLAYER_ROLES: readonly PlayerRole[] = [
  'batsman',
  'bowler',
  'all_rounder',
  'wicket_keeper',
] as const;

export const PLAYER_ROLE_LABELS: Record<PlayerRole, string> = {
  batsman: 'Batsman',
  bowler: 'Bowler',
  all_rounder: 'All-Rounder',
  wicket_keeper: 'Wicket-Keeper',
};

// --- Subscription Plans ---
export const SUBSCRIPTION_PLANS = {
  FREE: { name: 'Free', price: 0, currency: '₹', teamsPerDay: 5, features: ['5 teams/day', 'Basic AI'] },
  PER_MATCH: { name: 'Per Match', price: 19, currency: '₹', teamsPerDay: Infinity, features: ['Unlimited teams', '3 agents', 'Match insights'] },
  MONTHLY: { name: 'Monthly', price: 99, currency: '₹', teamsPerDay: Infinity, features: ['Unlimited teams', '3 agents', 'Priority support', 'RAG insights'] },
  API: { name: 'API Access', price: 499, currency: '₹', apiCallsPerMonth: 10_000, features: ['REST API', '10K calls/month', 'Webhook support'] },
} as const;

// --- HTTP Status Codes ---
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  RATE_LIMITED: 429,
  SERVER_ERROR: 500,
  SERVICE_UNAVAILABLE: 503,
} as const;

// --- Cache TTLs (seconds) ---
export const CACHE_TTL = {
  TEAM_RESULT: 600,       // 10 minutes
  PLAYER_STATS: 3600,     // 1 hour
  MATCH_LIST: 300,        // 5 minutes
  LIVE_SCORE: 15,         // 15 seconds
  USER_PROFILE: 1800,     // 30 minutes
} as const;
