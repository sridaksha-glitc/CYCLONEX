"use client";

import { 
  Activity, 
  Layers, 
  Cpu, 
  CheckCircle2, 
  BarChart3, 
  ShieldCheck, 
  FileText,
  TrendingUp,
  BrainCircuit
} from "lucide-react";

export default function ModelsArchitecturePage() {
  const imdScale = [
    { name: "Low Pressure Area", abbr: "LPA", kts: "< 17 kts", kmh: "< 31 km/h", p_def: "< 1.0 hPa", impact: "Minor surface agitation, convective rain bands" },
    { name: "Depression", abbr: "D", kts: "17 – 27 kts", kmh: "31 – 49 km/h", p_def: "1.0 – 3.0 hPa", impact: "Squally winds, rough seas, fisherman warning" },
    { name: "Deep Depression", abbr: "DD", kts: "28 – 33 kts", kmh: "50 – 61 km/h", p_def: "3.0 – 4.5 hPa", impact: "Well-formed vortex, coastal squalls" },
    { name: "Cyclonic Storm", abbr: "CS", kts: "34 – 47 kts", kmh: "62 – 88 km/h", p_def: "4.5 – 8.5 hPa", impact: "Gale force winds, thatched hut damage" },
    { name: "Severe Cyclonic Storm", abbr: "SCS", kts: "48 – 63 kts", kmh: "89 – 117 km/h", p_def: "8.5 – 15.0 hPa", impact: "Uprooting trees, power line disruption" },
    { name: "Very Severe Cyclonic Storm", abbr: "VSCS", kts: "64 – 89 kts", kmh: "118 – 166 km/h", p_def: "15.0 – 30.0 hPa", impact: "Extensive structural destruction, 1.5–3m surge" },
    { name: "Extremely Severe Cyclonic Storm", abbr: "ESCS", kts: "90 – 119 kts", kmh: "167 – 221 km/h", p_def: "30.0 – 60.0 hPa", impact: "Catastrophic damage, 3–6m storm surge" },
    { name: "Super Cyclonic Storm", abbr: "SuCS", kts: "≥ 120 kts", kmh: "≥ 222 km/h", p_def: "> 60.0 hPa", impact: "Total devastation, extreme coastal inundation" },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="border-b border-slate-800 pb-6">
        <div className="inline-flex items-center gap-2 text-xs font-mono text-cyan-400 mb-1">
          <BrainCircuit className="h-4 w-4" />
          <span>SCIENTIFIC SPECIFICATIONS & EXPLAINABLE AI ARCHITECTURE</span>
        </div>
        <h1 className="text-3xl font-black text-white">Model Architecture & Climatology</h1>
        <p className="text-slate-400 text-sm mt-1 max-w-3xl">
          Complete transparent documentation of CYCLONEX inference models, multi-source feature fusion layers, physical meteorological boundaries, and decision-support heuristics.
        </p>
      </div>

      {/* Model Cards (Model A, B, C) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Model A */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <span className="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-cyan-950 text-cyan-400 border border-cyan-800">
              MODEL A
            </span>
            <span className="text-xs font-mono text-slate-500">v1.0-cv</span>
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Cyclone Detection</h3>
            <p className="text-slate-400 text-xs mt-1 leading-relaxed">
              Lightweight computer vision feature extractor analyzing satellite IR (10.8µm) and visible spectral bands.
            </p>
          </div>
          <div className="space-y-1.5 text-xs font-mono text-slate-300">
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-500">Key Features:</span>
              <span>CDO symmetry, minimum core temp</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-500">Output:</span>
              <span className="text-cyan-400">cyclone_detected, probability</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Inference Latency:</span>
              <span className="text-emerald-400">~12ms</span>
            </div>
          </div>
        </div>

        {/* Model B */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <span className="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-950 text-blue-400 border border-blue-800">
              MODEL B
            </span>
            <span className="text-xs font-mono text-slate-500">v1.0-classifier</span>
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Cyclone Classification</h3>
            <p className="text-slate-400 text-xs mt-1 leading-relaxed">
              Multi-source calibrated classifier categorizing storms strictly into authoritative IMD/WMO standard categories.
            </p>
          </div>
          <div className="space-y-1.5 text-xs font-mono text-slate-300">
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-500">Physics Baseline:</span>
              <span>Atkinson-Holliday P_deficit(V)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-500">Output:</span>
              <span className="text-blue-400">8-Tier IMD Category, Conf</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Standards:</span>
              <span className="text-emerald-400">WMO / IMD RSMC</span>
            </div>
          </div>
        </div>

        {/* Model C */}
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
          <div className="flex items-center justify-between">
            <span className="px-2.5 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-950 text-amber-400 border border-amber-800">
              MODEL C
            </span>
            <span className="text-xs font-mono text-slate-500">v1.0-predictor</span>
          </div>
          <div>
            <h3 className="text-base font-bold text-white">Short-term Prediction</h3>
            <p className="text-slate-400 text-xs mt-1 leading-relaxed">
              Gradient-boosted regression baseline projecting 6h, 12h, and 24h intensity trajectory, pressure deficit, and movement.
            </p>
          </div>
          <div className="space-y-1.5 text-xs font-mono text-slate-300">
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-500">Lead Times:</span>
              <span>+6h, +12h, +24h horizons</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-800/60">
              <span className="text-slate-500">Outputs:</span>
              <span className="text-amber-400">Wind, Pressure, RI Flag</span>
            </div>
            <div className="flex justify-between py-1">
              <span className="text-slate-500">Rapid Intensification:</span>
              <span className="text-rose-400">ΔV ≥ 30 kts / 24h</span>
            </div>
          </div>
        </div>
      </div>

      {/* Authoritative IMD / WMO Classification Standard Table */}
      <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <ShieldCheck className="h-5 w-5 text-emerald-400" />
              <span>Authoritative IMD / WMO Tropical Cyclone Intensity Scale</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Strictly enforced in CYCLONEX Model B. No categories or wind thresholds are invented or altered.
            </p>
          </div>
          <span className="text-[11px] font-mono text-slate-400">NORTH INDIAN OCEAN BASIN</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-900/90 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-2.5 px-3">Classification</th>
                <th className="py-2.5 px-3">Abbr</th>
                <th className="py-2.5 px-3">Sustained Winds (kts)</th>
                <th className="py-2.5 px-3">Sustained Winds (km/h)</th>
                <th className="py-2.5 px-3">Central Deficit</th>
                <th className="py-2.5 px-3 font-sans">Typical Impact / Warning Tier</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {imdScale.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-900/50">
                  <td className="py-3 px-3 font-bold text-white font-sans">{row.name}</td>
                  <td className="py-3 px-3 text-cyan-400 font-bold">{row.abbr}</td>
                  <td className="py-3 px-3 text-amber-300">{row.kts}</td>
                  <td className="py-3 px-3 text-slate-300">{row.kmh}</td>
                  <td className="py-3 px-3 text-slate-400">{row.p_def}</td>
                  <td className="py-3 px-3 text-slate-400 font-sans">{row.impact}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Physics & Heuristics Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs leading-relaxed">
        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-2">
          <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
            <FileText className="h-4 w-4 text-cyan-400" />
            <span>Atkinson-Holliday Wind-Pressure Physics</span>
          </h3>
          <p className="text-slate-400">
            CYCLONEX grounds feature fusion in the empirical Atkinson-Holliday relationship:
          </p>
          <div className="p-3 bg-slate-950 rounded-xl font-mono text-cyan-300 border border-slate-800">
            V_max = 6.7 × (1010 - P_c)^0.644
          </div>
          <p className="text-slate-400 text-[11px]">
            This prevents inconsistent model predictions where low pressure and weak winds or high pressure and hurricane winds might otherwise co-occur statistically.
          </p>
        </div>

        <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-2">
          <h3 className="text-sm font-bold text-white font-mono flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-amber-400" />
            <span>Prototype Risk Index (PRI) Formula</span>
          </h3>
          <p className="text-slate-400">
            A transparent 0 to 100 decision-support score combining multiple hazard axes:
          </p>
          <div className="p-3 bg-slate-950 rounded-xl font-mono text-amber-300 border border-slate-800 text-[11px]">
            PRI = 0.45·WindHazard + 0.30·PressureDrop + 0.15·IntensificationTrend + 0.10·SatelliteCoherence
          </div>
          <p className="text-slate-500 text-[11px]">
            <strong>DISCLAIMER:</strong> This is a project-specific decision-support index, NOT an official cyclone warning from IMD or WMO.
          </p>
        </div>
      </div>
    </div>
  );
}
