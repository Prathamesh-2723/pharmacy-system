"use client";

import React, { useEffect, useState } from "react";
import {
  Search,
  Plus,
  Filter,
  AlertTriangle,
  Clock,
  ShieldCheck,
  ChevronDown,
  X,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import { BatchItem, DistributorScorecard } from "@/types";

export default function BatchesPage() {
  const [batches, setBatches] = useState<BatchItem[]>([]);
  const [distributors, setDistributors] = useState<DistributorScorecard[]>([]);
  const [search, setSearch] = useState("");
  const [selectedDistributor, setSelectedDistributor] = useState<string>("");
  const [activeTab, setActiveTab] = useState<string>("ALL");
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);

  // New batch form state
  const [formName, setFormName] = useState("");
  const [formCategory, setFormCategory] = useState("General");
  const [formDistId, setFormDistId] = useState("");
  const [formBatchNo, setFormBatchNo] = useState("");
  const [formExpiry, setFormExpiry] = useState("");
  const [formQty, setFormQty] = useState(100);
  const [formPrice, setFormPrice] = useState(25.0);
  const [formInvoice, setFormInvoice] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [formSubmitting, setFormSubmitting] = useState(false);

  const loadBatches = async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (search) params.search = search;
      if (selectedDistributor) params.distributor_id = selectedDistributor;
      if (activeTab === "15D") params.urgency_bucket = "15D";
      if (activeTab === "30D") params.urgency_bucket = "30D";
      if (activeTab === "60D") params.urgency_bucket = "60D";
      if (activeTab === "90D") params.urgency_bucket = "90D";
      if (activeTab === "CLOSING_SOON") params.closing_soon_only = true;

      const [batchRes, distRes] = await Promise.all([
        api.getBatches(params),
        api.getDistributors(),
      ]);
      setBatches(batchRes);
      setDistributors(distRes);
      if (!formDistId && distRes.length > 0) {
        setFormDistId(distRes[0].id);
      }
    } catch (err) {
      console.error("Failed to load batches:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBatches();
  }, [search, selectedDistributor, activeTab]);

  const handleCreateBatch = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormSubmitting(true);
    setFormError(null);

    try {
      await api.createManualBatch({
        product_name: formName,
        category: formCategory,
        distributor_id: formDistId,
        batch_no: formBatchNo,
        expiry_date: formExpiry,
        qty: Number(formQty),
        purchase_price: Number(formPrice),
        invoice_ref: formInvoice,
      });
      setShowAddModal(false);
      // Reset form
      setFormName("");
      setFormBatchNo("");
      setFormExpiry("");
      loadBatches();
    } catch (err: any) {
      setFormError(err.message || "Failed to create batch");
    } finally {
      setFormSubmitting(false);
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
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Batch-Level Expiry & Return Eligibility
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Automated monitoring of SKU return windows per distributor agreements.
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center space-x-2 px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold shadow-md shadow-emerald-500/20 transition-all hover:scale-[1.02]"
        >
          <Plus className="w-4 h-4 stroke-[2.5]" />
          <span>Add Batch Entry</span>
        </button>
      </div>

      {/* Filter Tabs & Search Bar */}
      <div className="glass-card rounded-2xl p-4 border border-slate-800 space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          {/* Tabs */}
          <div className="flex items-center space-x-1.5 p-1 bg-[#090D16] rounded-xl border border-slate-800">
            {[
              { id: "ALL", label: "All Stock" },
              { id: "CLOSING_SOON", label: "Window Closing (≤7d)", badge: "Critical" },
              { id: "15D", label: "≤ 15 Days" },
              { id: "30D", label: "30 Days" },
              { id: "60D", label: "60 Days" },
              { id: "90D", label: "90 Days" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center space-x-1.5 ${
                  activeTab === tab.id
                    ? "bg-emerald-500 text-slate-950 font-bold shadow-sm"
                    : "text-slate-400 hover:text-slate-200"
                }`}
              >
                <span>{tab.label}</span>
                {tab.badge && (
                  <span className="text-[9px] px-1.5 py-0.2 rounded-full bg-rose-500/20 text-rose-300 font-bold">
                    {tab.badge}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Search & Distributor Select */}
          <div className="flex items-center space-x-3 flex-1 justify-end max-w-md">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Filter by medicine or batch..."
                className="w-full bg-[#0D1322] border border-slate-700/80 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              />
            </div>

            <select
              value={selectedDistributor}
              onChange={(e) => setSelectedDistributor(e.target.value)}
              className="bg-[#0D1322] border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs text-slate-300 focus:outline-none focus:border-emerald-500"
            >
              <option value="">All Distributors</option>
              {distributors.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Batches Table */}
      <div className="glass-card rounded-2xl border border-slate-800 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-slate-800 bg-[#0B101D] text-slate-400 uppercase tracking-wider text-[10px]">
                <th className="py-3 px-4 font-semibold">Product SKU</th>
                <th className="py-3 px-4 font-semibold">Batch No</th>
                <th className="py-3 px-4 font-semibold">Distributor</th>
                <th className="py-3 px-4 font-semibold">Expiry Date</th>
                <th className="py-3 px-4 font-semibold">Return Eligibility Status</th>
                <th className="py-3 px-4 font-semibold text-right">Qty</th>
                <th className="py-3 px-4 font-semibold text-right">Value at Risk</th>
                <th className="py-3 px-4 font-semibold text-right">Risk Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 text-slate-200">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-500">
                    <div className="flex items-center justify-center space-x-2">
                      <div className="w-4 h-4 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />
                      <span>Scanning batches against distributor return policies...</span>
                    </div>
                  </td>
                </tr>
              ) : batches.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-500">
                    No batches found matching selected criteria.
                  </td>
                </tr>
              ) : (
                batches.map((b) => (
                  <tr key={b.id} className="hover:bg-slate-800/20 transition-colors">
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-100">{b.product_name}</div>
                      <div className="text-[10px] text-slate-400">{b.category}</div>
                    </td>
                    <td className="py-3 px-4 font-mono font-medium text-slate-300">
                      {b.batch_no}
                    </td>
                    <td className="py-3 px-4 text-slate-300 font-medium">{b.distributor_name}</td>
                    <td className="py-3 px-4">
                      <div className="font-medium text-slate-200">{b.expiry_date}</div>
                      <div className="text-[10px] text-slate-400">
                        {b.days_to_expiry > 0 ? `${b.days_to_expiry} days to exp` : "Expired"}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      {b.eligible ? (
                        <div>
                          <div className="flex items-center space-x-1 text-emerald-400 font-semibold">
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Return Window Open</span>
                          </div>
                          <div className="text-[10px] text-slate-400">
                            Closes: <span className="text-slate-200 font-medium">{b.window_closes_on}</span> (
                            <span className={b.days_to_window_close <= 7 ? "text-rose-400 font-bold" : "text-slate-300"}>
                              {b.days_to_window_close}d left
                            </span>
                            )
                          </div>
                          {b.window_closing_soon && (
                            <span className="inline-block mt-0.5 text-[9px] px-1.5 py-0.2 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 font-bold animate-pulse">
                              Window Closing Soon!
                            </span>
                          )}
                        </div>
                      ) : (
                        <div>
                          <div className="flex items-center space-x-1 text-slate-400 font-semibold">
                            <AlertCircle className="w-3.5 h-3.5 text-slate-500" />
                            <span>Ineligible</span>
                          </div>
                          <div className="text-[10px] text-slate-400 max-w-[200px] truncate" title={b.blocked_reason || ""}>
                            {b.blocked_reason}
                          </div>
                        </div>
                      )}
                    </td>
                    <td className="py-3 px-4 text-right font-medium">{b.current_qty}</td>
                    <td className="py-3 px-4 text-right font-semibold text-emerald-400">
                      {formatCurrency(b.value_at_risk)}
                    </td>
                    <td className="py-3 px-4 text-right">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                          b.priority_score > 5000
                            ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                            : b.priority_score > 1000
                            ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                            : "bg-slate-800 text-slate-400 border-slate-700"
                        }`}
                      >
                        {b.priority_score.toFixed(0)}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Manual Add Batch Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="glass-card rounded-2xl w-full max-w-lg p-6 border border-slate-700 shadow-2xl relative">
            <button
              onClick={() => setShowAddModal(false)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <h2 className="text-lg font-bold text-white mb-1">Add Batch Stock Entry</h2>
            <p className="text-xs text-slate-400 mb-4">
              Enter individual purchase batch details for rules evaluation.
            </p>

            {formError && (
              <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-medium">
                {formError}
              </div>
            )}

            <form onSubmit={handleCreateBatch} className="space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Medicine / Product Name
                </label>
                <input
                  type="text"
                  required
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  placeholder="e.g. Augmentin 625 Duo"
                  className="w-full bg-[#0D1322] border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Category
                  </label>
                  <select
                    value={formCategory}
                    onChange={(e) => setFormCategory(e.target.value)}
                    className="w-full bg-[#0D1322] border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  >
                    <option value="General">General</option>
                    <option value="Antibiotics">Antibiotics</option>
                    <option value="Analgesic">Analgesic</option>
                    <option value="Cardiovascular">Cardiovascular</option>
                    <option value="Antidiabetic">Antidiabetic</option>
                    <option value="Cold Chain">Cold Chain</option>
                    <option value="Schedule X">Schedule X</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Distributor
                  </label>
                  <select
                    value={formDistId}
                    onChange={(e) => setFormDistId(e.target.value)}
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
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Batch Number
                  </label>
                  <input
                    type="text"
                    required
                    value={formBatchNo}
                    onChange={(e) => setFormBatchNo(e.target.value)}
                    placeholder="e.g. AUG-2026-X1"
                    className="w-full bg-[#0D1322] border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Expiry Date
                  </label>
                  <input
                    type="date"
                    required
                    value={formExpiry}
                    onChange={(e) => setFormExpiry(e.target.value)}
                    className="w-full bg-[#0D1322] border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Quantity
                  </label>
                  <input
                    type="number"
                    required
                    min={1}
                    value={formQty}
                    onChange={(e) => setFormQty(Number(e.target.value))}
                    className="w-full bg-[#0D1322] border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Purchase Price (₹)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    min={0.01}
                    value={formPrice}
                    onChange={(e) => setFormPrice(Number(e.target.value))}
                    className="w-full bg-[#0D1322] border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Invoice No (Ref)
                  </label>
                  <input
                    type="text"
                    value={formInvoice}
                    onChange={(e) => setFormInvoice(e.target.value)}
                    placeholder="INV-9901"
                    className="w-full bg-[#0D1322] border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div className="pt-3 flex items-center justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={formSubmitting}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold shadow-md shadow-emerald-500/20 disabled:opacity-50"
                >
                  {formSubmitting ? "Saving..." : "Save Batch"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
