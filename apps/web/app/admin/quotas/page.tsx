"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Shield, Activity, Users, Zap, Calendar, TrendingUp } from "lucide-react";
import { aiKit } from "@/lib/api";

export default function AdminQuotasPage() {
  const [quotas, setQuotas] = useState<any[]>([]);
  const [stats, setStats] = useState<any>({ total_users: 0, total_teams: 0, active_subscriptions: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadAdminData() {
      try {
        const [quotaData, statsData] = await Promise.all([
          aiKit.getAdminQuotas(),
          aiKit.getAdminStats()
        ]);
        setQuotas(quotaData);
        setStats(statsData);
      } catch (err) {
        setError("You do not have administrative access to this page.");
      } finally {
        setLoading(false);
      }
    }
    loadAdminData();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Activity className="w-12 h-12 text-indigo-500 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-xl mx-auto px-4 py-32 text-center">
        <Shield className="w-16 h-16 text-rose-500 mx-auto mb-6" />
        <h1 className="text-3xl font-bold text-white mb-4">Access Restricted</h1>
        <p className="text-slate-400 mb-8">{error}</p>
        <a href="/" className="bg-indigo-600 hover:bg-indigo-700 px-6 py-3 rounded-lg font-bold transition-all">
          Return to Dashboard
        </a>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-12 mt-8">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center space-x-4 mb-4">
          <div className="p-3 bg-indigo-500/10 rounded-xl border border-indigo-500/20">
            <Shield className="w-8 h-8 text-indigo-400" />
          </div>
          <h1 className="text-4xl font-extrabold text-white tracking-tight">Admin Terminal</h1>
        </div>
        <p className="text-slate-400 max-w-2xl text-lg">
          Operational oversight of the TeamGenie AI infrastructure. Monitoring usage quotas and subscription lifecycles.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        <StatCard icon={<Users />} label="Total Users" value={stats.total_users} color="text-blue-400" />
        <StatCard icon={<Zap />} label="Active Squads Generated" value={stats.total_teams} color="text-amber-400" />
        <StatCard icon={<TrendingUp />} label="Pro Subscriptions" value={stats.active_subscriptions} color="text-emerald-400" />
      </div>

      {/* Quotas Table */}
      <div className="glass-panel border-slate-800 rounded-3xl overflow-hidden shadow-2xl">
        <div className="px-8 py-6 border-b border-slate-800 bg-slate-900/50 flex justify-between items-center">
          <h2 className="text-xl font-bold text-white flex items-center">
            <Activity className="w-5 h-5 mr-3 text-indigo-400" />
            Live Usage Monitoring
          </h2>
          <span className="text-xs font-mono text-slate-500 bg-slate-950 px-3 py-1 rounded-full border border-slate-800">
            Last 100 entries
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-slate-950 text-slate-500 text-xs uppercase tracking-wider text-left">
                <th className="px-8 py-4 font-bold">User Information</th>
                <th className="px-8 py-4 font-bold text-center">Date</th>
                <th className="px-8 py-4 font-bold text-center">Squad Generations</th>
                <th className="px-8 py-4 font-bold text-center">API Calls</th>
                <th className="px-8 py-4 font-bold text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {quotas.map((q, i) => (
                <motion.tr 
                  key={`${q.email}-${q.date}`}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.02 }}
                  className="hover:bg-indigo-500/5 transition-colors group"
                >
                  <td className="px-8 py-5">
                    <div className="flex items-center space-x-4">
                      <div className="w-10 h-10 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-indigo-400 group-hover:scale-110 transition-transform">
                        {q.email.charAt(0).toUpperCase()}
                      </div>
                      <span className="text-white font-medium text-sm">{q.email}</span>
                    </div>
                  </td>
                  <td className="px-8 py-5 text-center">
                    <div className="flex items-center justify-center space-x-2 text-slate-400 text-xs">
                      <Calendar className="w-3.5 h-3.5" />
                      <span>{q.date}</span>
                    </div>
                  </td>
                  <td className="px-8 py-5 text-center font-bold text-white text-lg">{q.generations}</td>
                  <td className="px-8 py-5 text-center text-slate-300 font-mono text-sm">{q.api_calls}</td>
                  <td className="px-8 py-5 text-center">
                     <span className={`px-3 py-1 rounded-full text-[10px] font-bold tracking-widest uppercase ${q.generations > 2 ? 'bg-amber-500/10 text-amber-400' : 'bg-emerald-500/10 text-emerald-400'}`}>
                        {q.generations > 2 ? 'Heavy' : 'Normal'}
                     </span>
                  </td>
                </motion.tr>
              ))}
              {quotas.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-8 py-20 text-center text-slate-500 italic">
                    No residential activity detected in the current audit period.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, color }: { icon: React.ReactNode, label: string, value: any, color: string }) {
  return (
    <div className="glass-panel border-slate-800 p-8 rounded-3xl group hover:border-slate-700 transition-all shadow-xl">
      <div className="flex items-center space-x-4 mb-4">
        <div className={`p-2 rounded-lg bg-slate-900 border border-slate-800 ${color}`}>
          {icon}
        </div>
        <span className="text-slate-400 font-medium text-sm">{label}</span>
      </div>
      <div className={`text-4xl font-extrabold ${color} group-hover:scale-105 transition-transform origin-left`}>
        {value}
      </div>
    </div>
  );
}
