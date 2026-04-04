/**
 * TeamGenie AI — Shared Constants
 */

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const TEAM_CONSTRAINTS = {
  TOTAL_PLAYERS: 11,
  MAX_BUDGET: 100,
  MIN_BATSMEN: 3,
  MIN_BOWLERS: 3,
  MIN_WICKET_KEEPERS: 1,
  MAX_FROM_ONE_TEAM: 7,
} as const;

export const RISK_LEVELS = ['safe', 'balanced', 'aggressive'] as const;
export type RiskLevel = typeof RISK_LEVELS[number];

export const SUBSCRIPTION_PLANS = {
  FREE: { name: 'Free', price: 0, teamsPerDay: 5 },
  PER_MATCH: { name: 'Per Match', price: 19, teamsPerDay: Infinity },
  MONTHLY: { name: 'Monthly', price: 99, teamsPerDay: Infinity },
  API: { name: 'API Access', price: 499, apiCallsPerMonth: 10000 },
} as const;

export const MATCH_TYPES = ['T20', 'ODI', 'Test', 'T10'] as const;
export const PLAYER_ROLES = ['batsman', 'bowler', 'all_rounder', 'wicket_keeper'] as const;
