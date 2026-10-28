"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldAlert, ArrowRight, Lock, Mail, Sparkles, Building2 } from "lucide-react";
import { api } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("owner@apollo.com");
  const [password, setPassword] = useState("Password123!");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await api.login(email, password);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Invalid email or password");
    } finally {
      setLoading(false);
    }
  };

  const handleDemoPreset = (demoEmail: string) => {
    setEmail(demoEmail);
    setPassword("Password123!");
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center p-6 relative overflow-hidden bg-[#090D16]">
      {/* Background ambient glowing orbs */}
      <div className="absolute -top-40 -left-40 w-96 h-96 bg-emerald-500/15 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute -bottom-40 -right-40 w-96 h-96 bg-indigo-500/15 rounded-full blur-[120px] pointer-events-none" />

      <div className="w-full max-w-md relative z-10">
        {/* Brand Card */}
        <div className="glass-card rounded-2xl p-8 border border-slate-800 shadow-2xl relative">
          {/* Logo & Header */}
          <div className="text-center mb-8">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-emerald-500 to-teal-400 mx-auto flex items-center justify-center shadow-lg shadow-emerald-500/30 mb-3">
              <ShieldAlert className="w-6 h-6 text-slate-950 stroke-[2.5]" />
            </div>
            <h1 className="text-2xl font-extrabold text-white tracking-tight flex items-center justify-center space-x-1">
              <span>Expiry</span>
              <span className="text-emerald-400">OS</span>
            </h1>
            <p className="text-xs text-slate-400 mt-1">
              Multi-tenant Pharmacy Expiry & Distributor Return Automation
            </p>
          </div>

          {error && (
            <div className="mb-6 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-medium flex items-center space-x-2">
              <span className="w-1.5 h-1.5 rounded-full bg-rose-400" />
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Work Email
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  placeholder="pharmacist@pharmacy.com"
                  className="w-full bg-[#0D1322] border border-slate-700/80 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/40 transition-all"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-500" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  placeholder="••••••••••••"
                  className="w-full bg-[#0D1322] border border-slate-700/80 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500/40 transition-all"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-3 px-4 rounded-xl font-semibold text-sm bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-slate-950 shadow-lg shadow-emerald-500/25 flex items-center justify-center space-x-2 transition-all hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50"
            >
              <span>{loading ? "Authenticating..." : "Sign In to ExpiryOS"}</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Quick Demo Credentials Presets */}
          <div className="mt-8 pt-6 border-t border-slate-800">
            <div className="flex items-center space-x-2 text-[11px] font-semibold text-slate-400 mb-3 uppercase tracking-wider">
              <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
              <span>Quick Demo Role Presets:</span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleDemoPreset("owner@apollo.com")}
                className={`px-2.5 py-2 rounded-xl text-xs font-medium border text-center transition-all ${
                  email === "owner@apollo.com"
                    ? "bg-emerald-500/15 border-emerald-500/40 text-emerald-300"
                    : "bg-[#0D1322] border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700"
                }`}
              >
                Owner
              </button>
              <button
                type="button"
                onClick={() => handleDemoPreset("pharmacist@apollo.com")}
                className={`px-2.5 py-2 rounded-xl text-xs font-medium border text-center transition-all ${
                  email === "pharmacist@apollo.com"
                    ? "bg-emerald-500/15 border-emerald-500/40 text-emerald-300"
                    : "bg-[#0D1322] border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700"
                }`}
              >
                Pharmacist
              </button>
              <button
                type="button"
                onClick={() => handleDemoPreset("staff@apollo.com")}
                className={`px-2.5 py-2 rounded-xl text-xs font-medium border text-center transition-all ${
                  email === "staff@apollo.com"
                    ? "bg-emerald-500/15 border-emerald-500/40 text-emerald-300"
                    : "bg-[#0D1322] border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700"
                }`}
              >
                Staff
              </button>
            </div>
          </div>

          {/* Tenant Pill */}
          <div className="mt-6 flex items-center justify-center space-x-2 text-[11px] text-slate-500">
            <Building2 className="w-3.5 h-3.5" />
            <span>Target Tenant: Apollo Healthcare & Retail Pharmacy</span>
          </div>
        </div>
      </div>
    </div>
  );
}
