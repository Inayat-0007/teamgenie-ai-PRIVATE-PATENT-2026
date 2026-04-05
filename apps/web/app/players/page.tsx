"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Database, TrendingUp, TrendingDown, Users } from "lucide-react";
import { aiKit } from "@/lib/api";

export default function PlayersPage() {
  const [players, setPlayers] = useState<any[]>([]);

  useEffect(() => {
    aiKit.getPlayers().then(setPlayers);
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 py-12 mt-8">
      <div className="mb-10 flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-extrabold text-white mb-2 flex items-center">
            <Database className="w-8 h-8 mr-3 text-indigo-400" />
            Player Analytics Engine
          </h1>
          <p className="text-slate-400">Raw statistical projections fueling the AI Risk Manager.</p>
        </div>
      </div>

      <div className="glass-panel rounded-2xl overflow-hidden border-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full bg-transparent">
            <thead>
              <tr className="bg-slate-900 border-b border-slate-800 text-slate-400 text-sm text-left">
                <th className="px-6 py-4 font-medium">Player</th>
                <th className="px-6 py-4 font-medium">Role</th>
                <th className="px-6 py-4 font-medium text-center">Form (1-10)</th>
                <th className="px-6 py-4 font-medium text-center">Projected</th>
                <th className="px-6 py-4 font-medium text-center">Ceiling / Floor</th>
                <th className="px-6 py-4 font-medium text-center">Ownership</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {players.map((p, i) => (
                <motion.tr 
                  key={p.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.05 }}
                  className="hover:bg-slate-800/40 transition-colors"
                >
                  <td className="px-6 py-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center font-bold text-xs text-white">
                        {p.name.charAt(0)}
                      </div>
                      <div>
                        <p className="font-bold text-white">{p.name}</p>
                        <p className="text-xs text-slate-500">{p.team}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-slate-300 capitalize">{p.role.replace('_', ' ')}</td>
                  <td className="px-6 py-4 text-center">
                    <span className={`px-2 py-1 rounded text-xs font-bold ${p.form > 8 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-800 text-slate-300'}`}>
                      {p.form}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center font-bold text-indigo-400">{p.expected}</td>
                  <td className="px-6 py-4 text-center">
                    <div className="flex items-center justify-center space-x-2 text-xs">
                       <span className="text-slate-400">{p.floor}</span>
                       <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                          <div className="h-full bg-gradient-to-r from-rose-500 via-amber-500 to-emerald-500 w-full" />
                       </div>
                       <span className="text-white font-bold">{p.ceiling}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <span className={`font-bold ${p.ownership < 25 ? 'text-purple-400' : 'text-slate-300'}`}>
                      {p.ownership}%
                      {p.ownership < 25 && ' 🔥'}
                    </span>
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
