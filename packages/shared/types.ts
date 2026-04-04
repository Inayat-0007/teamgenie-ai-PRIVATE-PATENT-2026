/**
 * TeamGenie AI — Shared TypeScript Types
 * Used across web, mobile, and packages.
 * Single source of truth for all entity shapes.
 */

// --- Enums (re-usable union types) ---
export type PlayerRole = 'batsman' | 'bowler' | 'all_rounder' | 'wicket_keeper';
export type MatchType = 'T20' | 'ODI' | 'Test' | 'T10';
export type MatchStatus = 'scheduled' | 'live' | 'completed' | 'abandoned';
export type UserTier = 'free' | 'per_match' | 'monthly' | 'api';
export type RiskLevel = 'safe' | 'balanced' | 'aggressive';
export type FormTrend = 'improving' | 'stable' | 'declining';

// --- Player ---
export interface Player {
  readonly id: string;
  readonly name: string;
  readonly team: string;
  readonly role: PlayerRole;
  readonly currentPrice: number;
  readonly predictedPoints: number;
  readonly confidence: number;
  readonly ownershipPct: number;
  readonly formTrend: FormTrend;
  readonly isCaptain?: boolean;
  readonly isViceCaptain?: boolean;
}

// --- Team ---
export interface GeneratedTeam {
  readonly players: readonly Player[];
  readonly captain: string;
  readonly viceCaptain: string;
  readonly totalCost: number;
  readonly predictedTotal: number;
  readonly riskScore: number;
}

export interface TeamReasoning {
  readonly budgetAgent: string;
  readonly differentialAgent: string;
  readonly riskAgent: string;
}

export interface TeamGenerationResult {
  readonly team: GeneratedTeam;
  readonly reasoning: TeamReasoning;
  readonly generationTimeMs: number;
  readonly cached: boolean;
  readonly modelVersion: string;
}

// --- Team Generation Request ---
export interface TeamGenerateRequest {
  readonly matchId: string;
  readonly budget?: number;
  readonly riskLevel?: RiskLevel;
  readonly userPreferences?: UserPreferences;
}

export interface UserPreferences {
  readonly favoritePlayers?: readonly string[];
  readonly avoidPlayers?: readonly string[];
}

// --- Match ---
export interface Match {
  readonly id: string;
  readonly teamA: string;
  readonly teamB: string;
  readonly venue: string;
  readonly matchDate: string;
  readonly matchType: MatchType;
  readonly status: MatchStatus;
  readonly seriesName?: string;
}

// --- User ---
export interface User {
  readonly id: string;
  readonly email: string;
  readonly fullName?: string;
  readonly username?: string;
  readonly tier: UserTier;
  readonly stats: UserStats;
  readonly createdAt?: string;
}

export interface UserStats {
  readonly teamsGenerated: number;
  readonly accuracy: number;
  readonly totalWinnings: number;
  readonly winRate: number;
}

// --- API Response ---
export interface ApiError {
  readonly code: string;
  readonly message: string;
  readonly details?: Readonly<Record<string, unknown>>;
  readonly requestId?: string;
}

export interface ApiResponse<T> {
  readonly data?: T;
  readonly error?: ApiError;
  readonly meta?: ApiMeta;
}

export interface ApiMeta {
  readonly requestId: string;
  readonly responseTimeMs: number;
  readonly cached: boolean;
}

// --- Pagination ---
export interface PaginatedResponse<T> {
  readonly items: readonly T[];
  readonly pagination: Pagination;
}

export interface Pagination {
  readonly page: number;
  readonly limit: number;
  readonly total: number;
  readonly totalPages: number;
}

// --- Subscription ---
export type SubscriptionPlan = 'free' | 'per_match' | 'monthly' | 'annual' | 'api';
export type SubscriptionStatus = 'active' | 'canceled' | 'past_due' | 'trialing';

export interface Subscription {
  readonly plan: SubscriptionPlan;
  readonly amount: number;
  readonly currency: string;
  readonly status: SubscriptionStatus;
  readonly currentPeriodEnd: string;
}

// --- WebSocket ---
export interface WSMessage<T = unknown> {
  readonly type: 'score_update' | 'player_update' | 'match_status' | 'heartbeat';
  readonly payload: T;
  readonly timestamp: number;
}

// --- Live Score ---
export interface LiveScore {
  readonly matchId: string;
  readonly teamAScore: string;
  readonly teamBScore: string;
  readonly overs: string;
  readonly currentBatsman?: string;
  readonly currentBowler?: string;
  readonly lastUpdated: string;
}
