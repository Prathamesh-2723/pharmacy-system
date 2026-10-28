"use client";

import React, { useEffect, useState } from "react";
import {
  ReceiptText,
  Plus,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowRight,
  X,
  FileCheck2,
  Coins,
} from "lucide-react";
import { api } from "@/lib/api";
import { CreditNote, DistributorScorecard, ReturnRequest } from "@/types";

export default function CreditsPage() {
  const [creditNotes, setCreditNotes] = useState<CreditNote[]>([]);
  const [distributors, setDistributors] = useState<DistributorScorecard[]>([]);
  const [pendingReturns, setPendingReturns] = useState<ReturnRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [toastMsg, setToastMsg] = useState<string | null>(null);

  // Modal State
  const [showModal, setShowModal] = useState(false);
  const [distId, setDistId] = useState("");
  const [returnReqId, setReturnReqId] = useState("");
  const [creditNoteNo, setCreditNoteNo] = useState("");
  const [creditDate, setCreditDate] = useState(new Date().toISOString().split("T")[0]);
  const [creditedAmount, setCreditedAmount] = useState<number>(0);
  const [remarks, setRemarks] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const loadCredits = async () => {
    try {
      setLoading(true);
      const [cnData, distData, retData] = await Promise.all([
        api.getCreditNotes(),
        api.getDistributors(),
        api.getReturns(),
      ]);
      setCreditNotes(cnData);
      setDistributors(distData);
      setPendingReturns(retData.filter((r) => ["SENT", "ACKNOWLEDGED", "PICKED_UP", "CREDIT_ISSUED"].includes(r.status)));
      if (!distId && distData.length > 0) {
        setDistId(distData[0].id);
      }
    } catch (err: any) {
      setToastMsg("Failed to load credit notes");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadCredits();
  }, []);

  const handleReturnSelect = (rid: string) => {
    setReturnReqId(rid);
    const found = pendingReturns.find((r) => r.id === rid);
    if (found) {
      setDistId(found.distributor_id);
      setCreditedAmount(found.total_estimated_value);
    }
  };

  const handleReconcile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await api.reconcileCreditNote({
        distributor_id: distId,
        return_request_id: returnReqId || null,
        credit_note_no: creditNoteNo,
        credit_note_date: creditDate,
        credited_amount: Number(creditedAmount),
        remarks: remarks || undefined,
      });
      setToastMsg("Credit note recorded and matched successfully!");
      setTimeout(() => setToastMsg(null), 4000);
      setShowModal(false);
      setCreditNoteNo("");
      setRemarks("");
      loadCredits();
    } catch (err: any) {
      setToastMsg(err.message || "Failed to reconcile credit note");
      setTimeout(() => setToastMsg(null), 4000);
    } finally {
      setSubmitting(false);
    }
  };

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: 0,
    }).format(val);
  };

  const totalCredited = creditNotes.reduce((acc, c) => acc + c.credited_amount, 0);
  const totalShortfall = creditNotes.reduce((acc, c) => acc + c.shortfall_amount, 0);

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12">
      {/* Toast Alert */}
      {toastMsg && (
        <div className="fixed top-20 right-8 bg-[#161F33] border border-emerald-500/40 text-emerald-300 px-4 py-2.5 rounded-xl shadow-xl z-50 flex items-center space-x-2 text-sm animate-bounce">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Credit Note Reconciliation & Shortfall Tracking
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Match distributor credit notes against return request estimates to prevent unclaimed write-offs.
          </p>
        </div>

        <button
          onClick={() => setShowModal(true)}
          className="flex items-center space-x-2 px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold shadow-md shadow-emerald-500/20 transition-all hover:scale-[1.02]"
        >
          <Plus className="w-4 h-4 stroke-[2.5]" />
          <span>Record Credit Note</span>
        </button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="glass-card rounded-2xl p-5 border border-slate-800">
          <div className="text-slate-400 text-xs mb-1">Total Credit Received</div>
          <div className="text-3xl font-extrabold text-emerald-400">
            {formatCurrency(totalCredited)}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Settled into pharmacy accounts</div>
        </div>

        <div className="glass-card rounded-2xl p-5 border border-slate-800">
          <div className="text-slate-400 text-xs mb-1">Total Discrepancies & Shortfalls</div>
          <div className="text-3xl font-extrabold text-amber-400">
            {formatCurrency(totalShortfall)}
          </div>
          <div className="text-[11px] text-slate-400 mt-1">Distributor deductions flagged for recovery</div>
        </div>

        <div className="glass-card rounded-2xl p-5 border border-slate-800">
          <div className="text-slate-400 text-xs mb-1">Total Notes Logged</div>
          <div className="text-3xl font-extrabold text-white">{creditNotes.length}</div>
          <div className="text-[11px] text-slate-400 mt-1">Audit verified records</div>
        </div>
      </div>

      {/* Credit Notes Table */}
      <div className="glass-card rounded-2xl border border-slate-800 overflow-hidden">
        <div className="p-4 border-b border-slate-800 bg-[#0B101D] flex items-center justify-between">
          <h2 className="text-sm font-bold text-white">Reconciled Credit Notes</h2>
          <span className="text-xs text-slate-400">{creditNotes.length} Entries</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 uppercase tracking-wider text-[10px]">
                <th className="py-3 px-4 font-semibold">Credit Note No</th>
                <th className="py-3 px-4 font-semibold">Distributor</th>
                <th className="py-3 px-4 font-semibold">Matched Return Ref</th>
                <th className="py-3 px-4 font-semibold">Date</th>
                <th className="py-3 px-4 font-semibold text-right">Expected (₹)</th>
                <th className="py-3 px-4 font-semibold text-right">Credited (₹)</th>
                <th className="py-3 px-4 font-semibold text-right">Shortfall (₹)</th>
                <th className="py-3 px-4 font-semibold text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-200">
              {creditNotes.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-500">
                    No credit notes recorded yet.
                  </td>
                </tr>
              ) : (
                creditNotes.map((c) => (
                  <tr key={c.id} className="hover:bg-slate-800/20">
                    <td className="py-3 px-4 font-mono font-bold text-white">
                      {c.credit_note_no}
                    </td>
                    <td className="py-3 px-4 font-medium text-slate-300">{c.distributor_name}</td>
                    <td className="py-3 px-4 font-mono text-emerald-400">
                      {c.return_request_no || "Unassigned"}
                    </td>
                    <td className="py-3 px-4 text-slate-400">{c.credit_note_date}</td>
                    <td className="py-3 px-4 text-right font-medium">
                      {formatCurrency(c.expected_amount)}
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-emerald-400">
                      {formatCurrency(c.credited_amount)}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {c.shortfall_amount > 0 ? (
                        <span className="font-bold text-amber-400">
                          {formatCurrency(c.shortfall_amount)}
                        </span>
                      ) : (
                        <span className="text-slate-500">₹0.00</span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                          c.status === "MATCHED"
                            ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                            : c.status === "PARTIAL"
                            ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                            : "bg-rose-500/10 text-rose-400 border-rose-500/30"
                        }`}
                      >
                        {c.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal: Record Credit Note */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="glass-card rounded-2xl w-full max-w-lg p-6 border border-slate-700 shadow-2xl relative">
            <button
              onClick={() => setShowModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <h2 className="text-lg font-bold text-white mb-1 flex items-center space-x-2">
              <Coins className="w-5 h-5 text-emerald-400" />
              <span>Record & Match Credit Note</span>
            </h2>
            <p className="text-xs text-slate-400 mb-4">
              Enter distributor credit note details to calculate expected amount vs actual credited amount.
            </p>

            <form onSubmit={handleReconcile} className="space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Match with Return Request (Optional)
                </label>
                <select
                  value={returnReqId}
                  onChange={(e) => handleReturnSelect(e.target.value)}
                  className="w-full bg-[#0D1322] border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="">Select Return Request (Auto-fills value)</option>
                  {pendingReturns.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.return_request_no} — {r.distributor_name} ({formatCurrency(r.total_estimated_value)})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Distributor
                  </label>
                  <select
                    value={distId}
                    onChange={(e) => setDistId(e.target.value)}
                    required
                    className="w-full bg-[#0D1322] border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  >
                    {distributors.map((d) => (
                      <option key={d.id} value={d.id}>
                        {d.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Credit Note Number
                  </label>
                  <input
                    type="text"
                    required
                    value={creditNoteNo}
                    onChange={(e) => setCreditNoteNo(e.target.value)}
                    placeholder="CN-2026-009"
                    className="w-full bg-[#0D1322] border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Credit Note Date
                  </label>
                  <input
                    type="date"
                    required
                    value={creditDate}
                    onChange={(e) => setCreditDate(e.target.value)}
                    className="w-full bg-[#0D1322] border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Credited Amount (₹)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min={0.01}
                    required
                    value={creditedAmount}
                    onChange={(e) => setCreditedAmount(Number(e.target.value))}
                    className="w-full bg-[#0D1322] border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Remarks / Discrepancy Reason
                </label>
                <textarea
                  value={remarks}
                  onChange={(e) => setRemarks(e.target.value)}
                  placeholder="e.g. 15% handling fee deducted by distributor warehouse"
                  rows={2}
                  className="w-full bg-[#0D1322] border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="pt-3 flex items-center justify-end space-x-2 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold shadow-md shadow-emerald-500/20 disabled:opacity-50"
                >
                  {submitting ? "Reconciling..." : "Save & Reconcile"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
