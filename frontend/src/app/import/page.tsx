"use client";

import React, { useState } from "react";
import {
  UploadCloud,
  FileSpreadsheet,
  Download,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Sparkles,
  ArrowRight,
  RefreshCw,
} from "lucide-react";
import { api } from "@/lib/api";

export default function ImportPage() {
  const [activeTab, setActiveTab] = useState<"CSV" | "OCR">("CSV");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [importResult, setImportResult] = useState<any | null>(null);
  const [ocrResult, setOcrResult] = useState<any | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleDownloadSampleCsv = () => {
    const csvContent = `item,batch_no,expiry,distributor,qty,price,invoice_no,category
Augmentin 625 Duo,AUG-2026-B1,2026-12-15,Sun Pharma Logistics,100,185.00,INV-2026-8801,Antibiotics
Dolo 650,DOL-2026-C2,2026-11-20,Micro Labs Hub,200,32.50,INV-2026-8802,Analgesic
Telma 40,TEL-2027-D3,2027-04-30,Glenmark Pharma Supply,150,145.00,INV-2026-8803,Cardiovascular
Pan D Capsule,PAN-2026-E4,2026-12-05,Alkem Logistics Co,120,165.00,INV-2026-8804,Antacid
Lantus Solostar,LAN-2026-F5,2026-11-25,Sanofi India Logistics,50,650.00,INV-2026-8805,Cold Chain
`;
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "expiryos_purchase_sample.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setImportResult(null);
      setOcrResult(null);
      setErrorMsg(null);
    }
  };

  const handleProcessCsv = async () => {
    if (!file) return;
    setUploading(true);
    setErrorMsg(null);

    try {
      const res = await api.uploadCsv(file);
      setImportResult(res);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to process CSV file");
    } finally {
      setUploading(false);
    }
  };

  const handleProcessOcr = async () => {
    if (!file) return;
    setUploading(true);
    setErrorMsg(null);

    try {
      const res = await api.parseInvoiceStub(file);
      setOcrResult(res);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to parse document");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Purchase Data Ingestion & OCR Parser
          </h1>
          <p className="text-xs text-slate-400 mt-1">
            Ingest batch entries with row-level validation, idempotency protection, or preview LayoutLM OCR stub.
          </p>
        </div>

        <button
          onClick={handleDownloadSampleCsv}
          className="flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-[#111726] border border-slate-700 text-slate-200 hover:text-white transition-all"
        >
          <Download className="w-3.5 h-3.5 text-emerald-400" />
          <span>Download Sample CSV</span>
        </button>
      </div>

      {/* Mode Selector Tabs */}
      <div className="flex space-x-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => {
            setActiveTab("CSV");
            setFile(null);
            setImportResult(null);
          }}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === "CSV"
              ? "bg-emerald-500 text-slate-950 font-bold"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <FileSpreadsheet className="w-4 h-4" />
          <span>Purchase CSV Importer (Idempotent)</span>
        </button>

        <button
          onClick={() => {
            setActiveTab("OCR");
            setFile(null);
            setOcrResult(null);
          }}
          className={`flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
            activeTab === "OCR"
              ? "bg-emerald-500 text-slate-950 font-bold"
              : "text-slate-400 hover:text-white"
          }`}
        >
          <Sparkles className="w-4 h-4" />
          <span>OCR / LayoutLM Document Parser (Interface Stub)</span>
        </button>
      </div>

      {/* Upload Box */}
      <div className="glass-card rounded-2xl p-8 border border-slate-800 text-center relative">
        <input
          type="file"
          id="fileInput"
          accept={activeTab === "CSV" ? ".csv" : ".pdf,image/*"}
          onChange={handleFileChange}
          className="hidden"
        />

        <label
          htmlFor="fileInput"
          className="cursor-pointer block border-2 border-dashed border-slate-700 hover:border-emerald-500/60 rounded-2xl p-8 transition-colors bg-[#0B101D]/50"
        >
          <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mx-auto mb-3 border border-emerald-500/20">
            <UploadCloud className="w-7 h-7" />
          </div>
          <div className="text-sm font-bold text-white mb-1">
            {file ? file.name : `Choose or drag & drop ${activeTab === "CSV" ? "a CSV" : "a PDF/Image"} invoice`}
          </div>
          <p className="text-xs text-slate-400">
            {activeTab === "CSV"
              ? "Columns: item, batch_no, expiry, distributor, qty, price, invoice_no"
              : "Supported formats: PDF, PNG, JPG (Invoice layout token extraction)"}
          </p>
        </label>

        {file && (
          <div className="mt-5 flex items-center justify-center space-x-3">
            <button
              onClick={activeTab === "CSV" ? handleProcessCsv : handleProcessOcr}
              disabled={uploading}
              className="px-6 py-2.5 rounded-xl text-xs font-semibold bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold shadow-md shadow-emerald-500/20 flex items-center space-x-2 transition-all hover:scale-[1.02] disabled:opacity-50"
            >
              {uploading ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <ArrowRight className="w-3.5 h-3.5" />
                  <span>Execute {activeTab === "CSV" ? "CSV Ingestion" : "OCR Extraction"}</span>
                </>
              )}
            </button>
          </div>
        )}

        {errorMsg && (
          <div className="mt-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-medium">
            {errorMsg}
          </div>
        )}
      </div>

      {/* CSV Result Summary Card */}
      {importResult && (
        <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h2 className="text-base font-bold text-white flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Import Execution Report: {importResult.filename}</span>
            </h2>
            <span className="text-xs text-slate-400">
              Processed: <span className="text-white font-bold">{importResult.total_rows_processed}</span> Rows
            </span>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-[#0D1322] border border-slate-800">
              <div className="text-[11px] text-slate-400">New Batches Created</div>
              <div className="text-2xl font-bold text-emerald-400 mt-1">
                {importResult.new_batches_imported}
              </div>
            </div>
            <div className="p-4 rounded-xl bg-[#0D1322] border border-slate-800">
              <div className="text-[11px] text-slate-400">Existing Updated (Idempotent)</div>
              <div className="text-2xl font-bold text-cyan-400 mt-1">
                {importResult.existing_batches_updated}
              </div>
            </div>
            <div className="p-4 rounded-xl bg-[#0D1322] border border-slate-800">
              <div className="text-[11px] text-slate-400">Row Errors</div>
              <div className={`text-2xl font-bold mt-1 ${importResult.error_count > 0 ? "text-rose-400" : "text-slate-400"}`}>
                {importResult.error_count}
              </div>
            </div>
          </div>

          {/* Row-Level Errors Grid */}
          {importResult.error_count > 0 && (
            <div className="mt-4 pt-4 border-t border-slate-800">
              <h3 className="text-xs font-semibold text-rose-400 uppercase tracking-wider mb-2 flex items-center space-x-1.5">
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Row-Level Validation Failures (Other rows safely imported)</span>
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs border border-slate-800 rounded-xl overflow-hidden">
                  <thead>
                    <tr className="bg-[#0B101D] text-slate-400 border-b border-slate-800">
                      <th className="py-2 px-3 font-semibold">Row #</th>
                      <th className="py-2 px-3 font-semibold">Error Reason</th>
                      <th className="py-2 px-3 font-semibold">Raw Data</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {importResult.errors.map((err: any, idx: number) => (
                      <tr key={idx} className="hover:bg-slate-800/20">
                        <td className="py-2 px-3 font-mono text-rose-400 font-bold">{err.row}</td>
                        <td className="py-2 px-3 text-slate-200">{err.error}</td>
                        <td className="py-2 px-3 font-mono text-[10px] text-slate-400">
                          {JSON.stringify(err.raw_data)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* OCR Result View */}
      {ocrResult && (
        <div className="glass-card rounded-2xl p-6 border border-slate-800 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h2 className="text-base font-bold text-white flex items-center space-x-2">
                <Sparkles className="w-4 h-4 text-emerald-400" />
                <span>LayoutLM Document Parser Stub</span>
              </h2>
              <p className="text-xs text-slate-400 font-mono mt-0.5">Model: {ocrResult.parser_model}</p>
            </div>
            <span className="text-xs text-emerald-400 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
              Confidence &ge; 95%
            </span>
          </div>

          <div className="p-3 rounded-xl bg-[#0B101D] border border-slate-800 text-xs text-slate-300">
            <span className="font-semibold text-slate-100">Extracted Invoice Header:</span> No: {ocrResult.invoice_no} | Date: {ocrResult.invoice_date} | Distributor: {ocrResult.distributor_name} (GSTIN: {ocrResult.distributor_gstin})
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 text-[10px] uppercase">
                  <th className="py-2 px-3 font-semibold">Medicine</th>
                  <th className="py-2 px-3 font-semibold">Batch No</th>
                  <th className="py-2 px-3 font-semibold">Expiry</th>
                  <th className="py-2 px-3 font-semibold text-right">Qty</th>
                  <th className="py-2 px-3 font-semibold text-right">Price (₹)</th>
                  <th className="py-2 px-3 font-semibold text-right">Confidence</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {ocrResult.items.map((it: any, i: number) => (
                  <tr key={i}>
                    <td className="py-2 px-3 font-semibold text-white">{it.item_name}</td>
                    <td className="py-2 px-3 font-mono text-slate-300">{it.batch_no}</td>
                    <td className="py-2 px-3 text-slate-300">{it.expiry_date}</td>
                    <td className="py-2 px-3 text-right">{it.qty}</td>
                    <td className="py-2 px-3 text-right">₹{it.purchase_price.toFixed(2)}</td>
                    <td className="py-2 px-3 text-right text-emerald-400 font-bold">
                      {(it.confidence_score * 100).toFixed(0)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <p className="text-[11px] text-slate-500 italic mt-2">{ocrResult.notes}</p>
        </div>
      )}
    </div>
  );
}
