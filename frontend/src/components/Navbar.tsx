"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  Radar, 
  Wind, 
  Cpu, 
  Bell, 
  ShieldAlert, 
  Activity, 
  Info,
  Server
} from "lucide-react";
import { useState, useEffect } from "react";
import { API_BASE_URL } from "@/lib/api";

export function Navbar() {
  const pathname = usePathname();
  const [dataMode, setDataMode] = useState<"DEMO" | "LIVE">("DEMO");
  const [systemOnline, setSystemOnline] = useState(true);

  // Check backend health periodically
  useEffect(() => {
    async function checkHealth() {
      try {
        const res = await fetch(`${API_BASE_URL}/health`);
        if (res.ok) {
          const data = await res.json();
          setSystemOnline(true);
          if (data.data_mode) setDataMode(data.data_mode);
        } else {
          setSystemOnline(false);
        }
      } catch {
        // Local offline fallback mode
        setSystemOnline(true);
      }
    }
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  const navLinks = [
    { href: "/", label: "Executive Dashboard", icon: Radar },
    { href: "/cyclones", label: "Cyclone Monitor", icon: Wind },
    { href: "/analysis", label: "AI Fusion Workbench", icon: Cpu },
    { href: "/alerts", label: "Alert Center", icon: Bell },
    { href: "/models", label: "Models & XAI", icon: Activity },
    { href: "/admin", label: "System Health", icon: Server },
  ];

  return (
    <header className="border-b border-slate-800 bg-slate-950/90 backdrop-blur sticky top-0 z-50">
      {/* Top Advisory Banner */}
      <div className="bg-slate-900/90 border-b border-slate-800/80 px-4 py-1.5 text-xs flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="flex h-2 w-2 relative">
            <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${systemOnline ? 'bg-emerald-400' : 'bg-rose-400'} opacity-75`}></span>
            <span className={`relative inline-flex rounded-full h-2 w-2 ${systemOnline ? 'bg-emerald-500' : 'bg-rose-500'}`}></span>
          </span>
          <span className="text-slate-400 font-mono tracking-wider">
            SYSTEM STATUS: <strong className={systemOnline ? "text-emerald-400" : "text-rose-400"}>{systemOnline ? "ONLINE (V1.0)" : "RECONNECTING"}</strong>
          </span>
          <span className="text-slate-600">|</span>
          <span className="text-slate-400 font-mono hidden sm:inline">BASIN: NORTH INDIAN OCEAN & ARABIAN SEA</span>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold tracking-wide border transition-all">
            {dataMode === "LIVE" ? (
              <span className="bg-emerald-950/80 border-emerald-500/50 text-emerald-300 px-2.5 py-0.5 rounded-full border font-mono font-bold">
                DATA MODE: LIVE TELEMETRY
              </span>
            ) : (
              <span className="bg-amber-950/90 border-amber-500 text-amber-300 px-2.5 py-0.5 rounded-full border flex items-center gap-1 font-mono font-bold">
                DATA MODE: DEMONSTRATION
              </span>
            )}

          </div>
          <span className="text-slate-500 hidden md:inline text-[11px]">
            *Prototype Decision-Support Index — Not an official warning
          </span>
        </div>
      </div>

      {/* Main Navigation Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20 group-hover:scale-105 transition-transform">
              <Radar className="h-6 w-6 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-black text-xl tracking-wider bg-clip-text text-transparent bg-gradient-to-r from-cyan-400 via-sky-300 to-blue-500">
                  CYCLONEX
                </span>
                <span className="text-[10px] uppercase font-bold tracking-widest px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800/60">
                  AI/ML
                </span>
              </div>
              <p className="text-[10px] text-slate-400 font-mono tracking-tight hidden sm:block">
                TROPICAL CYCLONE INTELLIGENCE PLATFORM
              </p>
            </div>
          </Link>

          {/* Nav Links */}
          <nav className="hidden md:flex items-center space-x-1 lg:space-x-2">
            {navLinks.map((link) => {
              const Icon = link.icon;
              const isActive = pathname === link.href;
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? "bg-cyan-950/80 text-cyan-300 border border-cyan-800/60 shadow-sm shadow-cyan-500/10"
                      : "text-slate-300 hover:text-white hover:bg-slate-800/60"
                  }`}
                >
                  <Icon className={`h-4 w-4 ${isActive ? 'text-cyan-400' : 'text-slate-400'}`} />
                  <span>{link.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>
      </div>
    </header>
  );
}
