"use client";
import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from "recharts";
import { TrendingUp, FileText, AlertTriangle, CheckCircle, ArrowRight } from "lucide-react";
import Link from "next/link";
import { API_BASE, API_HEADERS } from "@/lib/api";

const API = API_BASE;
const h = API_HEADERS;

const COLORS = ["#2E6DB4", "#16A34A", "#D97706", "#DC2626", "#7C3AED"];
const fmt = (n: number) => new Intl.NumberFormat("id-ID").format(Math.round(n));

interface Stats {
  total: number; paa_count: number; gmm_count: number;
  total_icl: number; total_lrc: number; total_lic: number;
  success: number; error: number;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [auditCount, setAuditCount] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`${API}/upload/session-status`, { headers: h }).then(r => r.json()).catch(() => null),
      fetch(`${API}/audit/`, { headers: h }).then(r => r.json()).catch(() => []),
    ]).then(([session, audits]) => {
      setAuditCount(Array.isArray(audits) ? audits.length : 0);
      setLoading(false);
    });
  }, []);

  const pieData = stats ? [
    { name: "PAA", value: stats.paa_count || 0 },
    { name: "GMM/BBA", value: stats.gmm_count || 0 },
  ] : [{ name: "PAA", value: 1 }, { name: "GMM/BBA", value: 1 }];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>
          <p className="text-slate-500 text-sm mt-0.5">Actuarial Engine PSAK 117 – Ringkasan Portofolio</p>
        </div>
        <Link href="/upload"
          className="flex items-center gap-2 bg-[#1B3A6B] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#2E6DB4] transition-colors">
          Upload Data <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "Total Kalkulasi", value: auditCount.toString(), icon: FileText, color: "text-blue-600", bg: "bg-blue-50" },
          { label: "Total ICL", value: stats ? `Rp ${fmt(stats.total_icl)}` : "–", icon: TrendingUp, color: "text-green-600", bg: "bg-green-50" },
          { label: "Polis Berhasil", value: stats ? stats.success.toString() : "–", icon: CheckCircle, color: "text-emerald-600", bg: "bg-emerald-50" },
          { label: "Error", value: stats ? stats.error.toString() : "0", icon: AlertTriangle, color: "text-amber-600", bg: "bg-amber-50" },
        ].map(({ label, value, icon: Icon, color, bg }) => (
          <div key={label} className="bg-white rounded-xl p-5 shadow-sm border border-slate-100">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-slate-500">{label}</span>
              <div className={`w-9 h-9 rounded-lg ${bg} flex items-center justify-center`}>
                <Icon className={`w-5 h-5 ${color}`} />
              </div>
            </div>
            <p className="text-2xl font-bold text-slate-800">{value}</p>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Distribusi Metode */}
        <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-100">
          <h2 className="font-semibold text-slate-700 mb-4">Distribusi Metode Kalkulasi</h2>
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%" cy="45%"
                innerRadius={55} outerRadius={85}
                dataKey="value"
                labelLine={false}
                label={({ cx = 0, cy = 0, midAngle = 0, innerRadius = 0, outerRadius = 0, percent = 0 }) => {
                  if (percent < 0.05) return null;
                  const RADIAN = Math.PI / 180;
                  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
                  const x = (cx as number) + radius * Math.cos(-midAngle * RADIAN);
                  const y = (cy as number) + radius * Math.sin(-midAngle * RADIAN);
                  return (
                    <text x={x} y={y} fill="white" textAnchor="middle" dominantBaseline="central"
                      fontSize={12} fontWeight="bold">
                      {`${(percent * 100).toFixed(0)}%`}
                    </text>
                  );
                }}
              >
                {pieData.map((_, idx) => (
                  <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                ))}
              </Pie>
              <Legend verticalAlign="bottom" height={36}
                formatter={(value) => <span style={{ fontSize: 12, color: '#475569' }}>{value}</span>} />
              <Tooltip
                formatter={(v, name) => [typeof v === 'number' ? `${fmt(v as number)} polis` : v, name]}
                contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: 12 }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Petunjuk Cepat */}
        <div className="bg-white rounded-xl p-5 shadow-sm border border-slate-100">
          <h2 className="font-semibold text-slate-700 mb-4">Panduan Penggunaan</h2>
          <div className="space-y-3">
            {[
              { step: "1", title: "Upload Template", desc: "Upload 4 file Excel template (Polis, Asumsi, YieldCurve, Lapse)", href: "/upload" },
              { step: "2", title: "Proses Kalkulasi", desc: "Klik tombol \"Proses Kalkulasi\" untuk menjalankan BBA/PAA", href: "/upload" },
              { step: "3", title: "Lihat Hasil", desc: "Tabel hasil per polis dengan filter dan sorting", href: "/results" },
              { step: "4", title: "Export", desc: "Download hasil sebagai Excel (3 sheet) atau CSV", href: "/results" },
            ].map(({ step, title, desc, href }) => (
              <Link key={step} href={href}
                className="flex items-start gap-3 p-3 rounded-lg hover:bg-slate-50 transition-colors group">
                <div className="w-7 h-7 rounded-full bg-[#1B3A6B] text-white text-xs font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
                  {step}
                </div>
                <div>
                  <p className="font-medium text-sm text-slate-700 group-hover:text-[#2E6DB4]">{title}</p>
                  <p className="text-xs text-slate-500">{desc}</p>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {[
          { title: "BBA / GMM", desc: "Untuk kontrak jiwa jangka panjang. PVFCF + RA + CSM = ICL.", color: "border-l-blue-500" },
          { title: "PAA", desc: "Untuk asuransi umum ≤1 tahun. LRC (unearned premium − DAC) + LIC.", color: "border-l-green-500" },
          { title: "VFA", desc: "Untuk produk unit-link. Variable fee dari underlying items.", color: "border-l-purple-500" },
        ].map(({ title, desc, color }) => (
          <div key={title} className={`bg-white rounded-xl p-4 shadow-sm border border-slate-100 border-l-4 ${color}`}>
            <h3 className="font-semibold text-slate-800 text-sm">{title}</h3>
            <p className="text-slate-500 text-xs mt-1">{desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
