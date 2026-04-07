"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Check, Zap, Terminal, Loader2, CreditCard, Shield, IndianRupee } from "lucide-react";
import Script from "next/script";
import { aiKit } from "@/lib/api";
import { supabase } from "@/lib/supabase";

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
      "Live ScoutFeed™ Reasoning",
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
      "Live ScoutFeed™ Reasoning",
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

// Extend window for Razorpay
declare global {
  interface Window {
    Razorpay: any;
  }
}

export default function PricingPage() {
  const [loadingTier, setLoadingTier] = useState<string | null>(null);

  const handleUpgrade = async (tierId: string) => {
    if (tierId === "free") return;
    setLoadingTier(tierId);
    
    try {
      // 1. Create order on backend
      const order = await aiKit.createOrder(tierId as "pro" | "elite");
      
      const { data: { user } } = await supabase.auth.getUser();

      // 2. Configure Razorpay
      const options = {
        key: order.key_id, 
        amount: order.amount,
        currency: order.currency,
        name: "TeamGenie AI",
        description: `Upgrade to ${tierId.toUpperCase()} Tier`,
        image: "/logo.png",
        order_id: order.order_id,
        handler: async function (response: any) {
          try {
             setLoadingTier(tierId); // Show loader during verification
             await aiKit.verifyPayment({
               razorpay_order_id: response.razorpay_order_id,
               razorpay_payment_id: response.razorpay_payment_id,
               razorpay_signature: response.razorpay_signature,
               plan_id: tierId
             });
             alert("Subscription upgraded successfully!");
             window.location.href = "/dashboard";
          } catch (err) {
             console.error("Verification failed:", err);
             alert("Payment verified but account update failed. Contact support.");
          } finally {
             setLoadingTier(null);
          }
        },
        prefill: {
          name: user?.user_metadata?.full_name || "",
          email: user?.email || "",
        },
        theme: {
          color: "#10b981", // Emerald 500
        },
      };

      const rzp = new window.Razorpay(options);
      rzp.on('payment.failed', function (response: any) {
         console.error("Payment failed:", response.error);
         alert(`Payment failed: ${response.error.description}`);
         setLoadingTier(null);
      });
      rzp.open();
    } catch (e) {
      console.error("Payment Init Error:", e);
      alert("Failed to initialize payment. Try again later.");
    } finally {
      setLoadingTier(null);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] text-white py-24 selection:bg-emerald-500/30">
      <Script src="https://checkout.razorpay.com/v1/checkout.js" />
      
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
    </div>
  );
}
