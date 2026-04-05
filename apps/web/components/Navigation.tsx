"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Zap, Home, Users, Search, BrainCircuit, Database, CreditCard } from "lucide-react";
import { cn } from "@/lib/utils";
import { motion } from "framer-motion";

export function Navigation() {
  const pathname = usePathname();

  const routes = [
    { href: "/", label: "Home", icon: Home },
    { href: "/team/generate", label: "PRO Gen", icon: Zap },
    { href: "/chat", label: "Elite Terminal", icon: BrainCircuit },
    { href: "/matches", label: "Matches", icon: Search },
    { href: "/pricing", label: "Pricing", icon: CreditCard },
    { href: "/players", label: "Players", icon: Database },
    { href: "/history", label: "My Squads", icon: Users },
  ];

  return (
    <nav className="fixed top-0 w-full z-50 glass-panel border-b-0 border-t-0 border-l-0 border-r-0 border-slate-800/80 supports-[backdrop-filter]:bg-slate-950/60">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <Link href="/" className="flex items-center space-x-2 group">
            <div className="bg-gradient-to-br from-indigo-500 to-purple-600 p-2 rounded-xl group-hover:shadow-[0_0_20px_rgba(99,102,241,0.5)] transition-all duration-300">
              <BrainCircuit className="h-5 w-5 text-white" />
            </div>
            <span className="font-bold text-xl tracking-tight text-white">
              TeamGenie<span className="text-indigo-400">.ai</span>
            </span>
          </Link>

          <div className="hidden lg:flex space-x-1">
            {routes.map((route) => {
              const active = pathname === route.href;
              const Icon = route.icon;
              return (
                <Link
                  key={route.href}
                  href={route.href}
                  className={cn(
                    "relative px-3 py-2 text-sm font-medium rounded-full transition-colors",
                    active ? "text-white" : "text-slate-400 hover:text-white hover:bg-slate-800/50"
                  )}
                >
                  <span className="relative z-10 flex items-center space-x-2">
                    <Icon className="h-4 w-4" />
                    <span>{route.label}</span>
                  </span>
                  {active && (
                    <motion.div
                      layoutId="nav-active"
                      className="absolute inset-0 bg-slate-800 rounded-full"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ duration: 0.2 }}
                    />
                  )}
                </Link>
              );
            })}
          </div>

          <div className="flex items-center space-x-4">
            <Link
              href="/auth/login"
              className="text-sm font-medium text-slate-300 hover:text-white transition-colors flex items-center space-x-2"
            >
               <span>Sign in</span>
            </Link>
            <Link
              href="/auth/register"
              className="bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium px-4 py-2 rounded-full transition-all shadow-[0_0_15px_rgba(79,70,229,0.3)] hover:shadow-[0_0_25px_rgba(79,70,229,0.5)]"
            >
              Get Started
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
