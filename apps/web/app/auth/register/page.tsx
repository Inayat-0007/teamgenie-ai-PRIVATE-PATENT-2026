"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { UserPlus, AlertCircle, CheckCircle2, Eye, EyeOff, Loader2 } from "lucide-react";
import { supabase } from "@/lib/supabase";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const getPasswordStrength = (pw: string) => {
    let score = 0;
    if (pw.length >= 8) score++;
    if (pw.length >= 12) score++;
    if (/[A-Z]/.test(pw)) score++;
    if (/[0-9]/.test(pw)) score++;
    if (/[^A-Za-z0-9]/.test(pw)) score++;
    return score;
  };

  const strengthLabels = ["Very Weak", "Weak", "Fair", "Strong", "Very Strong"];
  const strengthColors = [
    "bg-red-500",
    "bg-orange-500",
    "bg-yellow-500",
    "bg-emerald-500",
    "bg-green-400",
  ];
  const pwStrength = getPasswordStrength(password);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      setLoading(false);
      return;
    }

    try {
      // Try backend API first (uses service role key, auto-confirms email, bypasses rate limits)
      const backendRes = await fetch(`${API_URL}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.trim(),
          password,
          full_name: fullName.trim(),
        }),
      });

      const data = await backendRes.json();

      if (backendRes.ok) {
        // Backend registration succeeded — now sign in via Supabase to get a session
        if (data.access_token) {
          // Backend returned a token directly, try to set session
          await supabase.auth.setSession({
            access_token: data.access_token,
            refresh_token: data.refresh_token || "",
          });
          setSuccess("Account created! Redirecting to dashboard...");
          setTimeout(() => router.push("/"), 1500);
        } else {
          // Sign in with the newly created account
          const { data: signInData, error: signInError } = await supabase.auth.signInWithPassword({
            email: email.trim(),
            password,
          });

          if (signInError) {
            // Account created but login failed (maybe email confirmation needed)
            setSuccess(
              "Account created! Please check your email for a confirmation link, then sign in."
            );
          } else {
            setSuccess("Account created! Redirecting to dashboard...");
            setTimeout(() => router.push("/"), 1500);
          }
        }
      } else {
        // Backend returned an error
        const errorMsg =
          data?.detail?.message || data?.error?.message || data?.message || "Registration failed";

        if (errorMsg.toLowerCase().includes("rate") || errorMsg.toLowerCase().includes("limit")) {
          setError("Server is busy. Please wait 30 seconds and try again.");
        } else if (errorMsg.toLowerCase().includes("already exists")) {
          setError("An account with this email already exists. Try signing in instead.");
        } else {
          setError(errorMsg);
        }
      }
    } catch (err: any) {
      // Network error — try direct Supabase as fallback
      try {
        const { data, error: supaError } = await supabase.auth.signUp({
          email: email.trim(),
          password,
          options: {
            data: { full_name: fullName.trim() },
            emailRedirectTo: `${window.location.origin}/auth/callback`,
          },
        });

        if (supaError) {
          setError(supaError.message);
        } else if (data.session) {
          setSuccess("Account created! Redirecting to dashboard...");
          setTimeout(() => router.push("/"), 1500);
        } else {
          setSuccess("Account created! Check your email for a confirmation link.");
        }
      } catch {
        setError("Could not connect to the server. Please try again later.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-4">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-purple-600/20 rounded-full blur-[150px] -z-10" />

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="w-full max-w-md glass-panel p-8 rounded-3xl border-slate-700/50"
      >
        <div className="text-center mb-8">
          <div className="mx-auto bg-purple-500/10 w-16 h-16 rounded-full flex items-center justify-center mb-4 border border-purple-500/20">
            <UserPlus className="h-8 w-8 text-purple-400" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Create Account</h1>
          <p className="text-slate-400">Start optimizing your fantasy teams</p>
        </div>

        <form className="space-y-5" onSubmit={handleRegister}>
          <div className="space-y-2">
            <label htmlFor="register-name" className="text-sm font-medium text-slate-300">
              Full Name
            </label>
            <input
              id="register-name"
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Inayat Hussain"
              className="w-full bg-slate-950/50 border border-slate-800 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all"
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="register-email" className="text-sm font-medium text-slate-300">
              Email address
            </label>
            <input
              id="register-email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full bg-slate-950/50 border border-slate-800 rounded-xl px-4 py-3 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all"
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="register-password" className="text-sm font-medium text-slate-300">
              Password
            </label>
            <div className="relative">
              <input
                id="register-password"
                type={showPassword ? "text" : "password"}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                minLength={8}
                className="w-full bg-slate-950/50 border border-slate-800 rounded-xl px-4 py-3 pr-12 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-purple-500/50 transition-all"
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
            {password.length > 0 && (
              <div className="space-y-1 pt-1">
                <div className="flex gap-1">
                  {[0, 1, 2, 3, 4].map((i) => (
                    <div
                      key={i}
                      className={`h-1 flex-1 rounded-full transition-all duration-300 ${
                        i < pwStrength ? strengthColors[pwStrength - 1] : "bg-slate-800"
                      }`}
                    />
                  ))}
                </div>
                <p className="text-xs text-slate-500">
                  {strengthLabels[Math.max(0, pwStrength - 1)]}
                </p>
              </div>
            )}
          </div>

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
            className={`w-full font-medium py-3 rounded-xl transition-all shadow-[0_0_20px_rgba(147,51,234,0.3)] mt-4 flex items-center justify-center gap-2 ${
              loading || success
                ? "bg-purple-600/50 text-purple-200 cursor-not-allowed"
                : "bg-purple-600 hover:bg-purple-500 text-white"
            }`}
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Creating account...
              </>
            ) : success ? (
              <>
                <CheckCircle2 className="w-5 h-5" />
                Account Created!
              </>
            ) : (
              "Sign Up"
            )}
          </button>
        </form>

        <div className="mt-8 text-center text-sm text-slate-400">
          Already have an account?{" "}
          <Link href="/auth/login" className="text-purple-400 hover:text-purple-300 font-medium">
            Sign in
          </Link>
        </div>
      </motion.div>
    </div>
  );
}
