"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import { Loader2, CheckCircle2, AlertCircle } from "lucide-react";

export default function AuthCallbackPage() {
  const router = useRouter();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
  const [message, setMessage] = useState("Verifying your email...");

  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Supabase handles the token exchange automatically via the URL hash
        const { data: { session }, error } = await supabase.auth.getSession();

        if (error) {
          setStatus("error");
          setMessage(error.message);
          return;
        }

        if (session) {
          setStatus("success");
          setMessage("Email confirmed! Redirecting to dashboard...");
          setTimeout(() => router.push("/"), 2000);
        } else {
          setStatus("success");
          setMessage("Email confirmed! You can now sign in.");
          setTimeout(() => router.push("/auth/login"), 2000);
        }
      } catch {
        setStatus("error");
        setMessage("Something went wrong during verification.");
      }
    };

    handleCallback();
  }, [router]);

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-4">
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-indigo-600/20 rounded-full blur-[150px] -z-10" />
      
      <div className="w-full max-w-md glass-panel p-8 rounded-3xl border-slate-700/50 text-center">
        {status === "loading" && (
          <>
            <Loader2 className="w-12 h-12 text-indigo-400 animate-spin mx-auto mb-4" />
            <h2 className="text-xl font-bold text-white mb-2">Verifying</h2>
          </>
        )}
        {status === "success" && (
          <>
            <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-white mb-2">Success!</h2>
          </>
        )}
        {status === "error" && (
          <>
            <AlertCircle className="w-12 h-12 text-rose-400 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-white mb-2">Error</h2>
          </>
        )}
        <p className="text-slate-400">{message}</p>
      </div>
    </div>
  );
}
