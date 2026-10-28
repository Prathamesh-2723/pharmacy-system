"use client";

import React, { useEffect, useState } from "react";
import {
  Building2,
  Sliders,
  Plus,
  ShieldCheck,
  Clock,
  Coins,
  CheckCircle2,
  X,
  AlertTriangle,
  History,
} from "lucide-react";
import { api } from "@/lib/api";
import { DistributorScorecard } from "@/types";

export default function DistributorsPage() {
  const [distributors, setDistributors] = useState<DistributorScorecard[]>([]);
  const [loading, setLoading] = useState(true);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  // Edit Rules Drawer State
  const [selectedDist, setSelectedDist] = useState<DistributorScorecard | null>(null);
  const [winStart, setWinStart] = useState(90);
  const [winEnd, setWinEnd] = useState(15);
  const [exclusions, setExclusions] = useState<string[]>([]);
  const [slaDays, setSlaDays] = useState(14);
  const [minVal, setMinVal] = useState(0.0);
  const [savingRules, setSavingRules] = useState(false);

  const loadDistributors = async () => {
    try {
      setLoading(true);
      const data = await api.getDistributors();
      setDistributors(data);
    } catch (err: any) {
      setToastMsg("Failed to load distributors scorecard");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDistributors();
  }, []);

  const handleOpenEditRules = (d: DistributorScorecard) => {
    setSelectedDist(d);
    const r = d.active_rule || ({} as any);
    setWinStart(r.return_window_start_days_before_expiry || 90);
    setWinEnd(r.return_window_end_days_before_expiry || 15);
    setExclusions(r.excluded_categories || []);
    setSlaDays(r.credit_note_sla_days || 14);
    setMinVal(Number(r.min_return_value || 0.0));
  };

  const handleSaveRuleVersion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDist) return;
    setSavingRules(true);

    try {
      await api.updateDistributorRules(selectedDist.id, {
        return_window_start_days_before_expiry: Number(winStart),
        return_window_end_days_before_expiry: Number(winEnd),
        excluded_categories: exclusions,
        requires_prior_authorization: false,
        return_format: "standard_v1",
        pickup_days: ["Monday", "Thursday"],
        credit_note_sla_days: Number(slaDays),
        min_return_value: Number(minVal),
      });
      setToastMsg(`Saved new return rule version for ${selectedDist.name}!`);
      setTimeout(() => setToastMsg(null), 4000);
      setSelectedDist(null);
      loadDistributors();
    } catch (err: any) {
      setToastMsg(err.message || "Failed to update rules");
      setTimeout(() => setToastMsg(null), 4000);
    } finally {
      setSavingRules(false);
    }
  };

  const toggleCategoryExclusion = (cat: string) => {
    if (exclusions.includes(cat)) {
      setExclusions(exclusions.filter((c) => c !== cat));
    } else {
      setExclusions([...exclusions, cat]);
    }
  };

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(val);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Toast Alert */}
      {toastMsg && (
        <div className="fixed top-20 right-8 bg-[#161F33] border border-emerald-500/40 text-emerald-300 px-4 py-2.5 rounded-xl shadow-xl z-50 flex items-center space-x-2 text-sm animate-bounce">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Distributor Scorecards & Return Policies
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Configurable distributor return parameters, turnaround SLAs, and credit note settlement tracking.
          </p>
        </div>

        <div className="text-xs text-slate-400 font-semibold bg-[#111726] border border-slate-800 px-3.5 py-2 rounded-xl">
          Total Distributors Managed: <span className="text-emerald-400 font-bold">{distributors.length}</span>
        </div>
      </div>

      {/* Distributors Scorecard Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {distributors.map((d) => {
          const rule = d.active_rule || ({} as any);
          return (
            <div
              key={d.id}
              className="glass-card rounded-2xl p-5 border border-slate-800 flex flex-col justify-between group hover:border-slate-700 transition-all"
            >
              <div>
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h2 className="text-sm font-bold text-white group-hover:text-emerald-300 transition-colors">
                      {d.name}
                    </h2>
                    <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                      Code: {d.code} • {d.phone || "No phone"}
                    </div>
                  </div>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">
                    Active Partner
                  </span>
                </div>

                {/* Return Rule Details Box */}
                <div className="p-3 rounded-xl bg-[#0B101D] border border-slate-800/80 space-y-2 mb-4">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">Return Window:</span>
                    <span className="font-semibold text-slate-200">
                      {rule.return_window_start_days_before_expiry || 90}d to {rule.return_window_end_days_before_expiry || 15}d before exp
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">Credit SLA:</span>
                    <span className="font-semibold text-indigo-400">
                      {rule.credit_note_sla_days || 14} Days
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-400">Min. Batch Value:</span>
                    <span className="font-semibold text-emerald-400">
                      {formatCurrency(rule.min_return_value || 0)}
                    </span>
                  </div>
                  <div className="text-xs pt-1 border-t border-slate-800">
                    <span className="text-slate-400 block text-[10px] mb-1">Excluded Categories:</span>
                    {rule.excluded_categories && rule.excluded_categories.length > 0 ? (
                      <div className="flex flex-wrap gap-1">
                        {rule.excluded_categories.map((c: string) => (
                          <span
                            key={c}
                            className="text-[9px] px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-300 border border-rose-500/20 font-medium"
                          >
                            {c}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-[10px] text-slate-500 italic">None (All Categories Eligible)</span>
                    )}
                  </div>
                </div>

                {/* Scorecard KPIs */}
                <div className="grid grid-cols-2 gap-2 text-center text-xs mb-3">
                  <div className="p-2 rounded-xl bg-[#0D1322] border border-slate-800/60">
                    <div className="text-[10px] text-slate-400">Active Returns</div>
                    <div className="text-sm font-bold text-white mt-0.5">{d.active_returns_count}</div>
                  </div>
                  <div className="p-2 rounded-xl bg-[#0D1322] border border-slate-800/60">
                    <div className="text-[10px] text-slate-400">Total Settled</div>
                    <div className="text-sm font-bold text-emerald-400 mt-0.5">
                      {formatCurrency(d.total_returned_value)}
                    </div>
                  </div>
                </div>
              </div>

              {/* Action */}
              <button
                onClick={() => handleOpenEditRules(d)}
                className="w-full mt-2 py-2 px-3 rounded-xl text-xs font-semibold bg-[#111726] hover:bg-[#161F33] text-slate-200 border border-slate-700/80 flex items-center justify-center space-x-1.5 transition-all"
              >
                <Sliders className="w-3.5 h-3.5 text-emerald-400" />
                <span>Configure Return Rules</span>
              </button>
            </div>
          );
        })}
      </div>

      {/* Edit Rules Modal */}
      {selectedDist && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="glass-card rounded-2xl w-full max-w-lg p-6 border border-slate-700 shadow-2xl relative">
            <button
              onClick={() => setSelectedDist(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <h2 className="text-base font-bold text-white mb-1 flex items-center space-x-2">
              <Sliders className="w-4 h-4 text-emerald-400" />
              <span>Configure Rules: {selectedDist.name}</span>
            </h2>
            <p className="text-xs text-slate-400 mb-4">
              Changes create an immutable new rule version without restarting the system.
            </p>

            <form onSubmit={handleSaveRuleVersion} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Window Opens (Days before expiry)
                  </label>
                  <input
                    type="number"
                    min={15}
                    max={365}
                    required
                    value={winStart}
                    onChange={(e) => setWinStart(Number(e.target.value))}
                    className="w-full bg-[#0D1322] border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
                  />
                  <span className="text-[10px] text-slate-500 mt-0.5 block">Standard: 90 days</span>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Window Closes (Days before expiry)
                  </label>
                  <input
                    type="number"
                    min={0}
                    max={90}
                    required
                    value={winEnd}
                    onChange={(e) => setWinEnd(Number(e.target.value))}
                    className="w-full bg-[#0D1322] border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
                  />
                  <span className="text-[10px] text-slate-500 mt-0.5 block">Standard: 15 days</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Credit Note SLA (Days)
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={60}
                    required
                    value={slaDays}
                    onChange={(e) => setSlaDays(Number(e.target.value))}
                    className="w-full bg-[#0D1322] border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Min Return Batch Value (₹)
                  </label>
                  <input
                    type="number"
                    min={0}
                    step="50"
                    required
                    value={minVal}
                    onChange={(e) => setMinVal(Number(e.target.value))}
                    className="w-full bg-[#0D1322] border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-2">
                  Category Exclusions
                </label>
                <div className="grid grid-cols-2 gap-2">
                  {["Cold Chain", "Schedule X", "Narcotics", "Breakage", "Ointments"].map((cat) => {
                    const isChecked = exclusions.includes(cat);
                    return (
                      <button
                        key={cat}
                        type="button"
                        onClick={() => toggleCategoryExclusion(cat)}
                        className={`px-3 py-2 rounded-xl text-xs font-medium border text-left transition-all flex items-center justify-between ${
                          isChecked
                            ? "bg-rose-500/15 border-rose-500/40 text-rose-300"
                            : "bg-[#0D1322] border-slate-800 text-slate-400 hover:border-slate-700"
                        }`}
                      >
                        <span>{cat}</span>
                        {isChecked && <span className="text-[10px] font-bold">EXCLUDED</span>}
                      </button>
                    );
                  })}
                </div>
              </div>

              <div className="pt-3 flex items-center justify-end space-x-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setSelectedDist(null)}
                  className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingRules}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold shadow-md shadow-emerald-500/20 disabled:opacity-50"
                >
                  {savingRules ? "Saving Version..." : "Save New Version"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
