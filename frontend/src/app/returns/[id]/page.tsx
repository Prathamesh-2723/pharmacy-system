"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  Printer,
  Share2,
  Clock,
  ShieldCheck,
  CheckCircle2,
  Calendar,
  Building2,
  History,
  FileSpreadsheet,
} from "lucide-react";
import { api } from "@/lib/api";
import { ReturnRequest } from "@/types";

export default function ReturnDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [returnReq, setReturnReq] = useState<ReturnRequest | null>(null);
  const [loading, setLoading] = useState(true);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  const loadReturn = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const data = await api.getReturnDetail(id);
      setReturnReq(data);
    } catch (err: any) {
      setToastMsg(err.message || "Failed to load return details");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReturn();
  }, [id]);

  const handlePrint = async () => {
    if (!id) return;
    try {
      const res = await api.renderReturnSlip(id);
      const printWindow = window.open("", "_blank");
      if (printWindow) {
        printWindow.document.write(res.html_slip);
        printWindow.document.close();
        printWindow.print();
      }
    } catch (err: any) {
      setToastMsg("Failed to generate printable slip");
    }
  };

  const handleWhatsApp = async () => {
    if (!id) return;
    try {
      const res = await api.renderReturnSlip(id);
      window.open(res.whatsapp_share_url, "_blank");
    } catch (err: any) {
      setToastMsg("Failed to open WhatsApp dispatch");
    }
  };

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(val);
  };

  if (loading) {
    return (
      <div className="py-24 text-center text-slate-500">
        <div className="flex items-center justify-center space-x-2">
          <div className="w-5 h-5 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />
          <span>Loading return request details...</span>
        </div>
      </div>
    );
  }

  if (!returnReq) {
    return (
      <div className="py-24 text-center text-slate-400">
        <p>Return Request not found.</p>
        <Link href="/returns" className="text-emerald-400 font-semibold mt-2 inline-block">
          &larr; Back to Return Board
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      {/* Toast Alert */}
      {toastMsg && (
        <div className="fixed top-20 right-8 bg-[#161F33] border border-emerald-500/40 text-emerald-300 px-4 py-2.5 rounded-xl shadow-xl z-50 flex items-center space-x-2 text-sm animate-bounce">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Top Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => router.back()}
            className="p-2 rounded-xl bg-[#111726] border border-slate-800 text-slate-400 hover:text-white"
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-2xl font-bold text-white tracking-tight font-mono">
                {returnReq.return_request_no}
              </h1>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                {returnReq.status}
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Distributor: <span className="text-slate-200 font-semibold">{returnReq.distributor_name}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleWhatsApp}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold shadow-md shadow-emerald-500/20 transition-all hover:scale-[1.02]"
          >
            <Share2 className="w-3.5 h-3.5" />
            <span>Open in WhatsApp</span>
          </button>
          <button
            onClick={handlePrint}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-[#111726] border border-slate-700 text-slate-200 hover:text-white transition-all"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Print Dispatch Slip</span>
          </button>
        </div>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="glass-card rounded-2xl p-4 border border-slate-800">
          <div className="text-slate-400 text-xs mb-1">Total Estimated Value</div>
          <div className="text-2xl font-bold text-white">
            {formatCurrency(returnReq.total_estimated_value)}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">{returnReq.item_count} Line Items</div>
        </div>

        <div className="glass-card rounded-2xl p-4 border border-slate-800">
          <div className="text-slate-400 text-xs mb-1">Credit Settled</div>
          <div className="text-2xl font-bold text-emerald-400">
            {formatCurrency(returnReq.total_credit_received)}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Reconciliation Status</div>
        </div>

        <div className="glass-card rounded-2xl p-4 border border-slate-800">
          <div className="text-slate-400 text-xs mb-1">Credit SLA Deadline</div>
          <div className="text-base font-bold text-slate-200 flex items-center space-x-1.5">
            <Clock className="w-4 h-4 text-indigo-400" />
            <span>
              {returnReq.credit_sla_deadline
                ? new Date(returnReq.credit_sla_deadline).toLocaleDateString()
                : "Active on Dispatch"}
            </span>
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Distributor Turnaround</div>
        </div>

        <div className="glass-card rounded-2xl p-4 border border-slate-800">
          <div className="text-slate-400 text-xs mb-1">Creation Date</div>
          <div className="text-base font-bold text-slate-200 flex items-center space-x-1.5">
            <Calendar className="w-4 h-4 text-cyan-400" />
            <span>{new Date(returnReq.created_at).toLocaleDateString()}</span>
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Audit Logged</div>
        </div>
      </div>

      {/* Items Table */}
      <div className="glass-card rounded-2xl border border-slate-800 overflow-hidden">
        <div className="p-4 border-b border-slate-800 bg-[#0B101D] flex items-center justify-between">
          <h2 className="text-sm font-bold text-white">Return Request Batches & Items</h2>
          <span className="text-xs text-slate-400">{returnReq.items.length} SKUs Listed</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                <th className="py-3 px-4 font-semibold">Medicine / SKU</th>
                <th className="py-3 px-4 font-semibold">Batch No</th>
                <th className="py-3 px-4 font-semibold">Expiry Date</th>
                <th className="py-3 px-4 font-semibold text-right">Requested Qty</th>
                <th className="py-3 px-4 font-semibold text-right">Unit Rate (₹)</th>
                <th className="py-3 px-4 font-semibold text-right">Total Amount (₹)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-200">
              {returnReq.items.map((it) => (
                <tr key={it.id} className="hover:bg-slate-800/20">
                  <td className="py-3 px-4 font-semibold text-slate-100">
                    {it.product_name}
                    <div className="text-[10px] text-slate-400 font-normal">{it.category}</div>
                  </td>
                  <td className="py-3 px-4 font-mono font-medium text-slate-300">{it.batch_no}</td>
                  <td className="py-3 px-4 text-slate-300">{it.expiry_date}</td>
                  <td className="py-3 px-4 text-right font-medium">{it.requested_qty}</td>
                  <td className="py-3 px-4 text-right">{formatCurrency(it.unit_purchase_price)}</td>
                  <td className="py-3 px-4 text-right font-semibold text-emerald-400">
                    {formatCurrency(it.total_value)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Audit Trail Events */}
      <div className="glass-card rounded-2xl p-6 border border-slate-800">
        <h2 className="text-sm font-bold text-white mb-4 flex items-center space-x-2">
          <History className="w-4 h-4 text-emerald-400" />
          <span>Status Event Audit Trail</span>
        </h2>
        <div className="space-y-4">
          {returnReq.events.map((ev, index) => (
            <div key={ev.id} className="flex items-start space-x-3 text-xs">
              <div className="w-2 h-2 rounded-full bg-emerald-400 mt-1.5 ring-4 ring-emerald-500/20" />
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <span className="font-semibold text-slate-200">
                    Transition to <span className="text-emerald-400">{ev.to_status}</span>
                  </span>
                  <span className="text-slate-500 text-[11px]">
                    via {ev.trigger} • {new Date(ev.created_at).toLocaleString()}
                  </span>
                </div>
                {ev.comment && <p className="text-slate-400 mt-0.5">{ev.comment}</p>}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
