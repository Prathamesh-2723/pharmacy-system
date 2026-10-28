"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Hourglass,
  RotateCcw,
  Building2,
  ReceiptText,
  UploadCloud,
  ShieldAlert,
  LogOut,
  Sparkles,
} from "lucide-react";
import { api } from "@/lib/api";

const NAV_ITEMS = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
    badge: null,
  },
  {
    name: "Expiry Risk Stock",
    href: "/batches",
    icon: Hourglass,
    badge: "Risk",
    badgeColor: "bg-amber-500/10 text-amber-400 border-amber-500/20",
  },
  {
    name: "Return Workflow",
    href: "/returns",
    icon: RotateCcw,
    badge: "Kanban",
    badgeColor: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  },
  {
    name: "Distributor Rules",
    href: "/distributors",
    icon: Building2,
    badge: "Rules",
    badgeColor: "bg-indigo-500/10 text-indigo-400 border-indigo-500/20",
  },
  {
    name: "Credit Reconciliation",
    href: "/credits",
    icon: ReceiptText,
    badge: "Credits",
    badgeColor: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
  },
  {
    name: "Data Ingestion",
    href: "/import",
    icon: UploadCloud,
    badge: "CSV",
    badgeColor: "bg-slate-700/40 text-slate-400 border-slate-600/30",
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  const handleLogout = () => {
    api.clearToken();
    window.location.href = "/login";
  };

  return (
    <aside className="fixed left-0 top-0 bottom-0 w-64 bg-[#090D16] border-r border-[#1E293B] flex flex-col z-30 select-none">
      {/* Brand Header */}
      <div className="h-16 px-6 flex items-center justify-between border-b border-[#1E293B]/80 bg-[#0B101D]">
        <Link href="/dashboard" className="flex items-center space-x-3 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20 group-hover:scale-105 transition-transform">
            <ShieldAlert className="w-5 h-5 text-slate-950 stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center space-x-1.5">
              <span className="font-bold text-lg tracking-tight text-white">Expiry</span>
              <span className="font-extrabold text-lg text-emerald-400">OS</span>
            </div>
            <p className="text-[10px] uppercase tracking-wider text-slate-400 font-medium">Pharmacy SaaS</p>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-6 space-y-1.5 overflow-y-auto">
        <div className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
          Core Workflows
        </div>
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all ${
                isActive
                  ? "bg-gradient-to-r from-emerald-500/15 to-teal-500/5 text-emerald-400 border border-emerald-500/30 shadow-sm shadow-emerald-500/10"
                  : "text-slate-400 hover:text-slate-200 hover:bg-[#111827] border border-transparent"
              }`}
            >
              <div className="flex items-center space-x-3">
                <Icon className={`w-4 h-4 ${isActive ? "text-emerald-400 stroke-[2.5]" : "text-slate-400"}`} />
                <span>{item.name}</span>
              </div>
              {item.badge && (
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-semibold border ${item.badgeColor}`}
                >
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Pharmacy Tenant Info & Logout */}
      <div className="p-3 border-t border-[#1E293B] bg-[#0A0F1A]">
        <div className="p-3 rounded-xl bg-[#111726] border border-[#1E293B]">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[10px] uppercase font-bold tracking-wider text-emerald-400 flex items-center space-x-1">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse inline-block" />
              <span>Apollo Pharmacy</span>
            </span>
            <span className="text-[10px] text-slate-400 bg-slate-800/80 px-1.5 py-0.5 rounded">RLS Active</span>
          </div>
          <div className="text-xs font-semibold text-slate-200 truncate">Mumbai Central Hub</div>
          <div className="text-[11px] text-slate-400 truncate">GSTIN: 27AAACA1234F1Z9</div>
        </div>

        <button
          onClick={handleLogout}
          className="mt-2 w-full flex items-center justify-center space-x-2 px-3 py-2 text-xs font-medium text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-colors border border-transparent hover:border-rose-500/20"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
}
