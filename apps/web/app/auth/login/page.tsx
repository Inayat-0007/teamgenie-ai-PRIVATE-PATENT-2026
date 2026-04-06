"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Lock, AlertCircle, CheckCircle2, Eye, EyeOff, Loader2 } from "lucide-react";
import { supabase } from "@/lib/supabase";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const { data, error: supaError } = await supabase.auth.signInWithPassword({
        email: email.trim(),
        password,
      });

      if (supaError) {
        // Handle specific Supabase error codes with friendly messages
        if (supaError.message.includes("Invalid login credentials")) {
          setError("Invalid email or password. Please check your credentials and try again.");
        } else if (supaError.message.includes("Email not confirmed")) {
          setError(
            "Your email hasn't been confirmed yet. Please check your inbox for the confirmation link."
          );
        } else if (supaError.message.includes("Too many requests")) {
          setError("Too many login attempts. Please wait a moment and try again.");
        } else {
          setError(supaError.message);
        }
        setLoading(false);
        return;
      }

      if (data.session) {
        setSuccess("Welcome back! Redirecting...");
        setTimeout(() => router.push("/"), 1000);
      }
    } catch (err: any) {
      setError(err?.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-4">
      {/* Background glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-indigo-600/20 rounded-full blur-[150px] -z-10" />

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-md glass-panel p-8 rounded-3xl border-slate-700/50"
      >
        <div className="text-center mb-8">
          <div className="mx-auto bg-indigo-500/10 w-16 h-16 rounded-full flex items-center justify-center mb-4 border border-indigo-500/20">
            <Lock className="h-8 w-8 text-indigo-400" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Welcome Back</h1>
          <p className="text-slate-400">Sign in to your TeamGenie account</p>
        </div>

        <form className="space-y-5" onSubmit={handleLogin}>
          <div className="space-y-2">
            <label htmlFor="login-email" className="text-sm font-medium text-slate-300">
              Email address
            </label>
            <input
              id="login-email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full bg-slate-950/50 border border-slate-800 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
            />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label htmlFor="login-password" className="text-sm font-medium text-slate-300">
                Password
              </label>
              <Link
                href="/auth/forgot-password"
                className="text-xs text-indigo-400 hover:text-indigo-300"
              >
                Forgot password?
              </Link>
            </div>
            <div className="relative">
              <input
                id="login-password"
                type={showPassword ? "text" : "password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-950/50 border border-slate-800 rounded-xl px-4 py-3 pr-12 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 transition-all"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
              </button>
            </div>
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

          {/* Success */}
          {success && (
            <motion.div
              initial={{ opacity: 0, y: -5 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-start space-x-2 text-emerald-400 bg-emerald-500/10 p-3 rounded-lg border border-emerald-500/20 text-sm"
            >
              <CheckCircle2 className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <span>{success}</span>
            </motion.div>
          )}

          <button
            type="submit"
            disabled={loading || !!success}
            className={`w-full font-medium py-3 rounded-xl transition-all shadow-[0_0_20px_rgba(79,70,229,0.3)] mt-4 flex items-center justify-center gap-2 ${
              loading || success
                ? "bg-indigo-600/50 text-indigo-200 cursor-not-allowed"
                : "bg-indigo-600 hover:bg-indigo-500 text-white"
            }`}
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Signing in...
              </>
            ) : success ? (
              <>
                <CheckCircle2 className="w-5 h-5" />
                Signed In!
              </>
            ) : (
              "Sign In"
            )}
          </button>
        </form>

        <div className="mt-8 text-center text-sm text-slate-400">
          Don&apos;t have an account?{" "}
          <Link
            href="/auth/register"
            className="text-indigo-400 hover:text-indigo-300 font-medium"
          >
            Create an account
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
