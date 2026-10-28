"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  RotateCcw,
  Sparkles,
  CheckCircle2,
  Clock,
  Printer,
  Share2,
  ChevronRight,
  ExternalLink,
  X,
  FileText,
  AlertCircle,
  Truck,
  Check,
  Send,
} from "lucide-react";
import { api } from "@/lib/api";
import { ReturnRequest } from "@/types";

const STAGES = [
  { id: "DRAFT", label: "Drafts", color: "border-slate-700 bg-slate-900/50 text-slate-300" },
  { id: "APPROVED", label: "Approved", color: "border-emerald-500/40 bg-emerald-950/20 text-emerald-400" },
  { id: "SENT", label: "Sent / Dispatched", color: "border-indigo-500/40 bg-indigo-950/20 text-indigo-400" },
  { id: "ACKNOWLEDGED", label: "Acknowledged", color: "border-cyan-500/40 bg-cyan-950/20 text-cyan-400" },
  { id: "PICKED_UP", label: "Picked Up", color: "border-blue-500/40 bg-blue-950/20 text-blue-400" },
  { id: "CREDIT_ISSUED", label: "Credit Issued", color: "border-amber-500/40 bg-amber-950/20 text-amber-400" },
  { id: "SETTLED", label: "Settled", color: "border-teal-500/40 bg-teal-950/20 text-teal-400" },
];

