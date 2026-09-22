"use client";
import { useEffect, useState } from "react";
import { BookOpen, RefreshCw, CheckCircle } from "lucide-react";
import { API_BASE, API_HEADERS } from "@/lib/api";

const API = API_BASE;

export default function AssumptionsPage() {
    const [assumptions, setAssumptions] = useState<Record<string, unknown>[]>([]);
    const [loading, setLoading] = useState(true);

    const load = () => {
        setLoading(true);
        fetch(`${API}/assumptions/`, { headers: API_HEADERS })
            .then(r => r.json())
            .then(d => { setAssumptions(Array.isArray(d) ? d : []); setLoading(false); })
            .catch(() => setLoading(false));
    };

    useEffect(() => { load(); }, []);

    return (
        <div className="space-y-5 max-w-4xl">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-slate-800">Asumsi Aktuaria</h1>
                    <p className="text-slate-500 text-sm mt-1">Manajemen set asumsi PSAK 117</p>
                </div>
                <button onClick={load}
                    className="flex items-center gap-2 px-3 py-2 border border-slate-200 bg-white rounded-lg text-sm hover:bg-slate-50">
                    <RefreshCw className="w-4 h-4" /> Refresh
                </button>
            </div>

            {/* Base assumptions info */}
            <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm">
                <div className="flex items-center gap-3 mb-4">
                    <div className="w-9 h-9 rounded-lg bg-blue-100 flex items-center justify-center">
                        <BookOpen className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                        <h2 className="font-semibold text-slate-800">Asumsi Dasar (TMI-3 2011)</h2>
                        <p className="text-xs text-slate-500">Data default dari <code>base_assumptions.json</code></p>
                    </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    {[
                        { label: "Tabel Mortalita", value: "TMI-3 2011", ok: true },
                        { label: "Metode RA", value: "Cost of Capital (CoC)", ok: true },
                        { label: "CoC Rate", value: "6% per tahun", ok: true },
                        { label: "Yield Curve", value: "OJK Q4 2024", ok: true },
                        { label: "Inflasi Klaim", value: "3% per tahun", ok: true },
                        { label: "Expense Ratio", value: "5% of premium", ok: true },
                    ].map(({ label, value, ok }) => (
                        <div key={label} className="bg-slate-50 rounded-lg p-3">
                            <p className="text-xs text-slate-500">{label}</p>
                            <div className="flex items-center gap-1.5 mt-1">
                                {ok && <CheckCircle className="w-3.5 h-3.5 text-green-500" />}
                                <p className="text-sm font-medium text-slate-700">{value}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Asumsi yang diupload */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="p-4 border-b border-slate-100">
                    <h2 className="font-semibold text-slate-800">Asumsi Tersimpan</h2>
                    <p className="text-xs text-slate-500 mt-0.5">{assumptions.length} set asumsi</p>
                </div>
                {loading ? (
                    <div className="p-8 text-center text-slate-400">Memuat...</div>
                ) : assumptions.length === 0 ? (
                    <div className="p-8 text-center">
                        <p className="text-slate-500 text-sm">Belum ada asumsi yang disimpan.</p>
                        <p className="text-slate-400 text-xs mt-1">Upload 01-templateassumption.xlsx di halaman Upload.</p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead className="bg-slate-50">
                                <tr>
                                    {["ID", "Nama", "Versi", "Dibuat"].map(h => (
                                        <th key={h} className="px-4 py-2.5 text-left text-xs font-semibold text-slate-600">{h}</th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody>
                                {assumptions.map((a, i) => (
                                    <tr key={i} className="border-t border-slate-50 hover:bg-slate-50/50">
                                        <td className="px-4 py-2.5 font-mono text-xs text-slate-500">{String(a.id || i)}</td>
                                        <td className="px-4 py-2.5 text-slate-700">{String(a.name || "–")}</td>
                                        <td className="px-4 py-2.5">{String(a.version || "–")}</td>
                                        <td className="px-4 py-2.5 text-slate-500 text-xs">{String(a.created_at || "–")}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>

            {/* Upload prompt */}
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm text-blue-700">
                <p className="font-semibold mb-1">💡 Upload Asumsi Baru</p>
                <p className="text-blue-600 text-xs">
                    Pergi ke <a href="/upload" className="underline font-medium">halaman Upload</a> dan upload{" "}
                    <code className="bg-blue-100 px-1 rounded">01-templateassumption.xlsx</code> untuk menambah set asumsi baru.
                </p>
            </div>
        </div>
    );
}
