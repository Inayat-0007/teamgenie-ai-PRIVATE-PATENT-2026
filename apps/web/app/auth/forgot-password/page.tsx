"use client";

import { useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { KeyRound, ArrowLeft, AlertCircle, CheckCircle2, Loader2, Mail } from "lucide-react";
import { supabase } from "@/lib/supabase";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess(false);

    try {
      const { error: supaError } = await supabase.auth.resetPasswordForEmail(
        email.trim(),
        {
          redirectTo: `${window.location.origin}/auth/login`,
        }
      );

      if (supaError) {
        if (supaError.message.includes("Too many requests")) {
          setError("Too many attempts. Please wait a few minutes and try again.");
        } else {
          setError(supaError.message);
        }
        setLoading(false);
        return;
      }

      // Always show success — never reveal whether email exists or not (security best practice)
      setSuccess(true);
    } catch (err: any) {
      setError(err?.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

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
        {!success ? (
          <>
            <div className="text-center mb-8">
              <div className="mx-auto bg-rose-500/10 w-16 h-16 rounded-full flex items-center justify-center mb-4 border border-rose-500/20">
                <KeyRound className="h-8 w-8 text-rose-400" />
              </div>
              <h1 className="text-3xl font-bold text-white mb-2">Reset Password</h1>
              <p className="text-slate-400 text-sm">
                Enter your email address and we&apos;ll send you a link to reset your
                password.
              </p>
            </div>

            <form className="space-y-5" onSubmit={handleForgotPassword}>
              <div className="space-y-2">
                <label htmlFor="forgot-email" className="text-sm font-medium text-slate-300">
                  Email address
                </label>
                <input
                  id="forgot-email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className="w-full bg-slate-950/50 border border-slate-800 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-rose-500/50 transition-all"
                />
              </div>

              {/* Error */}
              {error && (
                <motion.div
                  initial={{ opacity: 0, y: -5 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-start space-x-2 text-rose-400 bg-rose-500/10 p-3 rounded-lg border border-rose-500/20 text-sm"
                >
                  <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                  <span>{error}</span>
                </motion.div>
              )}

              <button
                type="submit"
                disabled={loading}
                className={`w-full font-medium py-3 rounded-xl transition-all shadow-[0_0_20px_rgba(225,29,72,0.3)] mt-4 flex items-center justify-center gap-2 ${
                  loading
                    ? "bg-rose-600/50 text-rose-200 cursor-not-allowed"
                    : "bg-rose-600 hover:bg-rose-500 text-white"
                }`}
              >
                {loading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Sending...
                  </>
                ) : (
                  "Send Reset Link"
                )}
              </button>
            </form>
          </>
        ) : (
          /* Success state — email sent confirmation */
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.4 }}
            className="text-center py-4"
          >
            <div className="mx-auto bg-emerald-500/10 w-20 h-20 rounded-full flex items-center justify-center mb-6 border border-emerald-500/20">
              <Mail className="h-10 w-10 text-emerald-400" />
            </div>
            <h2 className="text-2xl font-bold text-white mb-3">Check Your Email</h2>
            <p className="text-slate-400 text-sm mb-2">
              If an account exists for{" "}
              <span className="text-white font-medium">{email}</span>, we&apos;ve
              sent a password reset link.
            </p>
            <p className="text-slate-500 text-xs mb-6">
              Didn&apos;t receive it? Check your spam folder or try again in a few
              minutes.
            </p>
            <button
              onClick={() => {
                setSuccess(false);
                setEmail("");
              }}
              className="text-sm text-rose-400 hover:text-rose-300 transition-colors"
            >
              Try a different email
            </button>
          </motion.div>
        )}

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