export default function ReturnsPage() {
  const [returns, setReturns] = useState<ReturnRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [autoDrafting, setAutoDrafting] = useState(false);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  // Print & WhatsApp Slip Modal State
  const [slipModalOpen, setSlipModalOpen] = useState(false);
  const [slipData, setSlipData] = useState<{
    html: string;
    waText: string;
    waUrl: string;
    returnNo: string;
  } | null>(null);

  const loadReturns = async () => {
    try {
      setLoading(true);
      const data = await api.getReturns();
      setReturns(data);
    } catch (err) {
      console.error("Failed to load returns:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReturns();
  }, []);

  const handleAutoGenerate = async () => {
    setAutoDrafting(true);
    try {
      const generated = await api.autoGenerateReturns();
      setToastMsg(`Generated ${generated.length} return draft(s) grouped by distributor.`);
      setTimeout(() => setToastMsg(null), 4000);
      loadReturns();
    } catch (err: any) {
      setToastMsg(err.message || "Failed to auto-generate returns");
      setTimeout(() => setToastMsg(null), 4000);
    } finally {
      setAutoDrafting(false);
    }
  };

  const handleBulkApprove = async () => {
    const draftIds = returns.filter((r) => r.status === "DRAFT").map((r) => r.id);
    if (draftIds.length === 0) {
      setToastMsg("No draft returns to approve.");
      setTimeout(() => setToastMsg(null), 3000);
      return;
    }
    try {
      await api.bulkApproveReturns(draftIds);
      setToastMsg(`Approved ${draftIds.length} draft return(s) with one click!`);
      setTimeout(() => setToastMsg(null), 4000);
      loadReturns();
    } catch (err: any) {
      setToastMsg(err.message || "Bulk approval failed");
    }
  };

  const handleTransition = async (id: string, toStatus: string) => {
    try {
      await api.transitionReturn(id, toStatus, `Transitioned to ${toStatus} via Kanban action`);
      loadReturns();
    } catch (err: any) {
      setToastMsg(err.message || "Transition failed");
      setTimeout(() => setToastMsg(null), 4000);
    }
  };

  const handleOpenSlip = async (id: string, returnNo: string) => {
    try {
      const res = await api.renderReturnSlip(id);
      setSlipData({
        html: res.html_slip,
        waText: res.whatsapp_summary,
        waUrl: res.whatsapp_share_url,
        returnNo,
      });
      setSlipModalOpen(true);
    } catch (err: any) {
      setToastMsg(err.message || "Failed to render dispatch slip");
      setTimeout(() => setToastMsg(null), 3000);
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
      {/* Toast Notification */}
      {toastMsg && (
        <div className="fixed top-20 right-8 bg-[#161F33] border border-emerald-500/40 text-emerald-300 px-4 py-2.5 rounded-xl shadow-xl z-50 flex items-center space-x-2 text-sm animate-bounce">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Page Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Return-to-Distributor Lifecycle Board
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Real-time Kanban tracking distributor return authorizations, dispatch slips, and credit settlements.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={handleAutoGenerate}
            disabled={autoDrafting}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold shadow-md shadow-emerald-500/20 transition-all hover:scale-[1.02] disabled:opacity-50"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>{autoDrafting ? "Scanning Batches..." : "Scan & Auto-Draft"}</span>
          </button>

          <button
            onClick={handleBulkApprove}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-[#111726] border border-emerald-500/40 text-emerald-400 hover:bg-emerald-500/10 transition-all"
          >
            <Check className="w-3.5 h-3.5" />
            <span>Approve All Drafts</span>
          </button>
        </div>
      </div>

      {/* Kanban Board Columns Container */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7 gap-3.5 overflow-x-auto pb-4">
        {STAGES.map((stage) => {
          const itemsInStage = returns.filter((r) => r.status === stage.id);
          const stageTotalValue = itemsInStage.reduce((acc, r) => acc + r.total_estimated_value, 0);

          return (
            <div
              key={stage.id}
              className="bg-[#0D1322] border border-slate-800 rounded-2xl p-3 flex flex-col min-w-[210px] max-w-[260px]"
            >
              {/* Column Header */}
              <div className="flex items-center justify-between pb-3 border-b border-slate-800/80 mb-3">
                <div className="flex items-center space-x-2">
                  <span className={`text-xs font-bold ${stage.color.split(" ")[2]}`}>
                    {stage.label}
                  </span>
                  <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-slate-800 text-slate-400 font-semibold">
                    {itemsInStage.length}
                  </span>
                </div>
                <span className="text-[10px] font-semibold text-slate-400">
                  {formatCurrency(stageTotalValue)}
                </span>
              </div>

              {/* Cards List */}
              <div className="flex-1 space-y-2.5 overflow-y-auto max-h-[650px] pr-1">
                {itemsInStage.length === 0 ? (
                  <div className="py-8 text-center text-[11px] text-slate-600">
                    No returns in {stage.label.toLowerCase()}
                  </div>
                ) : (
                  itemsInStage.map((ret) => (
                    <div
                      key={ret.id}
                      className="glass-card rounded-xl p-3 border border-slate-800/80 hover:border-slate-700 transition-all relative group"
                    >
                      {/* Top Bar: Return No & Actions */}
                      <div className="flex items-center justify-between text-[11px] mb-1">
                        <Link
                          href={`/returns/${ret.id}`}
                          className="font-mono font-bold text-slate-200 hover:text-emerald-400 transition-colors flex items-center space-x-1"
                        >
                          <span>{ret.return_request_no}</span>
                          <ExternalLink className="w-2.5 h-2.5 text-slate-500" />
                        </Link>
                        <button
                          onClick={() => handleOpenSlip(ret.id, ret.return_request_no)}
                          title="View Dispatch Slip & WhatsApp Share"
                          className="p-1 rounded text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10 transition-colors"
                        >
                          <FileText className="w-3.5 h-3.5" />
                        </button>
                      </div>

                      {/* Distributor & Value */}
                      <div className="text-xs font-semibold text-slate-300 truncate">
                        {ret.distributor_name}
                      </div>
                      <div className="flex items-center justify-between mt-2 pt-2 border-t border-slate-800/60 text-xs">
                        <span className="text-slate-400 text-[11px]">
                          {ret.item_count} SKU{ret.item_count > 1 ? "s" : ""}
                        </span>
                        <span className="font-bold text-emerald-400">
                          {formatCurrency(ret.total_estimated_value)}
                        </span>
                      </div>

                      {/* SLA Warning */}
                      {ret.credit_sla_deadline && (
                        <div className="mt-1 text-[10px] text-indigo-400 flex items-center space-x-1">
                          <Clock className="w-3 h-3" />
                          <span>
                            SLA: {new Date(ret.credit_sla_deadline).toLocaleDateString()}
                          </span>
                        </div>
                      )}

                      {/* Transition Action Buttons */}
                      <div className="mt-2.5 pt-2 border-t border-slate-800/80 flex items-center justify-end space-x-1">
                        {ret.status === "DRAFT" && (
                          <button
                            onClick={() => handleTransition(ret.id, "APPROVED")}
                            className="w-full py-1 text-[11px] font-semibold rounded bg-emerald-500/20 text-emerald-300 hover:bg-emerald-500/30 border border-emerald-500/40 text-center transition-all"
                          >
                            Approve
                          </button>
                        )}
                        {ret.status === "APPROVED" && (
                          <button
                            onClick={() => handleTransition(ret.id, "SENT")}
                            className="w-full py-1 text-[11px] font-semibold rounded bg-indigo-500/20 text-indigo-300 hover:bg-indigo-500/30 border border-indigo-500/40 text-center transition-all flex items-center justify-center space-x-1"
                          >
                            <Send className="w-3 h-3" />
                            <span>Dispatch</span>
                          </button>
                        )}
                        {ret.status === "SENT" && (
                          <button
                            onClick={() => handleTransition(ret.id, "ACKNOWLEDGED")}
                            className="w-full py-1 text-[11px] font-semibold rounded bg-cyan-500/20 text-cyan-300 hover:bg-cyan-500/30 border border-cyan-500/40 text-center transition-all"
                          >
                            Mark Ack
                          </button>
                        )}
                        {ret.status === "ACKNOWLEDGED" && (
                          <button
                            onClick={() => handleTransition(ret.id, "PICKED_UP")}
                            className="w-full py-1 text-[11px] font-semibold rounded bg-blue-500/20 text-blue-300 hover:bg-blue-500/30 border border-blue-500/40 text-center transition-all flex items-center justify-center space-x-1"
                          >
                            <Truck className="w-3 h-3" />
                            <span>Picked Up</span>
                          </button>
                        )}
                        {ret.status === "PICKED_UP" && (
                          <Link
                            href="/credits"
                            className="w-full py-1 text-[11px] font-semibold rounded bg-amber-500/20 text-amber-300 hover:bg-amber-500/30 border border-amber-500/40 text-center transition-all block"
                          >
                            Reconcile Credit
                          </Link>
                        )}
                        {ret.status === "CREDIT_ISSUED" && (
                          <button
                            onClick={() => handleTransition(ret.id, "SETTLED")}
                            className="w-full py-1 text-[11px] font-semibold rounded bg-teal-500/20 text-teal-300 hover:bg-teal-500/30 border border-teal-500/40 text-center transition-all"
                          >
                            Final Settle
                          </button>
                        )}
                        {ret.status === "SETTLED" && (
                          <div className="w-full py-0.5 text-[10px] text-teal-400 text-center font-medium">
                            100% Reconciled
                          </div>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Dispatch Slip & WhatsApp Modal */}
      {slipModalOpen && slipData && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="glass-card rounded-2xl w-full max-w-3xl max-h-[90vh] flex flex-col border border-slate-700 shadow-2xl relative overflow-hidden">
            {/* Modal Header */}
            <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-[#0B101D]">
              <div>
                <h2 className="text-base font-bold text-white flex items-center space-x-2">
                  <span>Return Request Dispatch Slip</span>
                  <span className="font-mono text-xs text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                    {slipData.returnNo}
                  </span>
                </h2>
                <p className="text-xs text-slate-400">
                  Ready for physical courier dispatch or direct WhatsApp transmission.
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <a
                  href={slipData.waUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold transition-all"
                >
                  <Share2 className="w-3.5 h-3.5" />
                  <span>Send via WhatsApp</span>
                </a>

                <button
                  onClick={() => {
                    const printWindow = window.open("", "_blank");
                    if (printWindow) {
                      printWindow.document.write(slipData.html);
                      printWindow.document.close();
                      printWindow.print();
                    }
                  }}
                  className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#111726] border border-slate-700 text-slate-200 hover:text-white transition-all"
                >
                  <Printer className="w-3.5 h-3.5" />
                  <span>Print Slip</span>
                </button>

                <button
                  onClick={() => setSlipModalOpen(false)}
                  className="p-1.5 rounded-lg text-slate-400 hover:text-white"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Content: Split HTML Slip Preview & WhatsApp Text */}
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
              {/* WhatsApp message copy preview box */}
              <div className="p-4 rounded-xl bg-[#090D16] border border-slate-800">
                <div className="flex items-center justify-between text-xs font-semibold text-emerald-400 mb-2">
                  <span>Direct WhatsApp Message Body:</span>
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(slipData.waText);
                      setToastMsg("Copied WhatsApp message text to clipboard!");
                      setTimeout(() => setToastMsg(null), 3000);
                    }}
                    className="text-[11px] text-slate-400 hover:text-white underline"
                  >
                    Copy Text
                  </button>
                </div>
                <pre className="text-xs text-slate-300 font-mono whitespace-pre-wrap bg-[#0D1322] p-3 rounded-lg border border-slate-800/80">
                  {slipData.waText}
                </pre>
              </div>

              {/* Printable HTML slip frame preview */}
              <div>
                <h3 className="text-xs font-semibold text-slate-300 mb-2 uppercase tracking-wider">
                  Physical Dispatch Slip Preview:
                </h3>
                <div className="border border-slate-700 rounded-xl overflow-hidden bg-white text-slate-900 p-6 shadow-inner">
                  <div dangerouslySetInnerHTML={{ __html: slipData.html }} />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
