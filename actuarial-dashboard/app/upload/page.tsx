"use client";
import { useState, useCallback } from "react";
import { Upload as UploadIcon, CheckCircle, AlertCircle, Loader2, Play, X } from "lucide-react";
import { API_BASE, API_KEY, API_HEADERS } from "@/lib/api";

const API = API_BASE;
const KEY = API_KEY;

interface FileStatus {
    file: File | null;
    status: "idle" | "uploading" | "done" | "error";
    rows?: number;
    error?: string;
    preview?: Record<string, unknown>[];
}

type FileKey = "portfolio" | "assumptions" | "tabphei" | "lapse";

const TEMPLATE_INFO: Record<FileKey, { label: string; desc: string; endpoint: string; template: string }> = {
    portfolio: {
        label: "00 – Data Polis",
        desc: "00-Templateupload.xlsx (sheet: datapolis)",
        endpoint: "/upload/portfolio",
        template: "policyno, cob, product, gwp, tsi, smethode",
    },
    assumptions: {
        label: "01 – Asumsi Aktuaria",
        desc: "01-templateassumption.xlsx (sheet: assumsi)",
        endpoint: "/upload/assumptions",
        template: "sguser, cob, syear, expclaim, expopex, expriskadj",
    },
    tabphei: {
        label: "02 – Yield Curve",
        desc: "02-templatetabphei.xlsx (sheet: lrc_tabphei)",
        endpoint: "/upload/tabphei",
        template: "sguser, syear, sdate, srate",
    },
    lapse: {
        label: "03 – Lapse Table",
        desc: "03-templatelapse.xlsx (sheet: lrc_lapsemmtable)",
        endpoint: "/upload/lapse",
        template: "sguser, syear, smonth, cob, srate",
    },
};

async function uploadFile(key: FileKey, file: File): Promise<{ rows: number; preview: Record<string, unknown>[]; errors: string[] }> {
    const form = new FormData();
    form.append("file", file);
    const r = await fetch(`${API}${TEMPLATE_INFO[key].endpoint}`, {
        method: "POST",
        headers: { ...API_HEADERS },
        body: form,
    });
    if (!r.ok) throw new Error(await r.text());
    return r.json().then(d => ({ rows: d.rows_parsed, preview: d.preview || [], errors: d.errors || [] }));
}

