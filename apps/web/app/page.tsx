'use client';

import { useCallback, useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';

// --- Data Constants (single source of truth) ---
const STATS = [
  { label: 'Response Time', value: '<5s', icon: '⚡' },
  { label: 'Accuracy', value: '72%', icon: '🎯' },
  { label: 'Uptime', value: '99.95%', icon: '🟢' },
  { label: 'Users', value: '10K+', icon: '👥' },
] as const;

const AGENTS = [
  {
    step: '01',
    title: 'Budget Optimizer',
    desc: 'OR-Tools ILP solver maximizes points within ₹100 budget constraint.',
    icon: '🤖',
  },
  {
    step: '02',
    title: 'Differential Expert',
    desc: 'RAG pipeline finds low-ownership gems with high upside potential.',
    icon: '💎',
  },
  {
    step: '03',
    title: 'Risk Manager',
    desc: 'Monte Carlo simulation balances risk/reward for your play style.',
    icon: '🛡️',
  },
] as const;

// --- Animation Variants ---
const fadeInUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0 },
};

const staggerContainer = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.15 } },
};

export default function HomePage() {
  const prefersReducedMotion = useReducedMotion();

  // Demo CTA state
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerate = useCallback(async () => {
    setIsGenerating(true);
    // TODO: Navigate to team generation page
    setTimeout(() => setIsGenerating(false), 2000);
  }, []);

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-4 py-16 relative overflow-hidden">
      {/* Background ambient glow orbs */}
      <div className="absolute top-1/4 -left-32 w-96 h-96 bg-indigo-600/10 rounded-full blur-[128px] pointer-events-none" aria-hidden="true" />
      <div className="absolute bottom-1/4 -right-32 w-96 h-96 bg-cyan-500/10 rounded-full blur-[128px] pointer-events-none" aria-hidden="true" />

      {/* Hero Section */}
      <motion.div
        initial="hidden"
        animate="visible"
        variants={prefersReducedMotion ? {} : fadeInUp}
        transition={{ duration: 0.8, ease: 'easeOut' }}
        className="text-center max-w-4xl mx-auto relative z-10"
      >
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-sm mb-8"
          role="status"
        >
          <span className="w-2 h-2 rounded-full bg-green-400 pulse-live" aria-hidden="true" />
          AI-Powered Fantasy Sports Intelligence
        </motion.div>

        {/* Title */}
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6 leading-[1.1]">
          Build{' '}
          <span className="gradient-text">Winning Teams</span>
          <br />
          in Under 5 Seconds
        </h1>

        {/* Subtitle */}
        <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          Three AI agents analyze millions of data points and collaborate to generate
          your optimal fantasy cricket team. 72% prediction accuracy, backed by data.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleGenerate}
            disabled={isGenerating}
            aria-label="Generate a free fantasy team"
            id="cta-generate"
            className="px-8 py-4 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-500 text-white font-semibold text-lg shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40 transition-all disabled:opacity-60 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:ring-offset-2 focus:ring-offset-gray-950"
          >
            {isGenerating ? (
              <span className="inline-flex items-center gap-2">
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Generating...
              </span>
            ) : (
              '🏏 Generate Team — Free'
            )}
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            aria-label="View a demo of TeamGenie AI"
            id="cta-demo"
            className="px-8 py-4 rounded-xl glass-card text-white font-semibold text-lg hover:bg-white/10 transition-colors focus:outline-none focus:ring-2 focus:ring-white/30 focus:ring-offset-2 focus:ring-offset-gray-950"
          >
            View Demo →
          </motion.button>
        </div>
      </motion.div>

      {/* Stats Bar */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="glass-card glow p-8 grid grid-cols-2 md:grid-cols-4 gap-8 max-w-3xl w-full relative z-10"
        role="list"
        aria-label="Platform statistics"
      >
        {STATS.map((stat) => (
          <div key={stat.label} className="text-center" role="listitem">
            <div className="text-2xl mb-1" aria-hidden="true">{stat.icon}</div>
            <div className="text-2xl md:text-3xl font-bold gradient-text">{stat.value}</div>
            <div className="text-sm text-gray-500 mt-1">{stat.label}</div>
          </div>
        ))}
      </motion.div>

      {/* How It Works */}
      <motion.section
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, amount: 0.3 }}
        variants={staggerContainer}
        className="mt-24 max-w-4xl w-full relative z-10"
        aria-labelledby="how-it-works-heading"
      >
        <h2 id="how-it-works-heading" className="text-3xl font-bold text-center mb-12">
          How <span className="gradient-text">TeamGenie</span> Works
        </h2>
        <div className="grid md:grid-cols-3 gap-6">
          {AGENTS.map((item) => (
            <motion.article
              key={item.step}
              variants={fadeInUp}
              whileHover={{ y: -4, scale: 1.02 }}
              className="glass-card p-6 cursor-default transition-shadow hover:glow"
            >
              <div className="text-4xl mb-4" aria-hidden="true">{item.icon}</div>
              <div className="text-xs text-indigo-400 font-mono mb-2">AGENT {item.step}</div>
              <h3 className="text-xl font-semibold mb-2">{item.title}</h3>
              <p className="text-gray-400 text-sm leading-relaxed">{item.desc}</p>
            </motion.article>
          ))}
        </div>
      </motion.section>

      {/* Footer */}
      <footer className="mt-24 mb-8 text-center text-gray-600 text-sm relative z-10">
        Built with ❤️ in Bhopal, India 🇮🇳 | © {new Date().getFullYear()} TeamGenie AI
      </footer>
    </main>
  );
}
