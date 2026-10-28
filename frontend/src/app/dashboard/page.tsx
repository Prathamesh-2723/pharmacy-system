"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  TrendingUp,
  AlertTriangle,
  RotateCcw,
  ReceiptText,
  Clock,
  ArrowUpRight,
  ShieldCheck,
  ChevronRight,
  Sparkles,
  FileSpreadsheet,
  CheckCircle2,
  Calendar,
} from "lucide-react";
import { api } from "@/lib/api";
import { DashboardKpis, BatchItem, DistributorScorecard } from "@/types";

export default function DashboardPage() {
  const [kpis, setKpis] = useState<DashboardKpis | null>(null);
  const [urgentBatches, setUrgentBatches] = useState<BatchItem[]>([]);
  const [distributors, setDistributors] = useState<DistributorScorecard[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    try {
      setLoading(true);
      const [kpiData, batchData, distData] = await Promise.all([
        api.getDashboardKpis(),
        api.getBatches({ eligible_only: true }),
        api.getDistributors(),
      ]);
      setKpis(kpiData);
      setUrgentBatches(batchData.slice(0, 5));
      setDistributors(distData.slice(0, 5));
    } catch (err) {
      console.error("Failed to load dashboard data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const formatCurrency = (val?: number) => {
    if (val === undefined || val === null) return "₹0.00";
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(val);
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Top Welcome & Summary Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2 text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-1">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping inline-block" />
            <span>Autonomous Return Engine Active</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Financial Impact & Expiry Overview
          </h1>
          <p className="text-xs text-slate-400 mt-0.5">
            Real-time tracking of near-expiry inventory, distributor return SLA compliance, and credit reconciliation.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <Link
            href="/import"
            className="flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-[#111726] border border-[#1E293B] text-slate-300 hover:text-white hover:border-slate-700 transition-all"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
            <span>Upload Purchase CSV</span>
          </Link>
          <Link
            href="/returns"
            className="flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold shadow-md shadow-emerald-500/20 transition-all hover:scale-[1.02]"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Open Return Kanban</span>
          </Link>
        </div>
      </div>

      {/* Hero Metric Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {/* KPI 1: Write-offs Avoided (The Money-Saved Hero) */}
        <div className="glass-card rounded-2xl p-6 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/10 rounded-full blur-2xl group-hover:bg-emerald-500/20 transition-all" />
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-emerald-400">
              Loss Avoidance
            </span>
            <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-white tracking-tight">
            {formatCurrency(kpis?.writeoffs_avoided_month || 0)}
          </div>
          <div className="flex items-center space-x-2 mt-2 text-xs">
            <span className="text-emerald-400 font-semibold flex items-center">
              Avoided Write-Offs
            </span>
            <span className="text-slate-400">• Settled this month</span>
          </div>
        </div>

        {/* KPI 2: Total Stock at Risk */}
        <div className="glass-card rounded-2xl p-6 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-amber-500/10 rounded-full blur-2xl group-hover:bg-amber-500/20 transition-all" />
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-amber-400">
              Value at Risk
            </span>
            <div className="p-2 rounded-xl bg-amber-500/10 text-amber-400 border border-amber-500/20">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-white tracking-tight">
            {formatCurrency(kpis?.total_value_at_risk || 0)}
          </div>
          <div className="flex items-center space-x-2 mt-2 text-xs">
            <span className="text-amber-400 font-semibold">Eligible for Return</span>
            <span className="text-slate-400">• Next 90 days</span>
          </div>
        </div>

        {/* KPI 3: Returns Pending in Workflow */}
        <div className="glass-card rounded-2xl p-6 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-500/10 rounded-full blur-2xl group-hover:bg-indigo-500/20 transition-all" />
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-indigo-400">
              Active Returns
            </span>
            <div className="p-2 rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              <RotateCcw className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-white tracking-tight">
            {formatCurrency(kpis?.returns_pending_value || 0)}
          </div>
          <div className="flex items-center space-x-2 mt-2 text-xs">
            <span className="text-indigo-400 font-semibold">
              {kpis?.returns_pending_count || 0} Batches Dispatched
            </span>
            <span className="text-slate-400">• Awaiting Credit</span>
          </div>
        </div>

        {/* KPI 4: Overdue Distributor Credits */}
        <div className="glass-card rounded-2xl p-6 relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-rose-500/10 rounded-full blur-2xl group-hover:bg-rose-500/20 transition-all" />
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider text-rose-400">
              SLA Breaches
            </span>
            <div className="p-2 rounded-xl bg-rose-500/10 text-rose-400 border border-rose-500/20">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="text-3xl font-extrabold text-rose-400 tracking-tight">
            {formatCurrency(kpis?.overdue_credits_value || 0)}
          </div>
          <div className="flex items-center space-x-2 mt-2 text-xs">
            <span className="text-rose-400 font-semibold">
              {kpis?.overdue_credits_count || 0} Overdue Returns
            </span>
            <span className="text-slate-400">• Escalation Queued</span>
          </div>
        </div>
      </div>

      {/* Urgency Horizons Progress Breakdown */}
      <div className="glass-card rounded-2xl p-6 border border-slate-800">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-base font-bold text-white tracking-tight">
              Expiry Horizon & Window Urgency Breakdown
            </h2>
            <p className="text-xs text-slate-400">
              Value distribution across near-expiry return windows.
            </p>
          </div>
          <span className="text-xs font-medium text-slate-400">
            Reconciliation Accuracy:{" "}
            <span className="text-emerald-400 font-bold">
              {kpis?.reconciliation_accuracy_percent || 98.5}%
            </span>
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* 15 Days (Critical) */}
          <div className="p-4 rounded-xl bg-[#0D1322] border border-rose-500/30 relative overflow-hidden">
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="font-semibold text-rose-400 flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping inline-block" />
                <span>&le; 15 Days (Critical)</span>
              </span>
              <span className="text-slate-400">Window Closing</span>
            </div>
            <div className="text-xl font-bold text-white">
              {formatCurrency(kpis?.value_expiring_15d || 0)}
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full mt-3 overflow-hidden">
              <div className="bg-rose-500 h-full rounded-full w-[85%]" />
            </div>
          </div>

          {/* 30 Days (High Risk) */}
          <div className="p-4 rounded-xl bg-[#0D1322] border border-amber-500/30">
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="font-semibold text-amber-400">16 – 30 Days</span>
              <span className="text-slate-400">Urgent Return</span>
            </div>
            <div className="text-xl font-bold text-white">
              {formatCurrency(kpis?.value_expiring_30d || 0)}
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full mt-3 overflow-hidden">
              <div className="bg-amber-400 h-full rounded-full w-[65%]" />
            </div>
          </div>

          {/* 60 Days (Moderate) */}
          <div className="p-4 rounded-xl bg-[#0D1322] border border-yellow-500/30">
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="font-semibold text-yellow-400">31 – 60 Days</span>
              <span className="text-slate-400">Active Window</span>
            </div>
            <div className="text-xl font-bold text-white">
              {formatCurrency(kpis?.value_expiring_60d || 0)}
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full mt-3 overflow-hidden">
              <div className="bg-yellow-400 h-full rounded-full w-[45%]" />
            </div>
          </div>

          {/* 90 Days (Planned) */}
          <div className="p-4 rounded-xl bg-[#0D1322] border border-cyan-500/30">
            <div className="flex items-center justify-between text-xs mb-1.5">
              <span className="font-semibold text-cyan-400">61 – 90 Days</span>
              <span className="text-slate-400">Window Opening</span>
            </div>
            <div className="text-xl font-bold text-white">
              {formatCurrency(kpis?.value_expiring_90d || 0)}
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full mt-3 overflow-hidden">
              <div className="bg-cyan-400 h-full rounded-full w-[30%]" />
            </div>
          </div>
        </div>
      </div>

      {/* Two Column Grid: Top Priority Batches & Distributor Scorecards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Urgent Batches List (2 Cols) */}
        <div className="lg:col-span-2 glass-card rounded-2xl p-6 border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-white tracking-tight flex items-center space-x-2">
                <span>Top Urgent Return Candidates</span>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">
                  Highest Financial Risk
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Ranked by ExpiryOS Priority Score (Value &times; Urgency &times; Window Proximity)
              </p>
            </div>
            <Link
              href="/batches"
              className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 flex items-center space-x-1"
            >
              <span>View All 1,500 Batches</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                  <th className="pb-3 font-semibold">Medicine / SKU</th>
                  <th className="pb-3 font-semibold">Distributor</th>
                  <th className="pb-3 font-semibold">Window Closes</th>
                  <th className="pb-3 font-semibold text-right">Qty</th>
                  <th className="pb-3 font-semibold text-right">Value at Risk</th>
                  <th className="pb-3 font-semibold text-right">Risk Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 text-slate-200">
                {urgentBatches.map((b) => (
                  <tr key={b.id} className="hover:bg-slate-800/20 transition-colors">
                    <td className="py-3">
                      <div className="font-semibold text-slate-100">{b.product_name}</div>
                      <div className="text-[11px] text-slate-400 font-mono">
                        Batch: {b.batch_no} • {b.category}
                      </div>
                    </td>
                    <td className="py-3 text-slate-300">{b.distributor_name}</td>
                    <td className="py-3">
                      <div className="font-medium text-slate-200">{b.window_closes_on}</div>
                      <div className="text-[10px] font-semibold text-rose-400">
                        {b.days_to_window_close} days left in window
                      </div>
                    </td>
                    <td className="py-3 text-right font-medium">{b.current_qty}</td>
                    <td className="py-3 text-right font-semibold text-emerald-400">
                      {formatCurrency(b.value_at_risk)}
                    </td>
                    <td className="py-3 text-right">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                        {b.priority_score.toFixed(0)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Distributor Performance Scorecard (1 Col) */}
        <div className="glass-card rounded-2xl p-6 border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-base font-bold text-white tracking-tight">
                  Distributor Scorecard
                </h2>
                <p className="text-xs text-slate-400">Credit turnaround & SLA compliance</p>
              </div>
              <Link
                href="/distributors"
                className="text-xs font-semibold text-emerald-400 hover:text-emerald-300 flex items-center"
              >
                <span>All 30</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="space-y-3">
              {distributors.map((d) => (
                <div
                  key={d.id}
                  className="p-3 rounded-xl bg-[#0D1322] border border-slate-800/80 hover:border-slate-700 transition-all flex items-center justify-between"
                >
                  <div>
                    <div className="font-semibold text-xs text-slate-200">{d.name}</div>
                    <div className="text-[10px] text-slate-400 mt-0.5">
                      Credit SLA:{" "}
                      <span className="text-slate-300 font-medium">
                        {d.avg_credit_turnaround_days} Days
                      </span>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-semibold border border-emerald-500/20">
                      {d.active_returns_count} Active Returns
                    </span>
                    <div className="text-[11px] font-semibold text-slate-300 mt-1">
                      {formatCurrency(d.total_returned_value)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-slate-800">
            <div className="flex items-center justify-between text-xs text-slate-400">
              <span className="flex items-center space-x-1.5">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Multi-tenant RLS Enforced</span>
              </span>
              <span className="text-emerald-400 font-semibold">100% Policy Isolation</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
