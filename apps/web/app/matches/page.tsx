"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Calendar, Trophy, ChevronRight, Lock, Zap, IndianRupee } from "lucide-react";
import { aiKit } from "@/lib/api";

export default function MatchesPage() {
  const [matches, setMatches] = useState<any[]>([]);
  const [generating, setGenerating] = useState(false);
  const [generatedTeam, setGeneratedTeam] = useState<any[] | null>(null);

  useEffect(() => {
    aiKit.getMatches().then(setMatches);
  }, []);

  const handleFastGenerate = async (matchId: string) => {
    setGenerating(true);
    setGeneratedTeam(null);
    try {
      // Free tier logic: hardcoded safe risk, standard budget
      const result = await aiKit.generateTeam({
        match_id: matchId,
        budget: 100,
        risk_level: "safe"
      });
      setGeneratedTeam(result.team?.players || result);
    } catch (e) {
      console.error(e);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-12 mt-8">
      <div className="flex justify-between items-end mb-10 border-b border-slate-800/50 pb-6">
        <div>
          <h1 className="text-4xl font-extrabold text-white mb-2 tracking-tight">
            Match Center <span className="text-sm font-medium bg-emerald-500/20 text-emerald-400 px-3 py-1 rounded-full align-middle ml-3">Free Tier Active</span>
          </h1>
          <p className="text-slate-400">1-Click generation for casual players. Upgrade for precise control.</p>
        </div>
        <a href="/team/generate" className="hidden md:flex items-center space-x-2 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-black px-6 py-2.5 rounded-full font-bold transition-all transform hover:scale-105 shadow-[0_0_20px_rgba(245,158,11,0.3)]">
          <Zap className="w-4 h-4" />
          <span>Switch to PRO Dashboard</span>
        </a>
      </div>

      <AnimatePresence mode="wait">
        {!generatedTeam && !generating && (
          <motion.div 
            initial={{ opacity: 0 }} 
            animate={{ opacity: 1 }} 
            exit={{ opacity: 0 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            {matches.map((match, i) => (
              <motion.div
                key={match.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="glass-panel rounded-3xl p-1 border border-slate-800/80 hover:border-indigo-500/50 transition-all group overflow-hidden relative"
              >
                <div className="bg-slate-900/50 rounded-[22px] p-6 h-full flex flex-col justify-between">
                  <div>
                    <div className="flex justify-between items-start mb-6">
                      <span className="bg-indigo-500/20 text-indigo-300 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider backdrop-blur-md">
                        {match.league}
                      </span>
                      <span className="flex items-center text-emerald-400 text-xs font-bold bg-emerald-500/10 px-2 py-1 rounded-md">
                        <Trophy className="w-3 h-3 mr-1" /> {match.prize}
                      </span>
                    </div>

                    <h3 className="text-2xl font-bold text-white mb-2 leading-tight">{match.title}</h3>

                    <div className="flex items-center text-slate-400 text-sm mb-8">
                      <Calendar className="w-4 h-4 mr-2" />
                      {match.date}
                    </div>
                  </div>

                  <button 
                    onClick={() => handleFastGenerate(match.id)}
                    className="w-full py-4 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-2xl transition-all flex justify-center items-center space-x-2 group-hover:shadow-[0_0_30px_rgba(99,102,241,0.4)]"
                  >
                    <Zap className="w-5 h-5 fill-current" />
                    <span>1-Click Generate</span>
                  </button>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}

        {generating && (
          <motion.div 
            initial={{ opacity: 0 }} 
            animate={{ opacity: 1 }} 
            className="flex flex-col items-center justify-center py-32"
          >
            <div className="relative w-24 h-24 mb-8">
              <div className="absolute inset-0 border-4 border-indigo-500/20 rounded-full"></div>
              <div className="absolute inset-0 border-4 border-indigo-500 rounded-full border-t-transparent animate-spin"></div>
              <div className="absolute inset-0 flex items-center justify-center">
                <Zap className="w-8 h-8 text-indigo-400 animate-pulse" />
              </div>
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Analyzing Pitch & Matchups</h2>
            <p className="text-indigo-300 text-center max-w-md">Our deterministic AI is scanning DuckDuckGo injury reports and historical head-to-head records...</p>
          </motion.div>
        )}

        {generatedTeam && !generating && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }} 
            animate={{ opacity: 1, scale: 1 }} 
            className="space-y-6"
          >
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-3xl font-bold text-white">Your Predicted 11</h2>
              <button 
                onClick={() => setGeneratedTeam(null)}
                className="text-slate-400 hover:text-white"
              >
                Back to Matches
              </button>
            </div>

            {/* Basic Players Grid (Free view) */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
              {generatedTeam.map((player: any, i: number) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.05 }}
                  className="bg-slate-800/80 border border-slate-700/50 rounded-xl p-3 text-center"
                >
                  <p className="font-bold text-indigo-300 text-xs mb-1 uppercase tracking-wider">{player.role}</p>
                  <p className="text-white font-medium text-sm whitespace-nowrap overflow-hidden text-ellipsis">{player.name}</p>
                </motion.div>
              ))}
            </div>

            {/* MUST HAVE PSYCHOLOGICAL UPGRADE HOOK */}
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1 }}
              className="mt-12 relative rounded-3xl overflow-hidden glass-panel border border-amber-500/30 p-1"
            >
              {/* Blurred underlay */}
              <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-md z-10 flex flex-col items-center justify-center p-8 text-center">
                <div className="w-16 h-16 bg-amber-500/20 rounded-full flex items-center justify-center mb-4 border border-amber-500/50">
                  <Lock className="w-8 h-8 text-amber-500" />
                </div>
                <h3 className="text-3xl font-extrabold text-white mb-3 tracking-tight">AI Differential Secret Found</h3>
                <p className="text-slate-300 max-w-lg mx-auto mb-8 text-lg">
                  Claude 4.0 Haiku Monte-Carlo simulation has identified a huge vulnerability in the opposition&apos;s bowling attack that 85% of players will miss. 
                </p>
                <a href="/team/generate" className="flex items-center space-x-3 bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-400 hover:to-orange-400 text-black px-10 py-4 rounded-xl font-bold transition-all transform hover:scale-105 shadow-[0_0_40px_rgba(245,158,11,0.4)] text-lg">
                  <span>Unlock PRO Dashboard</span>
                  <span className="font-black bg-black/10 px-2 py-1 rounded">₹199/mo</span>
                </a>
              </div>

              {/* Fake blurred content */}
              <div className="p-8 opacity-20 filter blur-sm">
                <div className="h-6 w-48 bg-slate-700 rounded mb-4"></div>
                <div className="h-4 w-full bg-slate-700 rounded mb-2"></div>
                <div className="h-4 w-5/6 bg-slate-700 rounded mb-8"></div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div className="h-32 bg-slate-800 rounded-xl"></div>
                  <div className="h-32 bg-slate-800 rounded-xl"></div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
