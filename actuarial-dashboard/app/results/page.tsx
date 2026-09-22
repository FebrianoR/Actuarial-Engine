"use client";
import { useEffect, useState, useMemo } from "react";
import { Download, Search, Filter, TrendingUp, AlertTriangle } from "lucide-react";
import { API_BASE, API_HEADERS } from "@/lib/api";

const API = API_BASE;

const fmt = (n: number) =>
    new Intl.NumberFormat("id-ID", { style: "decimal", maximumFractionDigits: 0 }).format(n);

interface PolicyResult {
    policyno: string; contract_id: string; cob: string; method: string;
    tsi: number; gwp: number; pvfcf: number; risk_adjustment: number; csm: number;
    lrc_net: number; lic: number; insurance_contract_liability: number; total_liability: number;
    is_onerous: boolean; trace_id: string; status: string; error?: string;
}

interface BatchData {
    batch_id: string;
    statistics: Record<string, number>;
    results: PolicyResult[];
    calculated_at: string;
}

export default function ResultsPage() {
    const [batch, setBatch] = useState<BatchData | null>(null);
    const [search, setSearch] = useState("");
    const [filterMethod, setFilterMethod] = useState("ALL");
    const [filterCob, setFilterCob] = useState("ALL");
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Coba load dari localStorage
        const stored = sessionStorage.getItem("lastBatchResult");
        if (stored) {
            setBatch(JSON.parse(stored));
        }
        setLoading(false);
    }, []);

    const results = batch?.results || [];

    const cobs = useMemo(() => ["ALL", ...Array.from(new Set(results.map(r => r.cob))).filter(Boolean)], [results]);
    const methods = ["ALL", "PAA", "GMM"];

    const filtered = useMemo(() => results.filter(r => {
        const matchSearch = !search || r.policyno?.includes(search) || r.contract_id?.includes(search);
        const matchMethod = filterMethod === "ALL" || r.method === filterMethod;
        const matchCob = filterCob === "ALL" || r.cob === filterCob;
        return matchSearch && matchMethod && matchCob;
    }), [results, search, filterMethod, filterCob]);

    const totals = useMemo(() => ({
        lrc: filtered.reduce((s, r) => s + (r.lrc_net || 0), 0),
        lic: filtered.reduce((s, r) => s + (r.lic || 0), 0),
        icl: filtered.reduce((s, r) => s + (r.insurance_contract_liability || r.total_liability || 0), 0),
    }), [filtered]);

    const handleExcelExport = () => {
        if (!batch?.batch_id) return;
        window.open(`${API}/export/excel/${batch.batch_id}?api_key=...`, "_blank");
        // Use fetch with API key
        fetch(`${API}/export/excel/${batch.batch_id}`, { headers: API_HEADERS })
            .then(r => r.blob())
            .then(blob => {
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `PSAK117_Hasil_${batch.batch_id.slice(0, 8)}.xlsx`;
                a.click();
                URL.revokeObjectURL(url);
            });
    };

    const handleCsvExport = () => {
        if (!batch?.batch_id) return;
        fetch(`${API}/export/csv/${batch.batch_id}`, { headers: API_HEADERS })
            .then(r => r.blob())
            .then(blob => {
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `PSAK117_Hasil_${batch.batch_id.slice(0, 8)}.csv`;
                a.click();
                URL.revokeObjectURL(url);
            });
    };

    if (loading) return <div className="text-slate-500 p-8">Memuat data...</div>;

    if (!batch) {
        return (
            <div className="flex flex-col items-center justify-center h-96 text-center">
                <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center mb-4">
                    <TrendingUp className="w-8 h-8 text-slate-400" />
                </div>
                <h2 className="text-xl font-semibold text-slate-700">Belum Ada Hasil</h2>
                <p className="text-slate-500 mt-2">Upload dan proses data terlebih dahulu</p>
                <a href="/upload"
                    className="mt-4 bg-[#1B3A6B] text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-[#2E6DB4]">
                    Pergi ke Upload
                </a>
            </div>
        );
    }

    return (
        <div className="space-y-5">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800">Hasil Kalkulasi</h1>
                    <p className="text-sm text-slate-500">Batch: {batch.batch_id.slice(0, 16)}... • {batch.calculated_at?.slice(0, 10)}</p>
                </div>
                <div className="flex gap-2">
                    <button onClick={handleCsvExport}
                        className="flex items-center gap-2 px-3 py-2 border border-slate-200 bg-white rounded-lg text-sm font-medium hover:bg-slate-50">
                        <Download className="w-4 h-4" /> CSV
                    </button>
                    <button onClick={handleExcelExport}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700">
                        <Download className="w-4 h-4" /> Export Excel
                    </button>
                </div>
            </div>

            {/* Totals */}
            <div className="grid grid-cols-3 gap-4">
                {[
                    { label: "Total LRC Neto", val: totals.lrc, color: "text-blue-700" },
                    { label: "Total LIC (Klaim)", val: totals.lic, color: "text-amber-700" },
                    { label: "Total ICL", val: totals.icl, color: "text-green-700" },
                ].map(({ label, val, color }) => (
                    <div key={label} className="bg-white rounded-xl p-4 shadow-sm border border-slate-100">
                        <p className="text-xs text-slate-500">{label}</p>
                        <p className={`text-lg font-bold ${color} mt-1`}>Rp {fmt(val)}</p>
                        <p className="text-xs text-slate-400">{filtered.length} polis dipilih</p>
                    </div>
                ))}
            </div>

            {/* Filters */}
            <div className="bg-white rounded-xl border border-slate-200 p-4 flex items-center gap-4 flex-wrap">
                <div className="relative flex-1 min-w-48">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <input type="text" placeholder="Cari nomor polis..." value={search}
                        onChange={e => setSearch(e.target.value)}
                        className="w-full pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-200" />
                </div>
                <div className="flex items-center gap-2">
                    <Filter className="w-4 h-4 text-slate-400" />
                    <select value={filterMethod} onChange={e => setFilterMethod(e.target.value)}
                        className="border border-slate-200 rounded-lg text-sm px-3 py-2 focus:outline-none">
                        {methods.map(m => <option key={m} value={m}>{m}</option>)}
                    </select>
                    <select value={filterCob} onChange={e => setFilterCob(e.target.value)}
                        className="border border-slate-200 rounded-lg text-sm px-3 py-2 focus:outline-none">
                        {cobs.map(c => <option key={c} value={c}>{c === "ALL" ? "Semua COB" : `COB: ${c}`}</option>)}
                    </select>
                </div>
                <span className="text-sm text-slate-500">{filtered.length} / {results.length} polis</span>
            </div>

            {/* Table */}
            <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
                <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                        <thead className="bg-[#1B3A6B] text-white">
                            <tr>
                                {["No", "Policy No", "COB", "Metode", "GWP", "LRC Neto", "LIC", "ICL / Total", "Onerous", "Status"].map(h => (
                                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold">{h}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {filtered.length === 0 ? (
                                <tr>
                                    <td colSpan={10} className="text-center text-slate-400 py-12">Tidak ada data</td>
                                </tr>
                            ) : (
                                filtered.map((r, i) => {
                                    const isOnerous = r.is_onerous;
                                    const total = r.insurance_contract_liability || r.total_liability || 0;
                                    return (
                                        <tr key={r.policyno || i}
                                            className={`border-b border-slate-50 hover:bg-slate-50 transition-colors ${isOnerous ? "bg-red-50" : i % 2 === 0 ? "bg-white" : "bg-slate-50/50"}`}>
                                            <td className="px-4 py-2.5 text-slate-500 text-xs">{i + 1}</td>
                                            <td className="px-4 py-2.5 font-mono text-xs">{r.policyno || r.contract_id}</td>
                                            <td className="px-4 py-2.5"><span className="bg-blue-100 text-blue-700 text-xs px-2 py-0.5 rounded">{r.cob}</span></td>
                                            <td className="px-4 py-2.5">
                                                <span className={`text-xs px-2 py-0.5 rounded font-medium ${r.method === "PAA" ? "bg-green-100 text-green-700" : "bg-purple-100 text-purple-700"}`}>
                                                    {r.method}
                                                </span>
                                            </td>
                                            <td className="px-4 py-2.5 text-right tabular-nums">{fmt(r.gwp || 0)}</td>
                                            <td className="px-4 py-2.5 text-right tabular-nums">{fmt(r.lrc_net || 0)}</td>
                                            <td className="px-4 py-2.5 text-right tabular-nums">{fmt(r.lic || 0)}</td>
                                            <td className="px-4 py-2.5 text-right tabular-nums font-semibold">{fmt(total)}</td>
                                            <td className="px-4 py-2.5">
                                                {isOnerous
                                                    ? <span className="flex items-center gap-1 text-red-600 text-xs"><AlertTriangle className="w-3 h-3" /> Ya</span>
                                                    : <span className="text-green-600 text-xs">Tidak</span>}
                                            </td>
                                            <td className="px-4 py-2.5">
                                                {r.status === "ok"
                                                    ? <span className="w-2 h-2 rounded-full bg-green-500 inline-block" />
                                                    : <span className="text-xs text-red-500">Error</span>}
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
