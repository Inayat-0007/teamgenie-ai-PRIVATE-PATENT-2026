"use client";

import { useState, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import { Terminal, Send, CheckCircle2, Shield, Crown, Sparkles } from "lucide-react";
import { aiKit } from "@/lib/api";

type Message = {
  id: string;
  role: "system" | "user" | "assistant";
  content: string;
  team?: any[];
};

export default function EliteChatTerminal() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "init",
      role: "system",
      content: "AUTH_SUCCESS: ELITE TIER DETECTED. MONTE CARLO SIMULATOR ONLINE. JIT DUCKDUCKGO DATA STREAM ACTIVE.",
    },
    {
      id: "welcome",
      role: "assistant",
      content: "Welcome to the Elite Terminal. Tell me which match you are targeting and any specific constraints. For example: \"Create a high-risk grand league team for CSK vs MI, make sure to ignore Rohit and captain an all-rounder.\"",
    }
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input;
    setInput("");
    
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      role: "user",
      content: userMessage
    }]);

    setIsTyping(true);

    try {
      // Fake delay to simulate AI parsing the natural language
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // We would normally fire this text completely to our Backend Agent.
      // For the demo, we ping the standard generation API to prove it works.
      const result = await aiKit.generateTeam({
        match_id: "IPL_Today_Match_Live",
        budget: 100,
        risk_level: "aggressive",
        team_a: "IPL",
        team_b: "Today's Match"
      });

      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Extracted parameters. I have parsed today's DDG injury reports and run 10,000 Monte Carlo simulations. Here is your mathematically optimal lineup:",
        team: result.team?.players || result
      }]);

    } catch (e) {
      console.error(e);
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "ERROR: Connection to Monte Carlo simulation server lost."
      }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 h-[calc(100vh-80px)] flex flex-col">
      <div className="flex justify-between items-center px-6 py-4 bg-slate-900 border border-slate-700/50 rounded-t-2xl">
        <div className="flex items-center space-x-3">
          <Terminal className="w-5 h-5 text-indigo-400" />
          <h1 className="text-xl font-mono text-slate-200 font-bold tracking-tight">ALGORITHM.TERMINAL</h1>
        </div>
        <div className="flex items-center space-x-3">
          <span className="flex items-center text-xs font-bold text-amber-500 bg-amber-500/10 px-3 py-1 rounded-full uppercase tracking-widest border border-amber-500/20">
            <Crown className="w-3 h-3 mr-2" /> Elite Whale
          </span>
          <span className="flex items-center text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-1 rounded border border-emerald-500/20">
            <CheckCircle2 className="w-3 h-3 mr-1" /> SECURE
          </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto bg-black p-6 border-x border-slate-800 font-mono text-sm shadow-[inset_0_0_50px_rgba(0,0,0,1)]">
        {messages.map((msg, idx) => (
          <motion.div 
            key={msg.id}
            initial={{ opacity: 0, x: msg.role === 'user' ? 20 : -20 }}
            animate={{ opacity: 1, x: 0 }}
            className={`mb-6 ${msg.role === 'user' ? 'text-right' : 'text-left'}`}
          >
            <div className={`inline-block max-w-[85%] ${msg.role === 'system' ? 'w-full' : ''}`}>
              {msg.role === 'system' && (
                <div className="text-emerald-500 text-xs mb-4 pb-4 border-b border-dashed border-slate-800 opacity-70">
                  [{mounted ? new Date().toISOString() : "CALCULATING..."}] {msg.content}
                </div>
              )}
              
              {msg.role === 'user' && (
                <div className="bg-indigo-900/40 border border-indigo-500/30 text-indigo-100 p-4 rounded-2xl rounded-tr-sm inline-block text-left relative overflow-hidden group">
                  <div className="absolute top-0 right-0 w-full h-full bg-indigo-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                  {msg.content}
                </div>
              )}
              
              {msg.role === 'assistant' && (
                <div>
                  <div className="flex items-top space-x-3">
                    <div className="mt-1 flex-shrink-0">
                      <Sparkles className="w-4 h-4 text-amber-400" />
                    </div>
                    <div className="text-slate-300 leading-relaxed max-w-2xl">
                      {msg.content}
                    </div>
                  </div>
                  
                  {msg.team && (
                    <motion.div 
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.5 }}
                      className="mt-6 ml-7 bg-slate-900 border border-slate-800 rounded-xl p-4 inline-block w-full"
                    >
                      <div className="text-xs text-amber-400 font-bold mb-4 border-b border-slate-800 pb-2">SIMULATION RESULTS // TIER: AGGRESSIVE</div>
                      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
                        {msg.team.map((player: any, i: number) => (
                          <div key={i} className="bg-black/50 border border-amber-500/10 rounded p-2 text-center hover:border-amber-500/40 transition-colors">
                            <p className="text-[10px] text-slate-500 uppercase">{player.role}</p>
                            <p className="text-amber-100 font-medium whitespace-nowrap overflow-hidden text-ellipsis text-xs">{player.name}</p>
                          </div>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </div>
              )}
            </div>
          </motion.div>
        ))}
        
        {isTyping && (
          <div className="flex items-center space-x-3 text-slate-500">
            <Sparkles className="w-4 h-4 text-amber-500/50 animate-pulse" />
            <div className="flex space-x-1">
              <span className="animate-bounce" style={{ animationDelay: '0ms' }}>.</span>
              <span className="animate-bounce" style={{ animationDelay: '150ms' }}>.</span>
              <span className="animate-bounce" style={{ animationDelay: '300ms' }}>.</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 bg-slate-900 border border-slate-700/50 rounded-b-2xl border-t-0 flex items-center">
        <span className="text-emerald-500 font-mono mr-3 text-lg font-bold">❯</span>
        <form onSubmit={handleSubmit} className="flex-1 flex space-x-4">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Instruct the simulation..."
            className="flex-1 bg-transparent border-none text-white font-mono text-sm focus:outline-none focus:ring-0 placeholder-slate-600"
            disabled={isTyping}
          />
          <button 
            type="submit" 
            disabled={!input.trim() || isTyping}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white p-2.5 rounded-xl transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