export default function UploadPage() {
    const [files, setFiles] = useState<Record<FileKey, FileStatus>>({
        portfolio: { file: null, status: "idle" },
        assumptions: { file: null, status: "idle" },
        tabphei: { file: null, status: "idle" },
        lapse: { file: null, status: "idle" },
    });

    const [batchStatus, setBatchStatus] = useState<"idle" | "running" | "done" | "error">("idle");
    const [batchResult, setBatchResult] = useState<Record<string, unknown> | null>(null);

    const handleDrop = useCallback(async (key: FileKey, f: File) => {
        setFiles(prev => ({ ...prev, [key]: { file: f, status: "uploading" } }));
        try {
            const res = await uploadFile(key, f);
            setFiles(prev => ({
                ...prev,
                [key]: { file: f, status: "done", rows: res.rows, preview: res.preview, error: res.errors[0] },
            }));
        } catch (e: unknown) {
            const msg = e instanceof Error ? e.message : String(e);
            setFiles(prev => ({ ...prev, [key]: { file: f, status: "error", error: msg } }));
        }
    }, []);

    const handleFileInput = (key: FileKey, e: React.ChangeEvent<HTMLInputElement>) => {
        const f = e.target.files?.[0];
        if (f) handleDrop(key, f);
    };

    const runBatch = async () => {
        setBatchStatus("running");
        try {
            const r = await fetch(`${API}/upload/batch-calculate`, {
                method: "POST",
                headers: { ...API_HEADERS, "Content-Type": "application/json" },
                body: JSON.stringify({}),
            });
            if (!r.ok) throw new Error(await r.text());
            const data = await r.json();
            setBatchResult(data);
            setBatchStatus("done");
            localStorage.setItem("lastBatchId", data.batch_id);
            sessionStorage.setItem("lastBatchResult", JSON.stringify(data));
        } catch (e: unknown) {
            const msg = e instanceof Error ? e.message : String(e);
            setBatchStatus("error");
            setBatchResult({ error: msg });
        }
    };

    const portfolioDone = files.portfolio.status === "done";
    const stats = batchResult && (batchResult as Record<string, Record<string, number>>).statistics;

    return (
        <div className="space-y-6 max-w-5xl">
            <div>
                <h1 className="text-2xl font-bold text-slate-800">Upload Template Excel</h1>
                <p className="text-slate-500 text-sm mt-1">Upload 4 template Excel PSAK 117 lalu klik Proses Kalkulasi</p>
            </div>

            {/* Upload cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {(Object.keys(TEMPLATE_INFO) as FileKey[]).map((key) => {
                    const info = TEMPLATE_INFO[key];
                    const state = files[key];
                    const isRequired = key === "portfolio";

                    return (
                        <div key={key}
                            className={`bg-white rounded-xl border-2 transition-all ${state.status === "done"
                                ? "border-green-400"
                                : state.status === "error"
                                    ? "border-red-400"
                                    : "border-slate-200 hover:border-blue-300"}`}>
                            <div className="p-4">
                                <div className="flex items-center justify-between mb-2">
                                    <div>
                                        <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${isRequired ? "bg-red-100 text-red-600" : "bg-slate-100 text-slate-600"}`}>
                                            {isRequired ? "WAJIB" : "Opsional"}
                                        </span>
                                    </div>
                                    {state.status === "done" && <CheckCircle className="w-5 h-5 text-green-500" />}
                                    {state.status === "error" && <AlertCircle className="w-5 h-5 text-red-500" />}
                                    {state.status === "uploading" && <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />}
                                </div>
                                <h3 className="font-semibold text-slate-800">{info.label}</h3>
                                <p className="text-xs text-slate-500 mt-0.5">{info.desc}</p>
                                <p className="text-xs text-slate-400 font-mono mt-1">{info.template}</p>
                            </div>

                            <label className="block mx-4 mb-4 cursor-pointer"
                                onDrop={e => { e.preventDefault(); const f = e.dataTransfer.files[0]; if (f) handleDrop(key, f); }}
                                onDragOver={e => e.preventDefault()}>
                                <div className={`border-2 border-dashed rounded-lg p-4 text-center transition-colors
                  ${state.status === "done" ? "border-green-300 bg-green-50" : "border-slate-200 bg-slate-50 hover:border-blue-300 hover:bg-blue-50"}`}>
                                    {state.status === "done" ? (
                                        <div>
                                            <CheckCircle className="w-6 h-6 text-green-500 mx-auto mb-1" />
                                            <p className="text-sm text-green-700 font-medium">{state.rows?.toLocaleString()} baris ter-parse</p>
                                            <p className="text-xs text-slate-500 truncate max-w-[200px] mx-auto">{state.file?.name}</p>
                                        </div>
                                    ) : state.status === "error" ? (
                                        <div>
                                            <X className="w-6 h-6 text-red-500 mx-auto mb-1" />
                                            <p className="text-xs text-red-600">{state.error?.slice(0, 80)}</p>
                                        </div>
                                    ) : (
                                        <div>
                                            <UploadIcon className="w-6 h-6 text-slate-400 mx-auto mb-1" />
                                            <p className="text-sm text-slate-600">Drop file di sini atau klik</p>
                                            <p className="text-xs text-slate-400">Format: .xlsx</p>
                                        </div>
                                    )}
                                </div>
                                <input type="file" accept=".xlsx" className="hidden" onChange={e => handleFileInput(key, e)} />
                            </label>

                            {/* Preview */}
                            {state.preview && state.preview.length > 0 && (
                                <div className="px-4 pb-4">
                                    <p className="text-xs font-medium text-slate-500 mb-1">Preview (5 baris pertama):</p>
                                    <div className="overflow-x-auto rounded border border-slate-100">
                                        <table className="text-xs w-full">
                                            <thead className="bg-slate-50">
                                                <tr>{Object.keys(state.preview[0]).map(k => <th key={k} className="px-2 py-1 text-left text-slate-600">{k}</th>)}</tr>
                                            </thead>
                                            <tbody>
                                                {state.preview.map((row, i) => (
                                                    <tr key={i} className={i % 2 === 0 ? "bg-white" : "bg-slate-50"}>
                                                        {Object.values(row).map((v, j) => <td key={j} className="px-2 py-1 text-slate-700 max-w-[100px] truncate">{String(v ?? "")}</td>)}
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>

            {/* Batch Button */}
            <div className="bg-white rounded-xl border border-slate-200 p-5">
                <div className="flex items-center justify-between">
                    <div>
                        <h3 className="font-semibold text-slate-800">Proses Kalkulasi Batch</h3>
                        <p className="text-sm text-slate-500">
                            {portfolioDone
                                ? `${files.portfolio.rows?.toLocaleString()} polis siap diproses`
                                : "Upload data polis terlebih dahulu"}
                        </p>
                    </div>
                    <button onClick={runBatch}
                        disabled={!portfolioDone || batchStatus === "running"}
                        className={`flex items-center gap-2 px-5 py-2.5 rounded-lg font-medium text-sm transition-all
              ${portfolioDone && batchStatus !== "running"
                                ? "bg-[#1B3A6B] text-white hover:bg-[#2E6DB4] shadow-md hover:shadow-lg"
                                : "bg-slate-100 text-slate-400 cursor-not-allowed"}`}>
                        {batchStatus === "running"
                            ? <><Loader2 className="w-4 h-4 animate-spin" /> Memproses...</>
                            : <><Play className="w-4 h-4" /> Proses Kalkulasi</>}
                    </button>
                </div>

                {/* Result */}
                {batchStatus === "done" && stats && (
                    <div className="mt-4 p-4 bg-green-50 rounded-lg border border-green-200">
                        <div className="flex items-center gap-2 mb-3">
                            <CheckCircle className="w-5 h-5 text-green-600" />
                            <span className="font-semibold text-green-700">Kalkulasi Selesai!</span>
                        </div>
                        <div className="grid grid-cols-3 gap-3">
                            {[
                                ["Total Polis", (stats as Record<string, number>).total],
                                ["Berhasil", (stats as Record<string, number>).success],
                                ["PAA", (stats as Record<string, number>).paa_count],
                                ["GMM", (stats as Record<string, number>).gmm_count],
                                ["Error", (stats as Record<string, number>).error],
                                ["Total ICL", new Intl.NumberFormat("id-ID").format((stats as Record<string, number>).total_icl)],
                            ].map(([label, val]) => (
                                <div key={label as string} className="text-center">
                                    <p className="text-xs text-slate-500">{label as string}</p>
                                    <p className="font-bold text-slate-700">{val}</p>
                                </div>
                            ))}
                        </div>
                        <div className="mt-3 pt-3 border-t border-green-200">
                            <a href="/results" className="text-sm text-blue-600 font-medium hover:underline">
                                → Lihat Hasil Kalkulasi
                            </a>
                        </div>
                    </div>
                )}

                {batchStatus === "error" && (
                    <div className="mt-4 p-4 bg-red-50 rounded-lg border border-red-200">
                        <div className="flex items-center gap-2">
                            <AlertCircle className="w-5 h-5 text-red-600" />
                            <span className="font-medium text-red-700">Error: {String((batchResult as Record<string, unknown>)?.error ?? "Unknown error")}</span>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
