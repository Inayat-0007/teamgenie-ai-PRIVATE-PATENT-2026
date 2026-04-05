"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { History, Award, ChevronRight } from "lucide-react";
import { aiKit } from "@/lib/api";

export default function HistoryPage() {
  const [history, setHistory] = useState<any[]>([]);

  useEffect(() => {
    aiKit.getHistory().then(setHistory);
  }, []);

  return (
    <div className="max-w-5xl mx-auto px-4 py-12 mt-8">
      <div className="mb-10 text-center">
        <div className="mx-auto bg-purple-500/10 w-16 h-16 rounded-full flex items-center justify-center mb-4 border border-purple-500/20">
            <History className="h-8 w-8 text-purple-400" />
        </div>
        <h1 className="text-4xl font-extrabold text-white mb-2">My Squads</h1>
        <p className="text-slate-400">Your historical AI-generated teams and performance metrics.</p>
      </div>

      <div className="space-y-4">
        {history.map((item, i) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
            className="glass-panel rounded-2xl p-6 flex flex-col md:flex-row items-center justify-between border-slate-800/80 hover:bg-slate-800/40 transition-all cursor-pointer"
          >
            <div className="flex-1 mb-4 md:mb-0">
              <div className="flex items-center space-x-3 mb-1">
                <h3 className="text-xl font-bold text-white">{item.match}</h3>
                <span className="bg-slate-800 text-slate-300 text-xs px-2 py-1 rounded-md">{item.date}</span>
              </div>
            </div>

            <div className="flex items-center space-x-8">
              <div className="text-center">
                <p className="text-xs text-slate-500 uppercase tracking-wide mb-1">Points Scored</p>
                <p className="text-2xl font-bold text-emerald-400">{item.points}</p>
              </div>
              <div className="text-center">
                <p className="text-xs text-slate-500 uppercase tracking-wide mb-1">Global Rank</p>
                <p className="text-2xl font-bold text-white flex items-center justify-center">
                  <Award className="w-4 h-4 mr-1 text-amber-400" /> #{item.rank}
                </p>
              </div>
              <ChevronRight className="w-5 h-5 text-slate-600 hidden md:block" />
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
