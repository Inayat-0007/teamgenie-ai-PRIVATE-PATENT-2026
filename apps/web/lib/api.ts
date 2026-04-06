const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface TeamGenerateRequest {
  match_id: string;
  budget: number;
  risk_level: string;
  team_a?: string;
  team_b?: string;
  venue?: string;
  toss_winner?: string;
  toss_decision?: string;
}

export const aiKit = {
  // 1. Team Generation Endpoint
  async generateTeam(data: TeamGenerateRequest) {
    try {
      const res = await fetch(`${API_BASE_URL}/api/team/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
        cache: "no-store",
      });

      if (!res.ok) {
        // Detailed error logging for debugging 422s
        const errData = await res.json().catch(() => ({}));
        console.error("Backend Error:", errData);
        throw new Error(`HTTP ${res.status}: ${JSON.stringify(errData)}`);
      }
      return await res.json();
    } catch (e) {
      console.warn("API Call Failed — No Fake Data Fallback Anymore:", e);
      throw e; // Rethrow to show the error in the UI
    }
  },

  // 2. Fetch Matches List
  async getMatches() {
    try {
      const res = await fetch(`${API_BASE_URL}/api/match/upcoming`, {
        cache: "no-store",
      });
      if (!res.ok) throw new Error("Failed to fetch matches");
      const data = await res.json();
      return data.matches || [];
    } catch (e) {
      console.warn("API Call Failed for getMatches:", e);
      return [];
    }
  },

  // 3. User History (Squads)
  async getHistory() {
    try {
      const res = await fetch(`${API_BASE_URL}/api/team/history`, {
        cache: "no-store",
      });
      if (!res.ok) throw new Error("Failed to fetch history");
      const data = await res.json();
      return data.teams || [];
    } catch (e) {
      console.warn("API Call Failed for getHistory:", e);
      return [];
    }
  },

  // 4. Players Analytics Directory
  async getPlayers(query: string = "") {
     try {
       const url = query 
         ? `${API_BASE_URL}/api/player/search?q=${encodeURIComponent(query)}`
         : `${API_BASE_URL}/api/player/search?q=a`; // Fallback search to list some players
       const res = await fetch(url, { cache: "no-store" });
       
       if (!res.ok) throw new Error("Failed to fetch players");
       const data = await res.json();
       // Map to expected format if necessary, though backend returns matching fields
       return data.players || [];
     } catch (e) {
       console.warn("API Call Failed for getPlayers:", e);
       return [];
     }
  },

  // 5. Player Stats & Insights
  async getPlayerStats(playerId: string) {
     try {
       const res = await fetch(`${API_BASE_URL}/api/player/${playerId}/stats`);
       if (!res.ok) return null;
       return await res.json();
     } catch (e) {
       return null;
     }
  },

  async getPlayerInsights(playerId: string) {
     try {
       const res = await fetch(`${API_BASE_URL}/api/player/${playerId}/insights`);
       if (!res.ok) return null;
       return await res.json();
     } catch (e) {
       return null;
     }
  }
};
