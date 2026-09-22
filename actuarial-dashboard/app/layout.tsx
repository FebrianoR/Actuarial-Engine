import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Actuarial Engine – PSAK 117",
  description: "Engine Perhitungan Aktuaria PSAK 117 – BBA, PAA, VFA",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="id">
      <body className={inter.className}>
        <div className="flex min-h-screen bg-slate-100">
          <Sidebar />
          <main className="flex-1 ml-64 p-6 overflow-auto">{children}</main>
        </div>
      </body>
    </html>
  );
}
