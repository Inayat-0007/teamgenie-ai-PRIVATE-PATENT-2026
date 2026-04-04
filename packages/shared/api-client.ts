/**
 * TeamGenie AI — API Client
 * Type-safe HTTP client for frontend ↔ backend communication.
 */

import type {
  ApiResponse,
  TeamGenerateRequest,
  TeamGenerationResult,
  Player,
  Match,
  User,
  PaginatedResponse,
} from '@teamgenie/shared';
import { API_BASE_URL, API_TIMEOUT_MS, API_RETRY_COUNT } from '@teamgenie/shared';

class ApiClient {
  private baseUrl: string;
  private accessToken: string | null = null;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  setToken(token: string) {
    this.accessToken = token;
  }

  clearToken() {
    this.accessToken = null;
  }

  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${path}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(this.accessToken ? { Authorization: `Bearer ${this.accessToken}` } : {}),
      ...(options.headers as Record<string, string> || {}),
    };

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), API_TIMEOUT_MS);

    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= API_RETRY_COUNT; attempt++) {
      try {
        const response = await fetch(url, {
          ...options,
          headers,
          signal: controller.signal,
        });

        clearTimeout(timeout);

        if (!response.ok) {
          const error = await response.json().catch(() => ({
            code: 'unknown',
            message: response.statusText,
          }));
          return { error };
        }

        const data = await response.json();
        return { data };
      } catch (err) {
        lastError = err as Error;
        if (attempt < API_RETRY_COUNT) {
          await new Promise((r) => setTimeout(r, 1000 * attempt)); // Exponential backoff
        }
      }
    }

    clearTimeout(timeout);
    return {
      error: {
        code: 'network_error',
        message: lastError?.message || 'Network request failed',
      },
    };
  }

  // --- Team Generation ---
  async generateTeam(request: TeamGenerateRequest): Promise<ApiResponse<TeamGenerationResult>> {
    return this.request('/api/team/generate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getTeamHistory(page = 1, limit = 20): Promise<ApiResponse<PaginatedResponse<any>>> {
    return this.request(`/api/team/history?page=${page}&limit=${limit}`);
  }

  // --- Players ---
  async searchPlayers(query: string, role?: string): Promise<ApiResponse<PaginatedResponse<Player>>> {
    const params = new URLSearchParams({ q: query });
    if (role) params.set('role', role);
    return this.request(`/api/player/search?${params}`);
  }

  async getPlayerInsights(playerId: string, matchId?: string): Promise<ApiResponse<any>> {
    const params = matchId ? `?match_id=${matchId}` : '';
    return this.request(`/api/player/${playerId}/insights${params}`);
  }

  // --- Matches ---
  async getUpcomingMatches(limit = 10): Promise<ApiResponse<{ matches: Match[] }>> {
    return this.request(`/api/match/upcoming?limit=${limit}`);
  }

  async getMatch(matchId: string): Promise<ApiResponse<{ match: Match }>> {
    return this.request(`/api/match/${matchId}`);
  }

  // --- User ---
  async getProfile(): Promise<ApiResponse<User>> {
    return this.request('/api/user/me');
  }

  async updateProfile(data: Partial<User>): Promise<ApiResponse<{ message: string }>> {
    return this.request('/api/user/me', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // --- Auth ---
  async login(email: string, password: string): Promise<ApiResponse<{ access_token: string; refresh_token: string }>> {
    return this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async register(email: string, password: string, fullName?: string): Promise<ApiResponse<{ access_token: string }>> {
    return this.request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
  }

  // --- Health ---
  async healthCheck(): Promise<ApiResponse<{ status: string; version: string }>> {
    return this.request('/health');
  }
}

export const api = new ApiClient();
export default ApiClient;
