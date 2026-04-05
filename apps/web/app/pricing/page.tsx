"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check, Zap, Terminal, Loader2, CreditCard, Shield, IndianRupee } from "lucide-react";

const TIERS = [
  {
    id: "free",
    name: "Casual Player",
    price: "₹0",
    period: "forever",
    description: "Perfect for quick, casual games with friends.",
    icon: <Shield className="w-6 h-6 text-gray-400" />,
    features: [
      "2 AI Generations per week",
      "1-Click Team Generation",
      "Standard Budget Optimizer",
      "Basic Injury Filters",
    ],
    disabledFeatures: [
      "Live Toss Intelligence",
      "Live ScoutFeed\u2122 Reasoning",
      "Differential Expert Mode",
      "Elite Bloomberg Terminal",
    ],
    cta: "Current Plan",
    popular: false,
  },
  {
    id: "pro",
    name: "Pro Strategist",
    price: "₹199",
    period: "per month",
    description: "For serious fantasy players playing head-to-head leagues.",
    icon: <Zap className="w-6 h-6 text-yellow-400" />,
    features: [
      "3 AI Generations per day",
      "Live Toss Intelligence Engine",
      "Live ScoutFeed\u2122 Reasoning",
      "Google OR-Tools Math Engine",
      "Risk Profile Configuration (Safe/Aggressive)",
    ],
    disabledFeatures: [
      "Elite Bloomberg Terminal",
      "Unlimited Generations",
    ],
    cta: "Upgrade to PRO",
    popular: true,
  },
  {
    id: "elite",
    name: "Elite Whale",
    price: "₹999",
    period: "per month",
    description: "For Grand League dominators requiring full AI control.",
    icon: <Terminal className="w-6 h-6 text-emerald-400" />,
    features: [
      "UNLIMITED Generatons",
      "Full Elite Bloomberg Terminal Access",
      "Natural Language Scenario Parsing",
      "Differential Expert Mode (<25% ownership)",
      "Priority API Generation Speed",
    ],
    disabledFeatures: [],
    cta: "Upgrade to ELITE",
    popular: false,
  }
];

