"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Zap, Shield, TrendingUp, Cpu, Award } from "lucide-react";
import { aiKit } from "@/lib/api";
import { PlayerCard } from "@/components/PlayerCard";
import { ScoutFeed } from "@/components/ScoutFeed";

export default function GenerateTeamPage() {
  const [matchId, setMatchId] = useState("ipl_2026_01");
  const [budget, setBudget] = useState(100);
  const [riskLevel, setRiskLevel] = useState("balanced");
  const [tossWinner, setTossWinner] = useState("");
  const [tossDecision, setTossDecision] = useState("");
  
  const [isGenerating, setIsGenerating] = useState(false);
  const [loadingAgent, setLoadingAgent] = useState("");
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsGenerating(true);
    setResult(null);
    setError("");

    try {
      // Fast, Addictive Loading Simulation sequence
      setLoadingAgent("JIT Scraper (DuckDuckGo)");
      await new Promise(r => setTimeout(r, 300));

      setLoadingAgent("Budget Optimizer (ILP)");
      await new Promise(r => setTimeout(r, 400));
      
      setLoadingAgent("Differential Expert (RAG)");
      await new Promise(r => setTimeout(r, 400));
      
      setLoadingAgent("Risk Manager (Monte Carlo)");
      await new Promise(r => setTimeout(r, 400));

      const response = await aiKit.generateTeam({
        match_id: matchId,
        budget,
        risk_level: riskLevel,
        ...(tossWinner && { toss_winner: tossWinner }),
        ...(tossDecision && { toss_decision: tossDecision }),
      });

      setResult(response.team);
    } catch (err: any) {
      setError(err.message || "Failed to generate team");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="max-w-[1600px] mx-auto px-4 py-8 mt-8">
      
      <div className="flex flex-col lg:flex-row gap-6">
        
        {/* Left Column: Form */}
        <div className="w-full lg:w-3/12 space-y-6">
          <div className="glass-panel p-6 rounded-2xl">
            <div className="flex items-center space-x-3 mb-6 border-b border-slate-800/50 pb-4">
              <div className="bg-indigo-500/20 p-2 rounded-lg">
                <Cpu className="text-indigo-400 w-6 h-6" />
              </div>
              <h2 className="text-xl font-bold">Params</h2>
            </div>

            <form onSubmit={handleGenerate} className="space-y-6">
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-300">Select Match</label>
                <select 
                  value={matchId}
                  onChange={(e) => setMatchId(e.target.value)}
                  className="w-full bg-slate-950/50 border border-slate-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500/50 appearance-none"
                >
                  <option value="ipl_2026_01">CSK vs MI (IPL Match 1)</option>
                  <option value="ipl_2026_02">RCB vs KKR (IPL Match 2)</option>
                  <option value="wc_2027_10">IND vs AUS (World Cup)</option>
                </select>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <label className="text-sm font-medium text-slate-300">Max Budget</label>
                  <span className="text-indigo-400 font-bold">₹{budget} Cr</span>
                </div>
                <input 
                  type="range" 
                  min="50" max="100" step="0.5" 
                  value={budget}
                  onChange={(e) => setBudget(Number(e.target.value))}
                  className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                />
              </div>

              <div className="space-y-3">
                <label className="text-sm font-medium text-slate-300">Risk Profile</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: 'safe', icon: Shield, label: 'Safe' },
                    { id: 'balanced', icon: TrendingUp, label: 'Bal' },
                    { id: 'aggressive', icon: Zap, label: 'Aggr' }
                  ].map(profile => (
                    <button
                      key={profile.id}
                      type="button"
                      onClick={() => setRiskLevel(profile.id)}
                      className={`flex flex-col items-center justify-center p-2 rounded-xl border transition-all ${
                        riskLevel === profile.id 
                          ? 'bg-indigo-500/20 border-indigo-500/50 text-indigo-300' 
                          : 'bg-slate-950/50 border-slate-800 text-slate-400 hover:border-slate-700'
                      }`}
                    >
                      <profile.icon className="w-4 h-4 mb-1" />
                      <span className="text-[10px] font-medium">{profile.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {error && (
                <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
                  {error}
                </div>
              )}

              {/* Phase 7: Toss Intelligence */}
              <div className="space-y-3 pt-2 border-t border-slate-800/50">
                <label className="text-sm font-medium text-slate-300 flex items-center space-x-2">
                  <span>⚡ Toss Result</span>
                  <span className="text-[10px] bg-amber-500/20 text-amber-400 px-2 py-0.5 rounded-full">LIVE</span>
                </label>
                <select
                  value={tossWinner}
                  onChange={(e) => setTossWinner(e.target.value)}
                  className="w-full bg-slate-950/50 border border-slate-800 rounded-xl px-4 py-2.5 text-white text-sm focus:outline-none focus:ring-2 focus:ring-amber-500/50 appearance-none"
                >
                  <option value="">Unknown / Not yet</option>
                  <option value="Team A">Team A won toss</option>
                  <option value="Team B">Team B won toss</option>
                </select>
                {tossWinner && (
                  <div className="grid grid-cols-2 gap-2">
                    {["bat", "bowl"].map(d => (
                      <button
                        key={d}
                        type="button"
                        onClick={() => setTossDecision(d)}
                        className={`py-2 rounded-xl border text-sm font-medium transition-all capitalize ${
                          tossDecision === d
                            ? 'bg-amber-500/20 border-amber-500/50 text-amber-300'
                            : 'bg-slate-950/50 border-slate-800 text-slate-400 hover:border-slate-700'
                        }`}
                      >
                        Chose to {d}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              <button
                type="submit"
                disabled={isGenerating}
                className={`w-full font-bold py-4 rounded-xl transition-all shadow-lg flex items-center justify-center space-x-2 ${
                  isGenerating 
                    ? 'bg-indigo-600/50 text-indigo-200 cursor-not-allowed' 
                    : 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-[0_0_20px_rgba(79,70,229,0.3)] hover:shadow-[0_0_30px_rgba(79,70,229,0.5)] active:scale-95'
                }`}
              >
                {isGenerating ? (
                   <>
                     <div className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full animate-spin" />
                     <span>Processing...</span>
                   </>
                ) : (
                  <>
                    <Zap className="w-5 h-5" />
                    <span>Run AI Generation</span>
                  </>
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Center Column: Loading / Results */}
        <div className="w-full lg:w-6/12 h-full">
          <AnimatePresence mode="wait">
            
            {/* Loading State */}
            {isGenerating && (
              <motion.div 
                key="loading"
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="glass-panel p-12 rounded-2xl flex flex-col items-center justify-center min-h-[600px] border-indigo-500/30"
              >
                <div className="relative w-32 h-32 mb-8">
                  <div className="absolute inset-0 bg-indigo-500/20 rounded-full animate-ping" />
                  <div className="absolute inset-2 bg-purple-500/20 rounded-full animate-ping animation-delay-300" />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Cpu className="w-12 h-12 text-indigo-400 animate-pulse" />
                  </div>
                </div>
                <h3 className="text-2xl font-bold text-white mb-2">Engaging Neural Network</h3>
                <p className="text-indigo-400 font-medium h-6 animate-pulse">{loadingAgent}</p>
              </motion.div>
            )}

            {/* Results State */}
            {!isGenerating && result && (
              <motion.div 
                key="results"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-6"
              >
                {/* Stats Bar */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                   <div className="glass-panel p-3 rounded-xl border border-indigo-500/30">
                     <p className="text-slate-400 text-xs mb-1 uppercase tracking-wider">Total Cost</p>
                     <p className="text-xl font-bold text-white">₹{result.total_cost.toFixed(1)}</p>
                   </div>
                   <div className="glass-panel p-3 rounded-xl border border-emerald-500/30">
                     <p className="text-slate-400 text-xs mb-1 uppercase tracking-wider">Proj Total</p>
                     <p className="text-xl font-bold text-emerald-400">{result.predicted_total.toFixed(0)} pts</p>
                   </div>
                   <div className="glass-panel p-3 rounded-xl">
                     <p className="text-slate-400 text-xs mb-1 uppercase tracking-wider">Risk Score</p>
                     <p className="text-xl font-bold text-purple-400">{(result.risk_score * 100).toFixed(0)}%</p>
                   </div>
                   <div className="glass-panel p-3 rounded-xl">
                     <p className="text-slate-400 text-xs mb-1 uppercase tracking-wider">Players</p>
                     <p className="text-xl font-bold text-white">11<span className="text-sm font-normal text-slate-500">/11</span></p>
                   </div>
                </div>

                {/* Staggered Player Grid */}
                <motion.div 
                  variants={{
                    hidden: { opacity: 0 },
                    show: {
                      opacity: 1,
                      transition: { staggerChildren: 0.05 }
                    }
                  }}
                  initial="hidden"
                  animate="show"
                  className="grid grid-cols-1 sm:grid-cols-2 gap-4"
                >
                  {result.players.map((player: any) => (
                    <PlayerCard 
                      key={player.id} 
                      player={player} 
                      isCaptain={player.id === result.captain}
                      isViceCaptain={player.id === result.vice_captain}
                    />
                  ))}
                </motion.div>
              </motion.div>
            )}

            {/* Empty State */}
            {!isGenerating && !result && (
              <motion.div 
                key="empty"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="glass-panel border-dashed border-2 border-slate-800 p-12 rounded-2xl flex flex-col items-center justify-center min-h-[600px] text-center"
              >
                <div className="bg-slate-900 w-20 h-20 rounded-full flex items-center justify-center mb-6">
                  <Award className="w-10 h-10 text-slate-600" />
                </div>
                <h3 className="text-xl font-bold text-slate-300 mb-2">Awaiting Parameters</h3>
                <p className="text-slate-500 max-w-sm text-sm">
                  Configure the match and budget on the left to deploy the AI pipeline.
                </p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Right Column: AI Intelligence Scout Feed */}
        <div className="w-full lg:w-3/12">
          <ScoutFeed />
        </div>

      </div>
    </div>
  );
}
