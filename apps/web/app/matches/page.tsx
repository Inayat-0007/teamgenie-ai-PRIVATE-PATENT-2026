"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { Calendar, Trophy, ChevronRight, PlayCircle } from "lucide-react";
import { aiKit } from "@/lib/api";

export default function MatchesPage() {
  const [matches, setMatches] = useState<any[]>([]);

  useEffect(() => {
    aiKit.getMatches().then(setMatches);
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 py-12 mt-8">
      <div className="flex justify-between items-end mb-10 border-b border-slate-800/50 pb-6">
        <div>
          <h1 className="text-4xl font-extrabold text-white mb-2">Match Center</h1>
          <p className="text-slate-400">Select an upcoming match to generate your intelligent roster.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {matches.map((match, i) => (
          <motion.div
            key={match.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="glass-panel rounded-2xl p-6 border-slate-800/80 hover:border-indigo-500/50 transition-all group"
          >
            <div className="flex justify-between items-start mb-4">
              <span className="bg-indigo-500/20 text-indigo-300 text-xs font-bold px-3 py-1 rounded-full uppercase tracking-wider">
                {match.league}
              </span>
              <span className="flex items-center text-emerald-400 text-xs font-bold bg-emerald-500/10 px-2 py-1 rounded-md">
                <Trophy className="w-3 h-3 mr-1" /> {match.prize}
              </span>
            </div>

            <h3 className="text-xl font-bold text-white mb-4 h-14">{match.title}</h3>

            <div className="flex items-center text-slate-400 text-sm mb-6">
              <Calendar className="w-4 h-4 mr-2" />
              {match.date}
            </div>

            <Link href={`/team/generate?match=${match.id}`} className="block w-full">
               <button className="w-full py-3 bg-slate-800 group-hover:bg-indigo-600 text-white font-medium rounded-xl transition-all flex justify-center items-center space-x-2">
                 <span>Generate Team</span>
                 <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
               </button>
            </Link>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
