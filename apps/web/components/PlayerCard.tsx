import { Star, ShieldAlert, TrendingUp } from "lucide-react";
import { motion } from "framer-motion";

export function PlayerCard({ player, isCaptain = false, isViceCaptain = false }: any) {
  return (
    <motion.div 
      variants={{
        hidden: { opacity: 0, scale: 0.8, y: 20 },
        show: { 
          opacity: 1, 
          scale: 1, 
          y: 0,
          transition: { type: "spring", stiffness: 400, damping: 25 }
        }
      }}
      whileHover={{ scale: 1.03, transition: { duration: 0.1 } }}
      whileTap={{ scale: 0.98 }}
      className={`glass-panel p-4 rounded-xl border relative overflow-hidden cursor-pointer ${
        isCaptain ? "border-amber-500/50 shadow-[0_0_15px_rgba(245,158,11,0.2)] bg-amber-500/5" : 
        isViceCaptain ? "border-indigo-500/50 shadow-[0_0_15px_rgba(99,102,241,0.2)] bg-indigo-500/5" : 
        "border-slate-800/50 hover:border-slate-600 hover:bg-slate-800/20"
      }`}
    >
      
      {/* Badges */}
      {isCaptain && (
        <div className="absolute top-0 right-0 bg-gradient-to-r from-amber-500 to-orange-500 text-white text-[10px] font-bold px-2 py-1 rounded-bl-lg flex items-center shadow-lg">
          <Star className="w-3 h-3 mr-1 fill-current" /> CAPTAIN (2x)
        </div>
      )}
      {isViceCaptain && (
        <div className="absolute top-0 right-0 bg-gradient-to-r from-indigo-500 to-purple-500 text-white text-[10px] font-bold px-2 py-1 rounded-bl-lg flex items-center shadow-lg">
          <ShieldAlert className="w-3 h-3 mr-1" /> VC (1.5x)
        </div>
      )}

      <div className="flex items-center space-x-3 mt-1">
        <div className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm shadow-inner bg-gradient-to-br ${
          player.role === 'batsman' ? 'from-blue-500 to-blue-700' :
          player.role === 'bowler' ? 'from-rose-500 to-rose-700' :
          player.role === 'all_rounder' ? 'from-emerald-500 to-emerald-700' :
          'from-purple-500 to-purple-700'
        }`}>
          {player.name.charAt(0)}
        </div>
        <div>
          <h4 className="font-bold text-slate-100 leading-tight tracking-tight">{player.name}</h4>
          <p className="text-xs text-slate-400 capitalize">{player.role.replace('_', ' ')} • ₹{player.price.toFixed(1)}</p>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-slate-800/50 flex justify-between items-center text-xs">
        <div className="flex flex-col">
          <span className="text-slate-500 mb-1 font-medium">Proj. Pts</span>
          <span className="font-bold text-emerald-400 flex items-center bg-emerald-500/10 px-2 py-0.5 rounded">
            <TrendingUp className="w-3 h-3 mr-1" /> 
            {isCaptain ? (player.predicted_points * 2).toFixed(1) : 
             isViceCaptain ? (player.predicted_points * 1.5).toFixed(1) : 
             player.predicted_points.toFixed(1)}
          </span>
        </div>
        <div className="flex flex-col text-right">
          <span className="text-slate-500 mb-1 font-medium">Ownership</span>
          <span className={`font-bold px-2 py-0.5 rounded ${player.ownership_pct < 25 ? 'bg-purple-500/10 text-purple-400' : 'bg-slate-800 text-slate-300'}`}>
            {player.ownership_pct}% 
            {player.ownership_pct < 25 && ' 🔥'}
          </span>
        </div>
      </div>
    </motion.div>
  )
}
