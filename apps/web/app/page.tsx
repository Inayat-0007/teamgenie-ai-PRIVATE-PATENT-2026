"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { ArrowRight, Bot, Shield, Zap, Search } from "lucide-react";

export default function Home() {
  return (
    <div className="relative min-h-[calc(100vh-4rem)] flex flex-col items-center justify-center overflow-hidden">
      {/* Background Orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-indigo-600/20 rounded-full blur-[128px] -z-10" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-600/20 rounded-full blur-[128px] -z-10" />

      <main className="flex-1 flex flex-col items-center justify-center text-center px-4 w-full max-w-5xl mx-auto pt-20 pb-32">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-flex items-center space-x-2 glass-panel px-4 py-2 rounded-full mb-8 border-indigo-500/30 text-indigo-300"
        >
          <span className="flex h-2 w-2 rounded-full bg-indigo-500 animate-pulse"></span>
          <span className="text-sm font-medium">Master Doctrine v2.0 Live Engine</span>
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="text-5xl md:text-7xl font-extrabold tracking-tight mb-8 leading-tight"
        >
          Dominate Fantasy Sports <br />
          with <span className="text-gradient">Multi-Agent AI</span>
        </motion.h1>

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="text-lg md:text-xl text-slate-400 max-w-2xl mx-auto mb-12"
        >
          Three autonomous CrewAI agents collaborate to generate mathematically perfect, 
          risk-adjusted fantasy rosters in under 4 milliseconds using OR-Tools ILP optimization.
        </motion.p>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="flex flex-col sm:flex-row items-center space-y-4 sm:space-y-0 sm:space-x-6"
        >
          <Link
            href="/team/generate"
            className="group relative px-8 py-4 bg-white text-slate-950 font-bold rounded-full overflow-hidden transition-all hover:scale-105 shadow-[0_0_40px_rgba(255,255,255,0.3)]"
          >
            <span className="relative z-10 flex items-center space-x-2">
              <span>Generate Team Now</span>
              <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
            </span>
          </Link>
          
          <Link
            href="/matches"
            className="px-8 py-4 glass-panel text-white font-medium rounded-full hover:bg-slate-800/80 transition-colors"
          >
            Explore Matches
          </Link>
        </motion.div>

        {/* Feature Grid */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.5 }}
          className="grid md:grid-cols-3 gap-6 mt-32 w-full text-left"
        >
          {[
            {
              icon: Zap,
              title: "Budget Optimizer (ILP)",
              desc: "Google OR-Tools Integer Linear Programming mathematically guarantees maximum projected points under ₹100 cap.",
              color: "text-amber-400"
            },
            {
              icon: Search, // Using Search from lucide instead of Brain
              title: "Differential Expert",
              desc: "RAG pipeline queries semantic vector spaces to identify <25% ownership players with explosive upside.",
              color: "text-emerald-400"
            },
            {
              icon: Shield,
              title: "Risk Manager",
              desc: "Monte-Carlo variance profiles determine the statistically safest Captain and Vice-Captain choices.",
              color: "text-rose-400"
            }
          ].map((feat, i) => (
            <div key={i} className="glass-panel p-8 rounded-2xl hover:bg-slate-800/40 transition-colors">
              <feat.icon className={`h-10 w-10 mb-4 ${feat.color}`} />
              <h3 className="text-xl font-bold mb-2">{feat.title}</h3>
              <p className="text-slate-400 text-sm leading-relaxed">{feat.desc}</p>
            </div>
          ))}
        </motion.div>
      </main>
    </div>
  );
}
