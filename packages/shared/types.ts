/**
 * TeamGenie AI — Shared TypeScript Types
 * Used across web, mobile, and packages.
 */

// --- Player ---
export interface Player {
  id: string;
  name: string;
  team: string;
  role: 'batsman' | 'bowler' | 'all_rounder' | 'wicket_keeper';
  currentPrice: number;
  predictedPoints: number;
  confidence: number;
  ownershipPct: number;
  formTrend: 'improving' | 'stable' | 'declining';
}

// --- Team ---
export interface GeneratedTeam {
  players: Player[];
  captain: string;
  viceCaptain: string;
  totalCost: number;
  predictedTotal: number;
  riskScore: number;
}

export interface TeamReasoning {
  budgetAgent: string;
  differentialAgent: string;
  riskAgent: string;
}

export interface TeamGenerationResult {
  team: GeneratedTeam;
  reasoning: TeamReasoning;
  generationTimeMs: number;
  cached: boolean;
  modelVersion: string;
}

// --- Match ---
export interface Match {
  id: string;
  teamA: string;
  teamB: string;
  venue: string;
  matchDate: string;
  matchType: 'T20' | 'ODI' | 'Test' | 'T10';
  status: 'scheduled' | 'live' | 'completed' | 'abandoned';
}

// --- User ---
export interface User {
  id: string;
  email: string;
  fullName?: string;
  username?: string;
  tier: 'free' | 'per_match' | 'monthly' | 'api';
  stats: UserStats;
}

export interface UserStats {
  teamsGenerated: number;
  accuracy: number;
  totalWinnings: number;
  winRate: number;
}

// --- API Response ---
export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
  requestId?: string;
}

export interface ApiResponse<T> {
  data?: T;
  error?: ApiError;
}

// --- Subscription ---
export type SubscriptionPlan = 'free' | 'per_match' | 'monthly' | 'annual' | 'api';

export interface Subscription {
  plan: SubscriptionPlan;
  amount: number;
  currency: string;
  status: 'active' | 'canceled' | 'past_due';
  currentPeriodEnd: string;
}