export default function PricingPage() {
  const [loadingTier, setLoadingTier] = useState<string | null>(null);
  const [showSimulatedModal, setShowSimulatedModal] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);

  const handleUpgrade = (tierId: string) => {
    if (tierId === "free") return;
    setLoadingTier(tierId);
    
    // Simulate Razorpay initialization delay
    setTimeout(() => {
      setLoadingTier(null);
      setSelectedPlan(tierId);
      setShowSimulatedModal(true);
    }, 1200);
  };

  return (
    <div className="min-h-screen bg-[#050505] text-white py-24 selection:bg-emerald-500/30">
      
      {/* Background Ambience */}
      <div className="fixed inset-0 pointer-events-none opacity-20">
        <div className="absolute top-0 right-1/4 w-[40vw] h-[40vw] bg-emerald-500/20 rounded-full blur-[120px]" />
        <div className="absolute bottom-0 left-1/4 w-[30vw] h-[30vw] bg-blue-600/20 rounded-full blur-[100px]" />
      </div>

      <div className="max-w-7xl mx-auto px-6 relative z-10">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h1 className="text-5xl md:text-6xl font-black mb-6 bg-gradient-to-r from-emerald-400 to-blue-500 text-transparent bg-clip-text tracking-tight">
              Unlock the Ultimate Edge
            </h1>
            <p className="text-xl text-gray-400">
              Stop guessing. Start winning. Let exactly calculated mathematics and live JIT intelligence build your 11-player squad.
            </p>
          </motion.div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-center max-w-6xl mx-auto">
          {TIERS.map((tier, index) => (
            <motion.div
              key={tier.id}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.15 }}
              className={`relative rounded-3xl backdrop-blur-md transition-all duration-300 ${
                tier.popular 
                  ? 'bg-gradient-to-b from-[#151a15] to-[#0a0f0a] border border-emerald-500/40 shadow-2xl shadow-emerald-900/20 scale-105 z-10' 
                  : 'bg-white/5 border border-white/10 hover:border-white/20'
              } p-8`}
            >
              {tier.popular && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-gradient-to-r from-emerald-500 to-emerald-400 text-black text-sm font-bold rounded-full uppercase tracking-wider">
                  Most Popular
                </div>
              )}

              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-semibold text-gray-200">{tier.name}</h3>
                {tier.icon}
              </div>

              <div className="mb-6 flex items-baseline">
                <span className="text-4xl font-black">{tier.price}</span>
                <span className="text-gray-500 ml-2">/{tier.period}</span>
              </div>

              <p className="text-gray-400 text-sm mb-8 h-10">{tier.description}</p>

              <button
                onClick={() => handleUpgrade(tier.id)}
                disabled={tier.id === "free" || loadingTier !== null}
                className={`w-full py-4 rounded-xl font-bold transition-all flex justify-center items-center ${
                  tier.id === 'free'
                    ? 'bg-white/5 text-gray-500 border border-white/10 cursor-not-allowed'
                    : tier.popular
                      ? 'bg-emerald-500 hover:bg-emerald-400 text-black shadow-lg shadow-emerald-500/25'
                      : 'bg-white text-black hover:bg-gray-100'
                }`}
              >
                {loadingTier === tier.id ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  tier.cta
                )}
              </button>

              <div className="mt-8 space-y-4">
                {tier.features.map((feature, i) => (
                  <div key={i} className="flex items-start">
                    <Check className={`w-5 h-5 mr-3 shrink-0 ${tier.popular ? 'text-emerald-400' : 'text-gray-300'}`} />
                    <span className="text-gray-200 text-sm">{feature}</span>
                  </div>
                ))}
                
                {tier.disabledFeatures.map((feature, i) => (
                  <div key={`disabled-${i}`} className="flex items-start opacity-40">
                    <div className="w-5 h-5 mr-3 shrink-0 flex items-center justify-center">
                      <div className="w-1.5 h-1.5 rounded-full bg-gray-500" />
                    </div>
                    <span className="text-gray-500 text-sm line-through decoration-gray-600">{feature}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Simulated Razorpay Modal */}
      <AnimatePresence>
        {showSimulatedModal && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4"
              onClick={() => setShowSimulatedModal(false)}
            >
              {/* Modal window */}
              <motion.div
                initial={{ opacity: 0, scale: 0.95, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95, y: 20 }}
                onClick={(e) => e.stopPropagation()}
                className="bg-[#1a1a1a] border border-white/10 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl shadow-emerald-900/10 flex flex-col"
              >
                {/* Header (Razorpay Style) */}
                <div className="bg-gradient-to-r from-emerald-600 to-blue-600 p-6 text-center shadow-inner relative">
                  <button 
                    onClick={() => setShowSimulatedModal(false)}
                    className="absolute top-4 right-4 text-white/70 hover:text-white"
                  >
                    \u2715
                  </button>
                  <div className="w-16 h-16 bg-white rounded-xl shadow-md mx-auto mb-4 flex items-center justify-center">
                    <Shield className="w-8 h-8 text-emerald-600" />
                  </div>
                  <h2 className="text-xl font-bold text-white mb-1">TeamGenie AI Checkout</h2>
                  <p className="text-emerald-100/80 text-sm">
                    {selectedPlan === 'pro' ? 'Pro Strategist Tier' : 'Elite Whale Terminal'}
                  </p>
                </div>

                {/* Body */}
                <div className="p-6">
                  <div className="flex justify-between items-center mb-6 pb-6 border-b border-white/5">
                    <span className="text-gray-400">Total Amount Payable</span>
                    <span className="text-3xl font-black text-white flex items-center">
                      <IndianRupee className="w-6 h-6 mr-1" />
                      {selectedPlan === 'pro' ? '199' : '999'}
                    </span>
                  </div>

                  <div className="space-y-4">
                    <h4 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-2">Simulated Gateway</h4>
                    
                    <button 
                      onClick={() => {
                        alert(`Success! Handled by simulated Razorpay. Tier upgraded to ${selectedPlan!.toUpperCase()}`);
                        setShowSimulatedModal(false);
                      }}
                      className="w-full bg-white/5 hover:bg-white/10 border border-white/10 p-4 rounded-xl flex items-center justify-between transition-colors group"
                    >
                      <div className="flex items-center text-gray-200">
                        <CreditCard className="w-6 h-6 mr-3 text-emerald-400" />
                        Credit / Debit Card
                      </div>
                      <ChevronRight />
                    </button>

                    <button 
                      onClick={() => {
                        alert(`UPI Success! Handled by simulated Razorpay.`);
                        setShowSimulatedModal(false);
                      }}
                      className="w-full bg-white/5 hover:bg-white/10 border border-white/10 p-4 rounded-xl flex items-center justify-between transition-colors group"
                    >
                      <div className="flex items-center text-gray-200">
                        <ScanBarcode className="w-6 h-6 mr-3 text-blue-400" />
                        UPI / QR Code
                      </div>
                      <ChevronRight />
                    </button>
                  </div>
                </div>

                {/* Footer */}
                <div className="bg-black/40 p-4 text-center">
                  <span className="text-xs text-gray-500 inline-flex items-center">
                    <Shield className="w-3 h-3 mr-1" />
                    Secured by Razorpay Test API
                  </span>
                </div>
              </motion.div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

    </div>
  );
}

// Icons
function ChevronRight() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-gray-500 group-hover:text-emerald-400 transition-colors">
      <path d="m9 18 6-6-6-6"/>
    </svg>
  )
}

function ScanBarcode({ className }: { className?: string }) {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
      <path d="M3 7V5a2 2 0 0 1 2-2h2"/><path d="M17 3h2a2 2 0 0 1 2 2v2"/><path d="M21 17v2a2 2 0 0 1-2 2h-2"/><path d="M7 21H5a2 2 0 0 1-2-2v-2"/><rect width="7" height="5" x="7" y="7" rx="1"/><rect width="7" height="5" x="7" y="12" rx="1"/><path d="M17 7v10"/>
    </svg>
  )
}
