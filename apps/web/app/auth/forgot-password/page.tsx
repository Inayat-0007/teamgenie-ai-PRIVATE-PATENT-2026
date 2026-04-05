"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { KeyRound, ArrowLeft } from "lucide-react";

export default function ForgotPasswordPage() {
  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-4">
      {/* Background glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-rose-600/20 rounded-full blur-[150px] -z-10" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-md glass-panel p-8 rounded-3xl border-slate-700/50"
      >
        <div className="text-center mb-8">
          <div className="mx-auto bg-rose-500/10 w-16 h-16 rounded-full flex items-center justify-center mb-4 border border-rose-500/20">
            <KeyRound className="h-8 w-8 text-rose-400" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Reset Password</h1>
          <p className="text-slate-400 text-sm">
            Enter your email address and we&apos;ll send you a link to reset your password.
          </p>
        </div>

        <form className="space-y-5" onSubmit={(e) => e.preventDefault()}>
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">Email address</label>
            <input
              type="email"
              placeholder="you@example.com"
              className="w-full bg-slate-950/50 border border-slate-800 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-rose-500/50 transition-all"
            />
          </div>

          <button
            type="button"
            className="w-full bg-rose-600 hover:bg-rose-500 text-white font-medium py-3 rounded-xl transition-all shadow-[0_0_20px_rgba(225,29,72,0.3)] mt-4"
          >
            Send Reset Link
          </button>
        </form>

        <div className="mt-8 text-center">
          <Link 
            href="/auth/login" 
            className="text-sm text-slate-400 hover:text-white transition-colors flex items-center justify-center space-x-2"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to login</span>
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
