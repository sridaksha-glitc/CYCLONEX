"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { 
  Wind, 
  Gauge, 
  ShieldAlert, 
  AlertTriangle, 
  Activity, 
  Compass, 
  Play, 
  CheckCircle2,
  RefreshCw,
  Cpu,
  Info,
  Sparkles
} from "lucide-react";
import { CycloneMap } from "@/components/CycloneMap";
import { 
  fetchCyclones, 
  fetchAlerts, 
  analyzeCyclone, 
  runDemoAnalysis,
  CycloneItem, 
  AlertItem, 
  AnalyzeResponse 
} from "@/lib/api";

export default function DashboardPage() {
  const [cyclones, setCyclones] = useState<CycloneItem[]>([]);
  const [selectedCyclone, setSelectedCyclone] = useState<CycloneItem | null>(null);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalyzeResponse | null>(null);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string>("");

  useEffect(() => {
    async function loadData() {
      try {
        const [cycData, alertData] = await Promise.all([
          fetchCyclones(),
          fetchAlerts()
        ]);
        setCyclones(cycData.cyclones || []);
        if (cycData.cyclones?.length > 0) {
          setSelectedCyclone(cycData.cyclones[0]);
        }
        setAlerts(alertData.alerts || []);
        setLastUpdated(new Date().toLocaleTimeString());
      } catch (err) {
        console.warn("Could not reach backend API, using initial benchmark store:", err);
        const fallback: CycloneItem[] = [
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
            data_mode: "HISTORICAL",
            started_at: "2024-05-24T12:00:00Z",
            last_updated_at: "2024-05-26T18:00:00Z"
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
            data_mode: "DEMO",
            started_at: "2026-09-25T12:00:00Z",
            last_updated_at: "2026-09-25T12:00:00Z"
          }
        ];
        setCyclones(fallback);
        setSelectedCyclone(fallback[0]);
        setLastUpdated(new Date().toLocaleTimeString());
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const triggerInstantAnalysis = async () => {
    if (!selectedCyclone) return;
    setAnalyzing(true);
    setAnalysisError(null);
    try {
      const data = await analyzeCyclone({
        latitude: selectedCyclone.current_lat,
        longitude: selectedCyclone.current_lon,
        pressure: selectedCyclone.central_pressure_hpa,
        wind_speed_kts: selectedCyclone.max_sustained_wind_kts,
        wind_speed: Math.round(selectedCyclone.max_sustained_wind_kts * 1.852),
        wind_direction: selectedCyclone.movement_direction_deg,
        cyclone_name: selectedCyclone.name,
        cyclone_id: selectedCyclone.id,
        data_mode: selectedCyclone.data_mode
      });
      setAnalysisResult(data);
    } catch (e: unknown) {
      console.error("Instant analysis failed:", e);
      setAnalysisResult(null); // Clear fake/stale values per rule 11
      const msg = e instanceof Error ? e.message : "Instant analysis failed. Ensure backend API is reachable.";
      setAnalysisError(msg);
    } finally {
      setAnalyzing(false);
    }
  };

  const triggerVerifiedDemoAnalysis = async () => {
    setAnalyzing(true);
    setAnalysisError(null);
    try {
      const data = await runDemoAnalysis();
      setAnalysisResult(data);
    } catch (e: unknown) {
      console.error("Verified demo analysis failed:", e);
      setAnalysisResult(null); // Clear fake/stale values per rule 11
      const msg = e instanceof Error ? e.message : "Verified demo analysis failed. Ensure backend API is reachable.";
      setAnalysisError(msg);
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

  const activeCount = cyclones.filter(c => c.status === "ACTIVE").length;
  const highRiskCount = cyclones.filter(c => c.risk_score >= 60).length;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Hero / Strategic Alert Bar */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950 p-6 sm:p-8 border border-slate-800 shadow-2xl">
        <div className="absolute top-0 right-0 -mt-12 -mr-12 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none"></div>

        <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-2 max-w-3xl">
            <div className="flex flex-wrap items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-950 border border-cyan-700/60 text-cyan-300 text-xs font-mono font-medium">
                <Activity className="h-3.5 w-3.5 text-cyan-400 animate-pulse" />
                <span>AI/ML TROPICAL CYCLONE INTELLIGENCE</span>
              </span>
              <span className="px-2.5 py-0.5 rounded-full bg-slate-950 border border-slate-800 text-slate-400 text-[11px] font-mono">
                System Status: <strong className="text-emerald-400">{loading ? "SYNCING..." : "ONLINE"}</strong>
              </span>
              {lastUpdated && (
                <span className="px-2.5 py-0.5 rounded-full bg-slate-950 border border-slate-800 text-slate-400 text-[11px] font-mono">
                  Sync: {lastUpdated}
                </span>
              )}
            </div>
            <h1 className="text-3xl sm:text-4xl font-black tracking-tight text-white">
              CYCLONEX Command Center
            </h1>
            <p className="text-slate-300 text-sm leading-relaxed">
              Multi-source AI platform fusing INSAT-3D satellite infrared vision, OpenWeather surface meteorology, and authoritative NOAA IBTrACS climatology for real-time identification, IMD classification, trajectory prediction, and early risk assessment.
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
              <span>Alert Center ({alerts.length})</span>
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
            <span className="text-3xl font-black text-white">{activeCount}</span>
            <span className="text-xs font-semibold text-emerald-400">Monitored</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500">Bay of Bengal & Arabian Sea basins</p>
        </div>

        {/* KPI 2 */}
        <div className="glass-panel p-5 rounded-xl border border-slate-800 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400">HIGH-RISK SYSTEMS</span>
            <Gauge className="h-5 w-5 text-rose-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-black text-rose-400">{highRiskCount}</span>
            <span className="text-xs font-bold text-rose-400 px-2 py-0.5 rounded bg-rose-950/80 border border-rose-800">
              PRI &ge; 60
            </span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500">Systems crossing emergency threshold</p>
        </div>

        {/* KPI 3 */}
        <div className="glass-panel p-5 rounded-xl border border-slate-800 relative overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-slate-400">PEAK SUSTAINED WINDS</span>
            <Wind className="h-5 w-5 text-amber-400" />
          </div>
          <div className="mt-2 flex items-baseline gap-2">
            <span className="text-3xl font-black text-amber-300">
              {selectedCyclone ? `${selectedCyclone.max_sustained_wind_kts} kts` : "--"}
            </span>
            <span className="text-xs font-mono text-slate-400">
              ({selectedCyclone ? Math.round(selectedCyclone.max_sustained_wind_kts * 1.852) : 0} km/h)
            </span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500 truncate">{selectedCyclone?.classification || "Active Vortex"}</p>
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
                <strong className="text-white">
                  {selectedCyclone?.max_sustained_wind_kts} kts ({selectedCyclone ? Math.round(selectedCyclone.max_sustained_wind_kts * 1.852) : 0} km/h)
                </strong>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Central Pressure</span>
                <strong className="text-white">{selectedCyclone?.central_pressure_hpa} hPa</strong>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Coordinates</span>
                <strong className="text-slate-300">{selectedCyclone?.current_lat}°N, {selectedCyclone?.current_lon}°E</strong>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/60">
                <span className="text-slate-400">Movement Vector</span>
                <strong className="text-slate-300">{selectedCyclone?.movement_speed_kmh} km/h @ {selectedCyclone?.movement_direction_deg}°</strong>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-slate-400">Data Mode</span>
                <span className="text-amber-400 font-bold">{selectedCyclone?.data_mode} DATA</span>
              </div>
            </div>

            {/* Run Fusion Inference Buttons */}
            <div className="space-y-2 pt-1">
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

              <button
                onClick={triggerVerifiedDemoAnalysis}
                disabled={analyzing}
                className="w-full py-2.5 rounded-xl bg-slate-900 hover:bg-slate-850 border border-cyan-800/80 hover:border-cyan-600 text-cyan-300 font-bold text-xs tracking-wider transition-all flex items-center justify-center gap-2 shadow disabled:opacity-50"
              >
                <Sparkles className="h-3.5 w-3.5 text-cyan-400" />
                <span>RUN VERIFIED DEMO ANALYSIS (REMAL)</span>
              </button>
            </div>

            {/* Error state display if API fails */}
            {analysisError && (
              <div className="mt-3 p-3.5 rounded-xl bg-rose-950/70 border border-rose-800 text-rose-300 text-xs flex items-center gap-2 animate-fadeIn">
                <AlertTriangle className="h-4 w-4 shrink-0 text-rose-400" />
                <span>{analysisError}</span>
              </div>
            )}

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

                {/* Trajectory progression */}
                <div className="space-y-1.5 pt-1 border-t border-slate-800">
                  <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">
                    Model C Multi-Horizon Forecast:
                  </span>
                  <div className="grid grid-cols-3 gap-1 text-center font-mono text-[10px]">
                    {(analysisResult.multi_horizon_forecast || analysisResult.multi_horizon_predictions)?.map((h, i) => (
                      <div key={i} className="p-1.5 bg-slate-900/90 rounded border border-slate-800">
                        <div className="text-cyan-400 font-bold">+{h.lead_time_hours}h</div>
                        <div className="text-white">{h.predicted_wind_speed_kts} kts</div>
                        <div className="text-slate-400">{h.predicted_pressure_hpa} hPa</div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Explainable AI breakdown preview */}
                <div className="text-[11px] text-slate-300 pt-1 border-t border-slate-800">
                  <span className="text-slate-400 block mb-1 font-mono">PRIMARY XAI ATTRIBUTIONS:</span>
                  <ul className="space-y-1">
                    {analysisResult.explanation?.slice(0, 2).map((exp, i) => (
                      <li key={i} className="flex items-start gap-1.5 text-slate-300">
                        <span className="text-cyan-400 font-bold">•</span>
                        <span><strong>{exp.feature}</strong>: {exp.description}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Disclaimer */}
                <div className="p-2 rounded bg-amber-950/20 border border-amber-800/30 text-[10px] text-amber-300/80 flex items-start gap-1.5">
                  <Info className="h-3 w-3 shrink-0 mt-0.5 text-amber-400" />
                  <span>{analysisResult.risk?.disclaimer || analysisResult.disclaimer}</span>
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
