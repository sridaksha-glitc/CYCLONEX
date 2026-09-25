"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { Wind, Search, Filter, ArrowUpRight, Compass, ShieldAlert, History } from "lucide-react";
import { fetchCyclones, CycloneItem } from "@/lib/api";

export default function CyclonesListPage() {
  const [cyclones, setCyclones] = useState<CycloneItem[]>([]);
  const [filterStatus, setFilterStatus] = useState<string>("ALL");
  const [search, setSearch] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchCyclones();
        setCyclones(data.cyclones || []);
      } catch (err) {
        console.error("Using offline mock:", err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filtered = cyclones.filter((c) => {
    const matchesStatus = filterStatus === "ALL" || c.status === filterStatus;
    const matchesSearch = c.name.toLowerCase().includes(search.toLowerCase()) || 
                          c.code.toLowerCase().includes(search.toLowerCase()) ||
                          c.classification.toLowerCase().includes(search.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="inline-flex items-center gap-2 text-xs font-mono text-cyan-400 mb-1">
            <Wind className="h-4 w-4" />
            <span>AUTHORITATIVE BASIN ARCHIVE & ACTIVE CELLS</span>
          </div>
          <h1 className="text-3xl font-black text-white">Tropical Cyclone Registry</h1>
          <p className="text-slate-400 text-sm mt-1">
            Real-time tracking of active cyclogenesis disturbances and benchmark historical storms across North Indian Ocean & Arabian Sea.
          </p>
        </div>

        {/* Search & Filter Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="h-4 w-4 text-slate-500 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search storm or code..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-cyan-500 transition-colors w-52"
            />
          </div>

          <div className="flex rounded-xl bg-slate-900 border border-slate-800 p-1 text-xs">
            {["ALL", "ACTIVE", "ARCHIVED"].map((tab) => (
              <button
                key={tab}
                onClick={() => setFilterStatus(tab)}
                className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                  filterStatus === tab
                    ? "bg-cyan-500 text-slate-950 font-bold"
                    : "text-slate-400 hover:text-white"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Cyclones Table */}
      <div className="glass-panel rounded-2xl border border-slate-800 overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900/90 border-b border-slate-800 text-slate-400 font-mono uppercase tracking-wider">
              <tr>
                <th className="py-3.5 px-4">Cyclone Code & Name</th>
                <th className="py-3.5 px-4">Basin</th>
                <th className="py-3.5 px-4">IMD Category</th>
                <th className="py-3.5 px-4">Winds (kts / km/h)</th>
                <th className="py-3.5 px-4">Pressure</th>
                <th className="py-3.5 px-4">Coordinates</th>
                <th className="py-3.5 px-4">Prototype Risk</th>
                <th className="py-3.5 px-4">Status & Provenance</th>
                <th className="py-3.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {filtered.map((c) => {
                const isExtreme = c.risk_level === "EXTREME";
                const isHigh = c.risk_level === "HIGH";
                const riskBadgeColor = isExtreme
                  ? "bg-rose-950 text-rose-300 border-rose-800"
                  : isHigh
                  ? "bg-amber-950 text-amber-300 border-amber-800"
                  : "bg-cyan-950 text-cyan-300 border-cyan-800";

                return (
                  <tr key={c.id} className="hover:bg-slate-900/50 transition-colors">
                    <td className="py-4 px-4 font-sans">
                      <div className="font-bold text-white text-sm">{c.name}</div>
                      <div className="text-[11px] font-mono text-cyan-400">{c.code}</div>
                    </td>
                    <td className="py-4 px-4 text-slate-300 font-sans">{c.basin}</td>
                    <td className="py-4 px-4 font-sans">
                      <span className="font-semibold text-slate-200">{c.classification}</span>
                    </td>
                    <td className="py-4 px-4 text-slate-200">
                      <strong>{c.max_sustained_wind_kts} kts</strong>{" "}
                      <span className="text-slate-500">({Math.round(c.max_sustained_wind_kts * 1.852)} km/h)</span>
                    </td>
                    <td className="py-4 px-4 text-slate-300">{c.central_pressure_hpa} hPa</td>
                    <td className="py-4 px-4 text-slate-400">
                      {c.current_lat}°N, {c.current_lon}°E
                    </td>
                    <td className="py-4 px-4">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${riskBadgeColor}`}>
                        {c.risk_level} ({c.risk_score})
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-1.5">
                        <span className={`h-2 w-2 rounded-full ${c.status === "ACTIVE" ? "bg-emerald-400 animate-ping" : "bg-slate-500"}`}></span>
                        <span className="text-[11px] text-slate-300 font-bold">{c.status}</span>
                      </div>
                      <span className="text-[10px] text-slate-500 block">{c.data_mode} DATA</span>
                    </td>
                    <td className="py-4 px-4 text-right">
                      <Link
                        href={`/cyclones/${c.code}`}
                        className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-cyan-600 text-slate-200 hover:text-white transition-all text-xs font-sans font-semibold"
                      >
                        <span>Telemetry</span>
                        <ArrowUpRight className="h-3.5 w-3.5" />
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
