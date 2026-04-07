import { supabase } from "./supabase";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function getAuthHeaders() {
  const { data: { session } } = await supabase.auth.getSession();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  
  if (session?.access_token) {
    headers["Authorization"] = `Bearer ${session.access_token}`;
  }
  
  return headers;
}

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
      const headers = await getAuthHeaders();
      const res = await fetch(`${API_BASE_URL}/api/team/generate`, {
        method: "POST",
        headers,
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
      const headers = await getAuthHeaders();
      const res = await fetch(`${API_BASE_URL}/api/match/upcoming`, {
        headers,
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
      const headers = await getAuthHeaders();
      const res = await fetch(`${API_BASE_URL}/api/team/history`, {
        headers,
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
       const headers = await getAuthHeaders();
       const url = query 
         ? `${API_BASE_URL}/api/player/search?q=${encodeURIComponent(query)}`
         : `${API_BASE_URL}/api/player/search?q=a`; // Fallback search to list some players
       const res = await fetch(url, { 
         headers,
         cache: "no-store" 
       });
       
       if (!res.ok) throw new Error("Failed to fetch players");
       const data = await res.json();
       return data.players || [];
     } catch (e) {
       console.warn("API Call Failed for getPlayers:", e);
       return [];
     }
  },

  // 5. Player Stats & Insights
  async getPlayerStats(playerId: string) {
     try {
       const headers = await getAuthHeaders();
       const res = await fetch(`${API_BASE_URL}/api/player/${playerId}/stats`, { headers });
       if (!res.ok) return null;
       return await res.json();
     } catch (e) {
       return null;
     }
  },

  async getPlayerInsights(playerId: string) {
     try {
       const headers = await getAuthHeaders();
       const res = await fetch(`${API_BASE_URL}/api/player/${playerId}/insights`, { headers });
       if (!res.ok) return null;
       return await res.json();
     } catch (e) {
       return null;
     }
  },

  // 6. Admin Endpoints
  async getAdminQuotas() {
    try {
      const headers = await getAuthHeaders();
      const res = await fetch(`${API_BASE_URL}/api/admin/quotas`, { headers });
      if (!res.ok) throw new Error("Admin access denied");
      return await res.json();
    } catch (e) {
      console.error("Admin Quotas fetch failed:", e);
      return [];
    }
  },

  async getAdminStats() {
    try {
      const headers = await getAuthHeaders();
      const res = await fetch(`${API_BASE_URL}/api/admin/stats`, { headers });
      if (!res.ok) throw new Error("Admin access denied");
      return await res.json();
    } catch (e) {
      console.error("Admin Stats fetch failed:", e);
      return { total_users: 0, total_teams: 0, active_subscriptions: 0 };
    }
  },

  // 7. Payment Endpoints
  async createOrder(planId: "pro" | "elite") {
    try {
      const headers = await getAuthHeaders();
      const res = await fetch(`${API_BASE_URL}/api/payment/create-order`, {
        method: "POST",
        headers,
        body: JSON.stringify({ plan_id: planId }),
      });
      if (!res.ok) throw new Error("Failed to create order");
      return await res.json();
    } catch (e) {
      console.error("Order Creation failed:", e);
      throw e;
    }
  },

  async verifyPayment(data: {
    razorpay_order_id: string;
    razorpay_payment_id: string;
    razorpay_signature: string;
    plan_id: string;
  }) {
    try {
      const headers = await getAuthHeaders();
      const res = await fetch(`${API_BASE_URL}/api/payment/verify`, {
        method: "POST",
        headers,
        body: JSON.stringify(data),
      });
      if (!res.ok) throw new Error("Payment verification failed");
      return await res.json();
    } catch (e) {
      console.error("Payment Verification failed:", e);
      throw e;
    }
  }
};

