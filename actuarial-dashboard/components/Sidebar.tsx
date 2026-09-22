"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutDashboard, Upload, BarChart3, FileText,
    BookOpen, Settings, Activity
} from "lucide-react";

const nav = [
    { href: "/", label: "Dashboard", icon: LayoutDashboard },
    { href: "/upload", label: "Upload Data", icon: Upload },
    { href: "/results", label: "Hasil Kalkulasi", icon: BarChart3 },
    { href: "/audit", label: "Audit Trail", icon: FileText },
    { href: "/assumptions", label: "Asumsi", icon: BookOpen },
];

export default function Sidebar() {
    const path = usePathname();
    return (
        <aside className="fixed left-0 top-0 h-full w-64 bg-[#1B3A6B] flex flex-col shadow-xl z-50">
            {/* Logo */}
            <div className="p-5 border-b border-white/10">
                <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-lg bg-blue-400 flex items-center justify-center">
                        <Activity className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <p className="text-white font-bold text-sm leading-tight">Actuarial Engine</p>
                        <p className="text-blue-300 text-xs">PSAK 117</p>
                    </div>
                </div>
            </div>

            {/* Nav */}
            <nav className="flex-1 p-3 space-y-1">
                {nav.map(({ href, label, icon: Icon }) => {
                    const active = path === href;
                    return (
                        <Link key={href} href={href}
                            className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all
                ${active
                                    ? "bg-white/15 text-white shadow-sm"
                                    : "text-blue-200 hover:bg-white/10 hover:text-white"}`}>
                            <Icon className="w-4 h-4 flex-shrink-0" />
                            {label}
                        </Link>
                    );
                })}
            </nav>

            {/* API Status */}
            <div className="p-4 border-t border-white/10">
                <div className="flex items-center gap-2 text-xs text-blue-300">
                    <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                    API: localhost:8000
                </div>
            </div>
        </aside>
    );
}
