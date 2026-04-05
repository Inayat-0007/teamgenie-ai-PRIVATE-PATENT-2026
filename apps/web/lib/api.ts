const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface TeamGenerateRequest {
  match_id: string;
  budget: number;
  risk_level: string;
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
        throw new Error("HTTP error!");
      }
      return await res.json();
    } catch (e) {
      // DEMO MODE FALLBACK: If backend is off or returns error, return high-quality mock data
      return {
          team: {
            players: [
              { id: "v_kohli", name: "Virat Kohli", role: "batsman", price: 10.5, predicted_points: 85.3, ownership_pct: 67.3 },
              { id: "r_sharma", name: "Rohit Sharma", role: "batsman", price: 10.0, predicted_points: 72.1, ownership_pct: 71.5 },
              { id: "h_pandya", name: "Hardik Pandya", role: "all_rounder", price: 9.0, predicted_points: 62.0, ownership_pct: 45.3 },
              { id: "j_bumrah", name: "Jasprit Bumrah", role: "bowler", price: 9.5, predicted_points: 68.4, ownership_pct: 55.2 },
              { id: "r_jadeja", name: "Ravindra Jadeja", role: "all_rounder", price: 9.0, predicted_points: 65.0, ownership_pct: 42.1 },
              { id: "s_yadav", name: "Suryakumar Yadav", role: "batsman", price: 9.0, predicted_points: 70.2, ownership_pct: 50.1 },
              { id: "m_siraj", name: "Mohammed Siraj", role: "bowler", price: 8.0, predicted_points: 50.1, ownership_pct: 22.3 },
              { id: "a_patel", name: "Axar Patel", role: "all_rounder", price: 8.0, predicted_points: 48.5, ownership_pct: 18.2 },
              { id: "k_yadav", name: "Kuldeep Yadav", role: "bowler", price: 8.5, predicted_points: 55.3, ownership_pct: 28.5 },
              { id: "s_gill", name: "Shubman Gill", role: "batsman", price: 9.5, predicted_points: 58.0, ownership_pct: 35.6 },
              { id: "r_pant", name: "Rishabh Pant", role: "wicket_keeper", price: 9.0, predicted_points: 60.5, ownership_pct: 38.7 },
            ],
            captain: "v_kohli",
            vice_captain: "r_sharma",
            total_cost: 100.0,
            predicted_total: 695.4,
            risk_score: 0.5,
          }
        };
    }
  },

  // 2. Fetch Matches List
  async getMatches() {
    return [
      { id: "ipl_2026_01", title: "Chennai Super Kings vs Mumbai Indians", league: "IPL 2026", date: "Tonight, 7:30 PM IST", status: "upcoming", prize: "₹10 Crores" },
      { id: "ipl_2026_02", title: "Royal Challengers Bangalore vs KKR", league: "IPL 2026", date: "Tomorrow, 7:30 PM IST", status: "upcoming", prize: "₹5 Crores" },
      { id: "wc_2027_10", title: "India vs Australia", league: "World Cup", date: "Friday, 2:00 PM IST", status: "upcoming", prize: "₹20 Crores" },
      { id: "eng_aus_01", title: "England vs Australia", league: "The Ashes", date: "Sat, 10:00 AM IST", status: "upcoming", prize: "₹2 Crores" }
    ];
  },

  // 3. User History (Squads)
  async getHistory() {
    return [
      { id: "sq_101", match: "CSK vs MI", date: "2026-04-03", points: 845.2, rank: 142, status: "completed" },
      { id: "sq_102", match: "RCB vs PBKS", date: "2026-04-01", points: 610.5, rank: 5402, status: "completed" },
      { id: "sq_103", match: "IND vs PAK", date: "2026-03-28", points: 1020.8, rank: 12, status: "completed" }
    ];
  },

  // 4. Players Analytics Directory
  async getPlayers() {
     return [
      { id: "v_kohli", name: "Virat Kohli", role: "batsman", team: "RCB", form: 8.5, expected: 85.3, floor: 40, ceiling: 140, ownership: 67 },
      { id: "r_sharma", name: "Rohit Sharma", role: "batsman", team: "MI", form: 7.2, expected: 72.1, floor: 20, ceiling: 120, ownership: 71 },
      { id: "j_bumrah", name: "Jasprit Bumrah", role: "bowler", team: "MI", form: 9.1, expected: 68.4, floor: 35, ceiling: 110, ownership: 55 },
      { id: "r_jadeja", name: "Ravindra Jadeja", role: "all_rounder", team: "CSK", form: 8.0, expected: 65.0, floor: 30, ceiling: 105, ownership: 42 },
      { id: "m_pathirana", name: "M. Pathirana", role: "bowler", team: "CSK", form: 7.5, expected: 58.0, floor: 15, ceiling: 90, ownership: 12 }, // Differential
      { id: "t_stubs", name: "Tristan Stubbs", role: "batsman", team: "DC", form: 8.8, expected: 62.0, floor: 10, ceiling: 130, ownership: 18 }, // Differential
     ];
  }
};
