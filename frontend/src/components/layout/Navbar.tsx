"use client";

import React, { useState, useEffect } from "react";
import { Search, Bell, Sparkles, CheckCircle2, UserCheck, Shield } from "lucide-react";
import { api } from "@/lib/api";

interface NavbarProps {
  onAutoDraftSuccess?: () => void;
}

export default function Navbar({ onAutoDraftSuccess }: NavbarProps) {
  const [userName, setUserName] = useState("Dr. Vikram Mehta");
  const [userRole, setUserRole] = useState("owner");
  const [isDrafting, setIsDrafting] = useState(false);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("expiryos_user");
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          setUserName(parsed.full_name || "Pharmacist");
          setUserRole(parsed.role || "pharmacist");
        } catch (e) {
          // ignore
        }
      }
    }
  }, []);

  const handleTriggerAutoDraft = async () => {
    setIsDrafting(true);
    try {
      const res = await api.autoGenerateReturns();
      setToastMsg(`Generated ${res.length} return draft(s) successfully!`);
      setTimeout(() => setToastMsg(null), 4000);
      if (onAutoDraftSuccess) onAutoDraftSuccess();
    } catch (err: any) {
      setToastMsg(err.message || "Failed to trigger auto draft");
      setTimeout(() => setToastMsg(null), 4000);
    } finally {
      setIsDrafting(false);
    }
  };

  return (
    <header className="fixed top-0 right-0 left-64 h-16 bg-[#090D16]/90 backdrop-blur-md border-b border-[#1E293B] px-8 flex items-center justify-between z-20">
      {/* Toast alert popup */}
      {toastMsg && (
        <div className="absolute top-20 right-8 bg-[#161F33] border border-emerald-500/40 text-emerald-300 px-4 py-2.5 rounded-xl shadow-xl shadow-emerald-500/10 flex items-center space-x-2 text-sm z-50 animate-bounce">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Global Search Bar */}
      <div className="relative w-96">
        <Search className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          placeholder="Quick search SKU, batch, or distributor..."
          className="w-full bg-[#111726] border border-[#1E293B] rounded-xl pl-10 pr-4 py-2 text-sm text-slate-200 placeholder-slate-400 focus:outline-none focus:border-emerald-500/60 focus:ring-1 focus:ring-emerald-500/30 transition-all"
        />
      </div>

      {/* Action Area & Profile */}
      <div className="flex items-center space-x-4">
        {/* Run Auto-Draft Workflow Button */}
        <button
          onClick={handleTriggerAutoDraft}
          disabled={isDrafting}
          className="flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-slate-950 shadow-md shadow-emerald-500/20 transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50"
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>{isDrafting ? "Scanning Rules..." : "Auto-Draft Returns"}</span>
        </button>

        {/* Notification Bell */}
        <div className="relative p-2 rounded-xl bg-[#111726] border border-[#1E293B] text-slate-300 hover:text-white cursor-pointer transition-colors">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-emerald-400 ring-2 ring-[#111726]" />
        </div>

        {/* User Pill */}
        <div className="flex items-center space-x-3 pl-2 border-l border-[#1E293B]">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-500 to-emerald-400 p-[1px]">
            <div className="w-full h-full bg-[#111726] rounded-full flex items-center justify-center">
              <UserCheck className="w-4 h-4 text-emerald-400" />
            </div>
          </div>
          <div className="text-left">
            <div className="text-xs font-semibold text-slate-200 leading-tight">{userName}</div>
            <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider flex items-center space-x-1">
              <Shield className="w-2.5 h-2.5 text-indigo-400" />
              <span>{userRole}</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
