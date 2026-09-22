"use client";
import { useEffect, useState } from "react";
import { FileText, ChevronDown, ChevronRight, Clock, CheckCircle } from "lucide-react";
import { API_BASE, API_KEY, API_HEADERS } from "@/lib/api";

const API = API_BASE;
const KEY = API_KEY;

interface AuditRecord {
    trace_id: string;
    calculation_type: string;   // "BBA" | "PAA"
    contract_id: string;
    assumption_version?: string;
    created_at: string;
    spa04_compliant: boolean;
    input_snapshot?: Record<string, unknown>;
    output_snapshot?: Record<string, unknown>;
    steps?: Record<string, unknown>;
}

function MethodBadge({ type }: { type: string }) {
    const t = type?.toUpperCase();
    const cls = t === "BBA"
        ? "bg-purple-100 text-purple-700 border border-purple-200"
        : t === "PAA"
            ? "bg-green-100 text-green-700 border border-green-200"
            : "bg-slate-100 text-slate-600 border border-slate-200";
    return <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${cls}`}>{t || "–"}</span>;
}

const fmt = (v: unknown): string => {
    if (typeof v === "number") return new Intl.NumberFormat("id-ID", { maximumFractionDigits: 2 }).format(v);
    if (typeof v === "object" && v !== null) return JSON.stringify(v).slice(0, 120);
    return String(v ?? "–");
};

export default function AuditPage() {
    const [records, setRecords] = useState<AuditRecord[]>([]);
    const [expanded, setExpanded] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`${API}/audit/`, { headers: API_HEADERS })
            .then(r => r.json())
            .then(d => { setRecords(Array.isArray(d) ? d : []); setLoading(false); })
            .catch(() => setLoading(false));
    }, []);

    const toggleExpand = (id: string) =>
        setExpanded(prev => prev === id ? null : id);

    const selectedRecord = records.find(r => r.trace_id === expanded);

    return (
        <div className="space-y-5 max-w-4xl">
            <div>
                <h1 className="text-2xl font-bold text-slate-800">Audit Trail</h1>
                <p className="text-slate-500 text-sm mt-1">
                    Riwayat kalkulasi aktuaria sesuai SPA-04 • {records.length} records
                </p>
            </div>

            {loading ? (
                <div className="text-slate-400 p-8 text-center">Memuat...</div>
            ) : records.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-64 text-center">
                    <FileText className="w-12 h-12 text-slate-300 mb-3" />
                    <p className="text-slate-500">Belum ada audit record. Lakukan kalkulasi terlebih dahulu.</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 gap-2">
                    {records.map((rec) => {
                        const isOpen = expanded === rec.trace_id;
                        return (
                            <div key={rec.trace_id}
                                className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                                {/* Header row */}
                                <button
                                    onClick={() => toggleExpand(rec.trace_id)}
                                    className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-50 transition-colors text-left">
                                    <div className="flex items-center gap-3 min-w-0">
                                        <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center flex-shrink-0">
                                            <FileText className="w-4 h-4 text-slate-500" />
                                        </div>
                                        <div className="min-w-0">
                                            {/* Policy no + method badge */}
                                            <div className="flex items-center gap-2 flex-wrap">
                                                <span className="font-semibold text-slate-800 text-sm">
                                                    {rec.contract_id || "–"}
                                                </span>
                                                <MethodBadge type={rec.calculation_type} />
                                                {rec.spa04_compliant && (
                                                    <span className="flex items-center gap-0.5 text-xs text-green-600">
                                                        <CheckCircle className="w-3 h-3" /> SPA-04
                                                    </span>
                                                )}
                                            </div>
                                            {/* trace_id */}
                                            <p className="font-mono text-xs text-slate-400 truncate mt-0.5">
                                                {rec.trace_id}
                                            </p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3 flex-shrink-0 ml-3">
                                        <div className="flex items-center gap-1 text-xs text-slate-400">
                                            <Clock className="w-3.5 h-3.5" />
                                            {rec.created_at
                                                ? new Date(rec.created_at).toLocaleString("id-ID", {
                                                    day: "2-digit", month: "short", year: "numeric",
                                                    hour: "2-digit", minute: "2-digit",
                                                })
                                                : "–"}
                                        </div>
                                        {isOpen
                                            ? <ChevronDown className="w-4 h-4 text-slate-400" />
                                            : <ChevronRight className="w-4 h-4 text-slate-400" />
                                        }
                                    </div>
                                </button>

                                {/* Expanded detail */}
                                {isOpen && selectedRecord && (
                                    <div className="border-t border-slate-100 bg-slate-50/60 p-4 space-y-4">
                                        {/* Input / Output summary */}
                                        <div className="grid grid-cols-2 gap-3">
                                            {/* Input */}
                                            {rec.input_snapshot && Object.keys(rec.input_snapshot).length > 0 && (
                                                <div className="bg-white rounded-lg border border-slate-100 p-3">
                                                    <p className="text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wide">Input</p>
                                                    <div className="space-y-1">
                                                        {Object.entries(rec.input_snapshot).map(([k, v]) => (
                                                            <div key={k} className="flex justify-between gap-2">
                                                                <span className="text-xs text-slate-500 font-mono">{k}</span>
                                                                <span className="text-xs text-slate-700 font-medium text-right">{fmt(v)}</span>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                            {/* Output */}
                                            {rec.output_snapshot && Object.keys(rec.output_snapshot).length > 0 && (
                                                <div className="bg-white rounded-lg border border-slate-100 p-3">
                                                    <p className="text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wide">Output</p>
                                                    <div className="space-y-1">
                                                        {Object.entries(rec.output_snapshot).map(([k, v]) => (
                                                            <div key={k} className="flex justify-between gap-2">
                                                                <span className="text-xs text-slate-500 font-mono">{k}</span>
                                                                <span className="text-xs text-slate-700 font-semibold text-right">{fmt(v)}</span>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>

                                        {/* Intermediate Steps */}
                                        {rec.steps && Object.keys(rec.steps).length > 0 && (
                                            <div>
                                                <p className="text-xs font-semibold text-slate-500 mb-2 uppercase tracking-wide">
                                                    Intermediate Steps ({Object.keys(rec.steps).length})
                                                </p>
                                                <div className="space-y-1">
                                                    {Object.entries(rec.steps).map(([step, val]) => {
                                                        const v = (val as Record<string, unknown>)?.value ?? val;
                                                        return (
                                                            <div key={step}
                                                                className="flex items-start justify-between bg-white rounded-lg px-3 py-2 border border-slate-100 gap-4">
                                                                <span className="text-xs font-mono text-[#1B3A6B] font-medium flex-shrink-0">{step}</span>
                                                                <span className="text-xs text-slate-600 font-mono text-right break-all">{fmt(v)}</span>
                                                            </div>
                                                        );
                                                    })}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
