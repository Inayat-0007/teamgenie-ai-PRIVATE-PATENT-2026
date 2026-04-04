'use client';

import { motion } from 'framer-motion';

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-4">
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: 'easeOut' }}
        className="text-center max-w-4xl mx-auto"
      >
        {/* Badge */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-sm mb-8"
        >
          <span className="w-2 h-2 rounded-full bg-green-400 pulse-live" />
          AI-Powered Fantasy Sports Intelligence
        </motion.div>

        {/* Title */}
        <h1 className="text-5xl md:text-7xl font-bold tracking-tight mb-6">
          Build{' '}
          <span className="gradient-text">Winning Teams</span>
          <br />
          in Under 5 Seconds
        </h1>

        {/* Subtitle */}
        <p className="text-lg md:text-xl text-gray-400 max-w-2xl mx-auto mb-10">
          Three AI agents analyze millions of data points and collaborate to generate
          your optimal fantasy cricket team. 72% prediction accuracy, backed by data.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="px-8 py-4 rounded-xl bg-gradient-to-r from-indigo-600 to-cyan-500 text-white font-semibold text-lg shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40 transition-shadow"
          >
            🏏 Generate Team — Free
          </motion.button>
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="px-8 py-4 rounded-xl glass-card text-white font-semibold text-lg hover:bg-white/10 transition-colors"
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
        className="glass-card glow p-8 grid grid-cols-2 md:grid-cols-4 gap-8 max-w-3xl w-full"
      >
        {[
          { label: 'Response Time', value: '<5s', icon: '⚡' },
          { label: 'Accuracy', value: '72%', icon: '🎯' },
          { label: 'Uptime', value: '99.95%', icon: '🟢' },
          { label: 'Users', value: '10K+', icon: '👥' },
        ].map((stat) => (
          <div key={stat.label} className="text-center">
            <div className="text-2xl mb-1">{stat.icon}</div>
            <div className="text-2xl md:text-3xl font-bold gradient-text">{stat.value}</div>
            <div className="text-sm text-gray-500 mt-1">{stat.label}</div>
          </div>
        ))}
      </motion.div>

      {/* How It Works */}
      <motion.section
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
        className="mt-24 max-w-4xl w-full"
      >
        <h2 className="text-3xl font-bold text-center mb-12">
          How <span className="gradient-text">TeamGenie</span> Works
        </h2>
        <div className="grid md:grid-cols-3 gap-6">
          {[
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
          ].map((item) => (
            <motion.div
              key={item.step}
              whileHover={{ y: -4, scale: 1.02 }}
              className="glass-card p-6 cursor-default"
            >
              <div className="text-4xl mb-4">{item.icon}</div>
              <div className="text-xs text-indigo-400 font-mono mb-2">AGENT {item.step}</div>
              <h3 className="text-xl font-semibold mb-2">{item.title}</h3>
              <p className="text-gray-400 text-sm">{item.desc}</p>
            </motion.div>
          ))}
        </div>
      </motion.section>

      {/* Footer */}
      <footer className="mt-24 mb-8 text-center text-gray-600 text-sm">
        Built with ❤️ in Bhopal, India 🇮🇳 | © 2026 TeamGenie AI
      </footer>
    </main>
  );
}
