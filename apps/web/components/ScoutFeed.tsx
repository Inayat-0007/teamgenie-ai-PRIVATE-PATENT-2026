"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Rss, Zap } from "lucide-react";

const DUMMY_FEED = [
  { id: 1, text: "Wankhede pitch glowing green tonight. Fast bowlers will get 15% more seam movement in powerplay.", time: "Live", highlight: true },
  { id: 2, text: "Mohammed Siraj's ownership dropped to 22% after recent form dip. Massive differential potential.", time: "2m ago", highlight: false },
  { id: 3, text: "Rohit Sharma average against left-arm spin is 142.0 this season.", time: "5m ago", highlight: false },
  { id: 4, text: "Weather update: 0% rain probability. Expect a full 20-over game.", time: "12m ago", highlight: false },
  { id: 5, text: "CSK likely to bowl first if they win the toss due to dew factor.", time: "18m ago", highlight: false }
];

export function ScoutFeed() {
  const [feed, setFeed] = useState<any[]>([]);
  
  // Simulate AI streaming in insights over time
  useEffect(() => {
    setFeed([DUMMY_FEED[4], DUMMY_FEED[3]]);
    
    setTimeout(() => setFeed(prev => [DUMMY_FEED[2], ...prev]), 2000);
    setTimeout(() => setFeed(prev => [DUMMY_FEED[1], ...prev]), 5000);
    setTimeout(() => setFeed(prev => [DUMMY_FEED[0], ...prev]), 9000);
  }, []);

  return (
    <div className="glass-panel rounded-2xl overflow-hidden h-[600px] flex flex-col border-slate-800/80">
      <div className="bg-slate-900/80 p-4 border-b border-slate-800/80 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="bg-rose-500/20 p-1.5 rounded flex items-center justify-center">
            <Rss className="w-4 h-4 text-rose-400 animate-pulse" />
          </div>
          <h3 className="font-bold text-sm tracking-wide text-slate-200">AI Scout Intel</h3>
        </div>
        <span className="text-[10px] uppercase font-bold text-slate-500 bg-slate-800 px-2 py-0.5 rounded">Live</span>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        <AnimatePresence>
          {feed.map((item) => (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, x: 20, height: 0 }}
              animate={{ opacity: 1, x: 0, height: 'auto' }}
              transition={{ type: "spring", stiffness: 400, damping: 25 }}
              className={`p-3 rounded-xl border text-sm ${
                item.highlight 
                  ? 'bg-rose-500/10 border-rose-500/30 shadow-[0_0_10px_rgba(225,29,72,0.1)]' 
                  : 'bg-slate-800/30 border-slate-700/50 hover:bg-slate-800/50 transition-colors'
              }`}
            >
              <div className="flex items-center space-x-1 mb-1">
                {item.highlight && <Zap className="w-3 h-3 text-rose-400" />}
                <span className={`text-[10px] font-bold ${item.highlight ? 'text-rose-400' : 'text-indigo-400'}`}>
                  {item.time}
                </span>
              </div>
              <p className="text-slate-300 leading-snug">{item.text}</p>
            </motion.div>
          ))}
        </AnimatePresence>
        
        {feed.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-slate-500 space-y-2">
            <div className="w-6 h-6 border-2 border-slate-700 border-t-slate-500 rounded-full animate-spin" />
            <p className="text-xs">Connecting to scout agent...</p>
          </div>
        )}
      </div>
    </div>
  );
}
