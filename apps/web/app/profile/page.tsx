"use client";

import { motion } from "framer-motion";
import { User, Mail, Shield, Bell, Settings, LogOut, CreditCard, Zap, Edit3, KeyRound } from "lucide-react";

export default function ProfilePage() {
  return (
    <div className="min-h-screen bg-[#050505] text-white py-24 selection:bg-indigo-500/30">
      {/* Background Ambience */}
      <div className="fixed inset-0 pointer-events-none opacity-20">
        <div className="absolute top-1/4 left-1/4 w-[40vw] h-[40vw] bg-indigo-500/20 rounded-full blur-[120px]" />
        <div className="absolute bottom-1/4 right-1/4 w-[30vw] h-[30vw] bg-purple-600/20 rounded-full blur-[100px]" />
      </div>

      <div className="max-w-4xl mx-auto px-6 relative z-10">
        <div className="mb-12">
          <motion.h1 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="text-4xl font-black bg-gradient-to-r from-indigo-400 to-purple-400 text-transparent bg-clip-text"
          >
            My Account
          </motion.h1>
          <motion.p 
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
            className="text-gray-400 mt-2"
          >
            Manage your profile, preferences, and subscription.
          </motion.p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          
          {/* Left Column - Navigation & User Card */}
          <div className="space-y-6">
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white/5 border border-white/10 rounded-3xl p-6 backdrop-blur-sm text-center relative overflow-hidden"
            >
              <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 to-purple-500" />
              <div className="relative inline-block mb-4">
                <div className="w-24 h-24 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 p-1 mx-auto">
                  <div className="w-full h-full bg-[#111] rounded-full flex items-center justify-center">
                    <User className="w-10 h-10 text-white/50" />
                  </div>
                </div>
                <button className="absolute bottom-0 right-0 p-2 bg-indigo-500 rounded-full shadow-lg border-2 border-[#111] hover:scale-110 transition-transform">
                  <Edit3 className="w-4 h-4 text-white" />
                </button>
              </div>
              <h2 className="text-xl font-bold">Mohammed Inayat</h2>
              <p className="text-gray-400 text-sm">mohammed@inayat.com</p>
              
              <div className="mt-6 pt-6 border-t border-white/10 flex justify-between items-center px-2">
                <div className="text-left">
                  <p className="text-xs text-gray-500 uppercase tracking-widest font-semibold">Tier</p>
                  <p className="text-emerald-400 font-bold flex items-center"><Zap className="w-3 h-3 mr-1" /> PRO</p>
                </div>
                <div className="text-right">
                  <p className="text-xs text-gray-500 uppercase tracking-widest font-semibold">Quotas</p>
                  <p className="text-white font-bold">1/3 Used</p>
                </div>
              </div>
            </motion.div>

            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white/5 border border-white/10 rounded-2xl p-2 backdrop-blur-sm"
            >
              <nav className="space-y-1">
                <a href="#" className="flex items-center px-4 py-3 bg-white/10 text-white rounded-xl font-medium">
                  <User className="w-5 h-5 mr-3 text-indigo-400" /> Personal Info
                </a>
                <a href="#" className="flex items-center px-4 py-3 text-gray-400 hover:text-white hover:bg-white/5 rounded-xl font-medium transition-colors">
                  <Shield className="w-5 h-5 mr-3" /> Security
                </a>
                <a href="/pricing" className="flex items-center px-4 py-3 text-gray-400 hover:text-white hover:bg-white/5 rounded-xl font-medium transition-colors">
                  <CreditCard className="w-5 h-5 mr-3" /> Subscription
                </a>
                <a href="#" className="flex items-center px-4 py-3 text-gray-400 hover:text-white hover:bg-white/5 rounded-xl font-medium transition-colors">
                  <Bell className="w-5 h-5 mr-3" /> Notifications
                </a>
              </nav>
            </motion.div>
          </div>

          {/* Right Column - Main Content Form */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="md:col-span-2 space-y-6"
          >
            {/* Personal Details */}
            <div className="bg-white/5 border border-white/10 rounded-3xl p-8 backdrop-blur-sm">
              <h3 className="text-xl font-semibold mb-6 flex items-center">
                <User className="w-5 h-5 mr-2 text-indigo-400" />
                Personal Information
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">First Name</label>
                  <input 
                    type="text" 
                    defaultValue="Mohammed"
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-2">Last Name</label>
                  <input 
                    type="text" 
                    defaultValue="Inayat"
                    className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
                  />
                </div>
                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-gray-400 mb-2">Email Address</label>
                  <div className="relative">
                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                    <input 
                      type="email" 
                      defaultValue="mohammed@inayat.com"
                      readOnly
                      className="w-full bg-black/40 border border-white/10 rounded-xl pl-12 pr-4 py-3 text-gray-400 focus:outline-none cursor-not-allowed"
                    />
                  </div>
                </div>
              </div>
              <div className="mt-8 flex justify-end">
                <button className="bg-white text-black font-bold px-6 py-3 rounded-xl hover:bg-gray-200 transition-colors">
                  Save Changes
                </button>
              </div>
            </div>

            {/* Security Section */}
            <div className="bg-white/5 border border-white/10 rounded-3xl p-8 backdrop-blur-sm">
              <h3 className="text-xl font-semibold mb-6 flex items-center">
                <KeyRound className="w-5 h-5 mr-2 text-indigo-400" />
                Password & Security
              </h3>
              <div className="space-y-4">
                <button className="w-full bg-black/40 border border-white/10 hover:border-white/30 p-4 rounded-xl flex items-center justify-between transition-colors">
                  <div className="flex items-center text-left">
                    <div className="bg-indigo-500/20 p-2 rounded-lg mr-4">
                      <KeyRound className="w-5 h-5 text-indigo-400" />
                    </div>
                    <div>
                      <p className="font-semibold text-white">Change Password</p>
                      <p className="text-sm text-gray-500">Update your account password</p>
                    </div>
                  </div>
                  <ChevronRight />
                </button>
                <button className="w-full bg-black/40 border border-white/10 hover:border-white/30 p-4 rounded-xl flex items-center justify-between transition-colors">
                  <div className="flex items-center text-left">
                    <div className="bg-purple-500/20 p-2 rounded-lg mr-4">
                      <Shield className="w-5 h-5 text-purple-400" />
                    </div>
                    <div>
                      <p className="font-semibold text-white">Two-Factor Authentication</p>
                      <p className="text-sm text-gray-500">Add an extra layer of security</p>
                    </div>
                  </div>
                  <div className="px-3 py-1 bg-gray-800 text-gray-400 text-xs rounded-full font-semibold uppercase tracking-wider">
                    Disabled
                  </div>
                </button>
              </div>
            </div>

            {/* Danger Zone */}
            <div className="mt-12 flex justify-center">
              <button className="flex items-center text-red-500 hover:text-red-400 font-medium transition-colors">
                <LogOut className="w-4 h-4 mr-2" />
                Sign out of all devices
              </button>
            </div>
            
          </motion.div>
        </div>
      </div>
    </div>
  );
}

function ChevronRight() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-gray-500">
      <path d="m9 18 6-6-6-6"/>
    </svg>
  );
}
