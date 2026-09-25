"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { 
  Wind, 
  Gauge, 
  ShieldAlert, 
  AlertTriangle, 
  Activity, 
  Eye, 
  Compass, 
  ArrowUpRight, 
  Play, 
  CheckCircle2,
  RefreshCw,
  Cpu
} from "lucide-react";
import { CycloneMap } from "@/components/CycloneMap";

export default function DashboardPage() {
  const [cyclones, setCyclones] = useState<any[]>([]);
  const [selectedCyclone, setSelectedCyclone] = useState<any>(null);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<any>(null);

  // Load initial active storms and alerts from backend (or fallback)
  useEffect(() => {
    async function loadData() {
      try {
        const [cycRes, alertRes] = await Promise.all([
          fetch("http://localhost:8000/api/v1/cyclones"),
          fetch("http://localhost:8000/api/v1/alerts")
        ]);

        if (cycRes.ok) {
          const cycData = await cycRes.json();
          setCyclones(cycData.cyclones || []);
          if (cycData.cyclones?.length > 0) {
            setSelectedCyclone(cycData.cyclones[0]);
          }
        }
        if (alertRes.ok) {
          const alData = await alertRes.json();
          setAlerts(alData.alerts || []);
        }
      } catch (err) {
        console.warn("Could not reach backend, using offline baseline:", err);
        // Offline benchmark data
        const fallback = [
          {
            id: "a1b2c3d4-e5f6-7890-abcd-ef1234567801",
            code: "BOB-01-2024",
            name: "Cyclone Remal",
            basin: "Bay of Bengal",
            status: "ACTIVE",
            classification: "Severe Cyclonic Storm",
            current_lat: 21.4,
            current_lon: 89.2,
            max_sustained_wind_kts: 60.0,
            central_pressure_hpa: 978.0,
            movement_speed_kmh: 16.0,
            movement_direction_deg: 355.0,
            risk_level: "HIGH",
            risk_score: 78,
            data_mode: "HISTORICAL"
          },
          {
            id: "a1b2c3d4-e5f6-7890-abcd-ef1234567804",
            code: "INVEST-91B",
            name: "Invest 91B (Early Stage)",
            basin: "Bay of Bengal",
            status: "ACTIVE",
            classification: "Deep Depression",
            current_lat: 12.8,
            current_lon: 85.4,
            max_sustained_wind_kts: 30.0,
            central_pressure_hpa: 998.0,
            movement_speed_kmh: 18.0,
            movement_direction_deg: 315.0,
            risk_level: "MODERATE",
            risk_score: 46,
            data_mode: "DEMO"
          }
        ];
        setCyclones(fallback);
        setSelectedCyclone(fallback[0]);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const triggerInstantAnalysis = async () => {
    if (!selectedCyclone) return;
    setAnalyzing(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          latitude: selectedCyclone.current_lat,
          longitude: selectedCyclone.current_lon,
          pressure: selectedCyclone.central_pressure_hpa,
          wind_speed: selectedCyclone.max_sustained_wind_kts * 1.852,
          cyclone_name: selectedCyclone.name
        })
      });
      if (res.ok) {
        const data = await res.json();
        setAnalysisResult(data);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setAnalyzing(false);
    }
  };

  const mapStormPoints = cyclones.map((c) => ({
    id: c.id,
    name: c.name,
    code: c.code,
    lat: c.current_lat,
    lon: c.current_lon,
    wind_kts: c.max_sustained_wind_kts,
    pressure: c.central_pressure_hpa,
    category: c.classification,
    risk_level: c.risk_level,
    risk_score: c.risk_score,
    status: c.status,
    data_mode: c.data_mode
  }));

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Hero / Strategic Alert Bar */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950 p-6 sm:p-8 border border-slate-800 shadow-2xl">
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none"></div>

        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-3xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-950 border border-cyan-700/60 text-cyan-300 text-xs font-mono font-medium">
              <Activity className="h-3.5 w-3.5 text-cyan-400 animate-pulse" />
              <span>EARLY CYCLONIC RISK ASSESSMENT ENGINE</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-black tracking-tight text-white">
              Multi-Source AI Cyclone Intelligence
            </h1>
            <p className="text-slate-300 text-sm leading-relaxed">
              Fusing INSAT-3D satellite infrared vision, in-situ OpenWeather surface telemetry, and authoritative IBTrACS climatology to detect, classify, and forecast tropical cyclone trajectories in the North Indian Ocean basin.
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <Link
              href="/analysis"
              className="px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-sm transition-all shadow-lg shadow-cyan-500/25 flex items-center gap-2"
            >
              <Cpu className="h-4 w-4" />
              <span>Launch AI Fusion Workbench</span>
            </Link>
            <Link
              href="/alerts"
              className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 font-semibold text-sm transition-all flex items-center gap-2"
            >
              <ShieldAlert className="h-4 w-4 text-amber-400" />
              <span>View Alert Center</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Top Telemetry KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* KPI 1 */}
        <div className="glass-panel p-5 rounded-xl border border-slate-800 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400">ACTIVE TRACK CELLS</span>
            <Wind className="h-5 w-5 text-cyan-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-black text-white">{cyclones.filter(c => c.status === "ACTIVE").length}</span>
            <span className="text-xs font-semibold text-emerald-400">Monitored</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500">Bay of Bengal & Arabian Sea basins</p>
        </div>

        {/* KPI 2 */}
        <div className="glass-panel p-5 rounded-xl border border-slate-800 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400">HIGHEST PROTOTYPE RISK</span>
            <Gauge className="h-5 w-5 text-rose-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-black text-rose-400">78</span>
            <span className="text-xs font-bold text-rose-400 px-2 py-0.5 rounded bg-rose-950/80 border border-rose-800">
              HIGH RISK
            </span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500">Cyclone Remal (Coastal Landfall Vector)</p>
        </div>

        {/* KPI 3 */}
        <div className="glass-panel p-5 rounded-xl border border-slate-800 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400">PEAK SUSTAINED WINDS</span>
            <Wind className="h-5 w-5 text-amber-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-black text-amber-300">60 kts</span>
            <span className="text-xs font-mono text-slate-400">(111 km/h)</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500">Classification: Severe Cyclonic Storm</p>
        </div>

        {/* KPI 4 */}
        <div className="glass-panel p-5 rounded-xl border border-slate-800 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400">AI INFERENCE ENGINE</span>
            <CheckCircle2 className="h-5 w-5 text-emerald-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-black text-emerald-400">v1.0-fusion</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500">Models A, B, C + XAI Feature Attribution</p>
        </div>
      </div>

      {/* Main Command-Center Grid: Interactive Map + Telemetry Dashboard */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Cols: Interactive Geospatial Tracking Map */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Compass className="h-5 w-5 text-cyan-400" />
              <h2 className="text-lg font-bold text-white tracking-wide">
                Geospatial Cyclone Tracking & Forecast Cone
              </h2>
            </div>
            <div className="text-xs font-mono text-slate-400">
              CLICK ANY STORM TO INSPECT
            </div>
          </div>

          <CycloneMap
            cyclones={mapStormPoints}
            selectedCycloneId={selectedCyclone?.id}
            onSelectCyclone={(c) => {
              const full = cyclones.find((orig) => orig.id === c.id);
              if (full) setSelectedCyclone(full);
            }}
          />

          {/* Storm Selector Tabs */}
          <div className="flex gap-2 overflow-x-auto pb-1">
            {cyclones.map((c) => (
              <button
                key={c.id}
                onClick={() => setSelectedCyclone(c)}
                className={`px-4 py-2.5 rounded-xl text-left border transition-all min-w-[200px] ${
                  selectedCyclone?.id === c.id
                    ? "bg-slate-900 border-cyan-500 text-white shadow-lg shadow-cyan-500/10"
                    : "bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700"
                }`}
              >
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-cyan-400 font-bold">{c.code}</span>
                  <span className={`text-[10px] px-1.5 py-0.2 rounded font-bold ${
                    c.risk_level === "EXTREME" ? "text-rose-400 bg-rose-950" : "text-amber-400 bg-amber-950"
                  }`}>
                    {c.risk_level}
                  </span>
                </div>
                <div className="font-bold text-sm text-slate-200 mt-1">{c.name}</div>
                <div className="text-[11px] text-slate-400">{c.classification} • {c.max_sustained_wind_kts} kts</div>
              </button>
            ))}
          </div>
        </div>

        {/* Right 1 Col: Live Storm Inspector & Real-time AI Re-Analysis */}
        <div className="space-y-6">
          <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <span className="text-xs font-mono text-cyan-400 font-semibold">{selectedCyclone?.code}</span>
                <h3 className="text-xl font-black text-white">{selectedCyclone?.name}</h3>
              </div>
              <span className={`px-2.5 py-1 rounded-lg text-xs font-black tracking-wider ${
                selectedCyclone?.risk_level === "EXTREME"
                  ? "bg-rose-950 text-rose-400 border border-rose-800"
                  : selectedCyclone?.risk_level === "HIGH"
                  ? "bg-amber-950 text-amber-400 border border-amber-800"
                  : "bg-cyan-950 text-cyan-400 border border-cyan-800"
              }`}>
                {selectedCyclone?.risk_level} ({selectedCyclone?.risk_score}/100)
              </span>
            </div>

            {/* Meteorological Parameters */}
            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">IMD Classification</span>
                <strong className="text-cyan-300 font-sans">{selectedCyclone?.classification}</strong>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Max Sustained Winds</span>
                <strong className="text-white">{selectedCyclone?.max_sustained_wind_kts} kts ({Math.round(selectedCyclone?.max_sustained_wind_kts * 1.852)} km/h)</strong>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Central Barometric Pressure</span>
                <strong className="text-white">{selectedCyclone?.central_pressure_hpa} hPa</strong>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Present Coordinates</span>
                <strong className="text-slate-300">{selectedCyclone?.current_lat}°N, {selectedCyclone?.current_lon}°E</strong>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Forward Movement</span>
                <strong className="text-slate-300">{selectedCyclone?.movement_speed_kmh} km/h @ {selectedCyclone?.movement_direction_deg}°</strong>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-slate-400">Data Mode & Provenance</span>
                <span className="text-amber-400 font-bold">{selectedCyclone?.data_mode} DATA</span>
              </div>
            </div>

            {/* Run Fusion Inference Button */}
            <button
              onClick={triggerInstantAnalysis}
              disabled={analyzing}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold text-xs tracking-wider transition-all flex items-center justify-center gap-2 shadow-lg shadow-cyan-600/20 disabled:opacity-50"
            >
              {analyzing ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>EXECUTING MULTI-SOURCE FUSION...</span>
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  <span>RUN LIVE AI INFERENCE PIPELINE</span>
                </>
              )}
            </button>

            {/* Live Model Results Card if Analyzed */}
            {analysisResult && (
              <div className="mt-4 p-4 rounded-xl bg-slate-950 border border-cyan-800/60 space-y-3 animate-fadeIn">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-cyan-400 font-bold">LATEST INFERENCE RESULT</span>
                  <span className="text-slate-400">{analysisResult.model_version}</span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="bg-slate-900 p-2 rounded">
                    <span className="text-[10px] text-slate-500 block">DETECTION CONF</span>
                    <strong className="text-emerald-400">{Math.round(analysisResult.cyclone_probability * 100)}% Confirmed</strong>
                  </div>
                  <div className="bg-slate-900 p-2 rounded">
                    <span className="text-[10px] text-slate-500 block">12H PREDICTED WIND</span>
                    <strong className="text-amber-400">{analysisResult.predicted_wind_speed_kts} kts</strong>
                  </div>
                </div>

                {/* Explainable AI breakdown preview */}
                <div className="text-[11px] text-slate-300">
                  <span className="text-slate-400 block mb-1 font-mono">PRIMARY CONTRIBUTING FACTORS:</span>
                  <ul className="space-y-1">
                    {analysisResult.explanation?.slice(0, 2).map((exp: any, i: number) => (
                      <li key={i} className="flex items-start gap-1.5 text-slate-300">
                        <span className="text-cyan-400 font-bold">•</span>
                        <span><strong>{exp.feature}</strong>: {exp.description}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            )}
          </div>

          {/* Recent Automated Alerts Card */}
          <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-3">
            <div className="flex items-center justify-between border-b border-slate-800 pb-2">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-400" />
                <h4 className="text-sm font-bold text-white">Dispatched Alerts (n8n)</h4>
              </div>
              <Link href="/alerts" className="text-xs text-cyan-400 hover:underline">
                View All
              </Link>
            </div>

            <div className="space-y-2.5">
              {alerts.slice(0, 3).map((al, idx) => (
                <div key={idx} className="p-3 rounded-lg bg-slate-950/80 border border-slate-800/80 text-xs">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-bold text-amber-300">{al.title}</span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800">
                      {al.severity}
                    </span>
                  </div>
                  <p className="text-slate-400 text-[11px] line-clamp-2 leading-relaxed">{al.message}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
