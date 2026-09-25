"use client";

import { useState } from "react";
import { 
  Cpu, 
  Wind, 
  Gauge, 
  Compass, 
  ShieldAlert, 
  CheckCircle2, 
  AlertTriangle, 
  Upload, 
  RefreshCw, 
  Play,
  Activity,
  Layers,
  Sparkles,
  Info
} from "lucide-react";
import { 
  BENCHMARK_SCENARIOS, 
  BenchmarkScenario, 
  analyzeCyclone, 
  AnalyzeResponse, 
  AnalyzeRequest 
} from "@/lib/api";

export default function AnalysisWorkbenchPage() {
  const [activeScenarioId, setActiveScenarioId] = useState<string>("severe_storm");
  const [dataMode, setDataMode] = useState<"DEMO" | "HISTORICAL" | "LIVE">("HISTORICAL");

  const [lat, setLat] = useState<number>(21.4);
  const [lon, setLon] = useState<number>(89.2);
  const [temperature, setTemperature] = useState<number>(28.5);
  const [humidity, setHumidity] = useState<number>(86);
  const [pressure, setPressure] = useState<number>(978);
  const [windKts, setWindKts] = useState<number>(60);
  const [windDirection, setWindDirection] = useState<number>(355);
  const [stormName, setStormName] = useState<string>("Cyclone Remal");
  const [satelliteImage, setSatelliteImage] = useState<string | null>(null);
  const [forceLive, setForceLive] = useState<boolean>(false);

  const [loading, setLoading] = useState<boolean>(false);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleApplyScenario = (scenario: BenchmarkScenario) => {
    setActiveScenarioId(scenario.id);
    setDataMode(scenario.data_mode);
    setLat(scenario.payload.latitude);
    setLon(scenario.payload.longitude);
    setTemperature(scenario.payload.temperature ?? 28.5);
    setHumidity(scenario.payload.humidity ?? 80);
    setPressure(scenario.payload.pressure ?? 1000);
    setWindKts(scenario.payload.wind_speed_kts ?? 30);
    setWindDirection(scenario.payload.wind_direction ?? 340);
    setStormName(scenario.payload.cyclone_name ?? "Benchmark Storm");
  };

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setSatelliteImage(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleRunAnalysis = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const payload: AnalyzeRequest = {
        latitude: lat,
        longitude: lon,
        temperature,
        humidity,
        pressure,
        wind_speed_kts: windKts,
        wind_speed: Math.round(windKts * 1.852),
        wind_direction: windDirection,
        cyclone_name: stormName,
        satellite_image: satelliteImage,
        data_mode: dataMode,
        force_live_weather: forceLive
      };

      const data = await analyzeCyclone(payload);
      setResult(data);
    } catch (err: any) {
      console.error("Analysis invocation error:", err);
      setError(err.message || "Failed to complete AI multi-source inference.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Page Header */}
      <div className="border-b border-slate-800 pb-6">
        <div className="inline-flex items-center gap-2 text-xs font-mono text-cyan-400 mb-1">
          <Cpu className="h-4 w-4" />
          <span>MULTI-SOURCE INFERENCE & EXPLAINABLE RISK WORKBENCH</span>
        </div>
        <h1 className="text-3xl font-black text-white">AI Fusion Workbench</h1>
        <p className="text-slate-400 text-sm mt-1 max-w-3xl">
          Execute end-to-end multi-source inference across Model A (Detection), Model B (IMD Classification), and Model C (Prediction), with transparent Explainable AI attribution and Prototype Risk Index generation.
        </p>
      </div>

      {/* 5 Canonical Benchmark Scenario Chips */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-mono text-slate-400 uppercase tracking-wider block">
            Select Standard Benchmark Scenario (Phase 3 Deterministic Calibration):
          </span>
          <span className="text-xs font-mono text-cyan-400 font-bold">
            DATA MODE: {dataMode}
          </span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-2.5">
          {BENCHMARK_SCENARIOS.map((sc) => {
            const isSelected = activeScenarioId === sc.id;
            return (
              <button
                key={sc.id}
                type="button"
                onClick={() => handleApplyScenario(sc)}
                className={`p-3 rounded-xl border text-left transition-all ${
                  isSelected 
                    ? "bg-cyan-950/70 border-cyan-500 shadow-lg shadow-cyan-500/10 text-white" 
                    : "bg-slate-900/80 hover:bg-slate-850 border-slate-800 text-slate-300"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[11px] font-bold font-mono text-cyan-400">{sc.title}</span>
                  <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-400">
                    {sc.data_mode}
                  </span>
                </div>
                <div className="text-[11px] font-semibold text-white truncate">{sc.category}</div>
                <div className="text-[10px] text-slate-400 line-clamp-2 mt-1 leading-snug">
                  {sc.description}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Form (5 Cols) */}
        <div className="lg:col-span-5 space-y-6">
          <form onSubmit={handleRunAnalysis} className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-5 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Layers className="h-4 w-4 text-cyan-400" />
                <span>Observation & Sensor Inputs</span>
              </h2>
              <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
                {(["DEMO", "HISTORICAL", "LIVE"] as const).map((mode) => (
                  <button
                    key={mode}
                    type="button"
                    onClick={() => setDataMode(mode)}
                    className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold transition-all ${
                      dataMode === mode 
                        ? "bg-cyan-500 text-slate-950" 
                        : "text-slate-400 hover:text-white"
                    }`}
                  >
                    {mode}
                  </button>
                ))}
              </div>
            </div>

            {/* Storm Label */}
            <div>
              <label className="text-[11px] font-mono text-slate-400 block mb-1">Storm / System Name</label>
              <input
                type="text"
                value={stormName}
                onChange={(e) => setStormName(e.target.value)}
                className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-white focus:outline-none focus:border-cyan-500"
              />
            </div>

            {/* Coordinates */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-[11px] font-mono text-slate-400 block mb-1">Latitude (°N)</label>
                <input
                  type="number"
                  step="0.1"
                  required
                  value={lat}
                  onChange={(e) => setLat(parseFloat(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-white focus:outline-none focus:border-cyan-500"
                />
              </div>
              <div>
                <label className="text-[11px] font-mono text-slate-400 block mb-1">Longitude (°E)</label>
                <input
                  type="number"
                  step="0.1"
                  required
                  value={lon}
                  onChange={(e) => setLon(parseFloat(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-white focus:outline-none focus:border-cyan-500"
                />
              </div>
            </div>

            {/* Barometric Pressure & Winds */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-[11px] font-mono text-slate-400 block mb-1">Central Pressure (hPa)</label>
                <input
                  type="number"
                  step="1"
                  required
                  value={pressure}
                  onChange={(e) => setPressure(parseFloat(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-white focus:outline-none focus:border-cyan-500"
                />
              </div>
              <div>
                <label className="text-[11px] font-mono text-slate-400 block mb-1">Sustained Wind (knots)</label>
                <input
                  type="number"
                  step="1"
                  required
                  value={windKts}
                  onChange={(e) => setWindKts(parseFloat(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-white focus:outline-none focus:border-cyan-500"
                />
                <span className="text-[10px] text-slate-500 font-mono mt-0.5 block">
                  ~{(windKts * 1.852).toFixed(1)} km/h
                </span>
              </div>
            </div>

            {/* Temp, Humidity & Heading */}
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="text-[11px] font-mono text-slate-400 block mb-1">SST (°C)</label>
                <input
                  type="number"
                  step="0.1"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-white focus:outline-none focus:border-cyan-500"
                />
              </div>
              <div>
                <label className="text-[11px] font-mono text-slate-400 block mb-1">Humidity (%)</label>
                <input
                  type="number"
                  step="1"
                  value={humidity}
                  onChange={(e) => setHumidity(parseFloat(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-white focus:outline-none focus:border-cyan-500"
                />
              </div>
              <div>
                <label className="text-[11px] font-mono text-slate-400 block mb-1">Direction (°)</label>
                <input
                  type="number"
                  step="5"
                  value={windDirection}
                  onChange={(e) => setWindDirection(parseFloat(e.target.value))}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-white focus:outline-none focus:border-cyan-500"
                />
              </div>
            </div>

            {/* Satellite Image Upload */}
            <div className="space-y-1.5">
              <label className="text-[11px] font-mono text-slate-400 block">
                Satellite Infrared / Visible Imagery (Optional)
              </label>
              <div className="border-2 border-dashed border-slate-800 hover:border-cyan-500/50 rounded-xl p-4 text-center transition-colors">
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="hidden"
                  id="satellite-upload"
                />
                <label htmlFor="satellite-upload" className="cursor-pointer space-y-1 block">
                  <Upload className="h-5 w-5 text-slate-400 mx-auto" />
                  <span className="text-xs text-cyan-400 font-semibold block">Upload Satellite IR Tile</span>
                  <span className="text-[10px] text-slate-500 block">PNG, JPEG, WebP up to 5MB</span>
                </label>
                {satelliteImage && (
                  <div className="mt-2 text-[11px] text-emerald-400 font-mono">
                    ✓ Image loaded for Model A feature extraction
                  </div>
                )}
              </div>
            </div>

            {/* Live Weather Toggle */}
            <div className="flex items-center gap-2 pt-2 border-t border-slate-800/80">
              <input
                type="checkbox"
                id="forceLive"
                checked={forceLive}
                onChange={(e) => setForceLive(e.target.checked)}
                className="rounded border-slate-700 bg-slate-900 text-cyan-500 focus:ring-0"
              />
              <label htmlFor="forceLive" className="text-xs text-slate-300">
                Attempt Live OpenWeather API lookup for coordinates
              </label>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-black text-xs tracking-wider uppercase transition-all shadow-lg shadow-cyan-500/20 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin text-slate-950" />
                  <span>Computing Multi-Source Fusion...</span>
                </>
              ) : (
                <>
                  <Play className="h-4 w-4 text-slate-950" />
                  <span>RUN AI ANALYSIS</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right Output Dashboard (7 Cols) */}
        <div className="lg:col-span-7 space-y-6">
          {error && (
            <div className="p-4 rounded-xl bg-rose-950/50 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {!result && !loading && (
            <div className="glass-panel p-12 rounded-2xl border border-slate-800 text-center space-y-3">
              <Cpu className="h-10 w-10 text-slate-600 mx-auto animate-pulse" />
              <h3 className="text-lg font-bold text-white">Inference Engine Ready</h3>
              <p className="text-slate-400 text-xs max-w-md mx-auto leading-relaxed">
                Configure coordinates and atmospheric observations on the left or select a preset scenario, then click <strong>RUN AI ANALYSIS</strong> to execute live inference.
              </p>
            </div>
          )}

          {result && (
            <div className="space-y-6 animate-fadeIn">
              {/* Top Result Banner */}
              <div className="glass-panel p-6 rounded-2xl border border-cyan-800/60 shadow-2xl relative overflow-hidden">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
                  <div>
                    <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-widest block">
                      MODEL INFERENCE RESULT ({result.model_version})
                    </span>
                    <h3 className="text-2xl font-black text-white mt-0.5">{result.classification}</h3>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className={`px-3 py-1.5 rounded-xl text-xs font-black border tracking-wider ${
                      result.risk_level === "EXTREME"
                        ? "bg-rose-950 text-rose-300 border-rose-800"
                        : result.risk_level === "HIGH"
                        ? "bg-amber-950 text-amber-300 border-amber-800"
                        : "bg-cyan-950 text-cyan-300 border-cyan-800"
                    }`}>
                      {result.risk_level} RISK ({result.risk_score}/100)
                    </span>
                    <span className="px-2.5 py-1.5 rounded-xl text-xs font-mono font-bold bg-slate-900 text-slate-300 border border-slate-800">
                      {result.data_mode} MODE
                    </span>
                  </div>
                </div>

                {/* 3 Model Summaries */}
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-4 text-xs font-mono">
                  <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80">
                    <span className="text-[10px] text-slate-500 block uppercase">MODEL A: DETECTION</span>
                    <strong className={result.cyclone_detected ? "text-emerald-400 text-sm" : "text-slate-400 text-sm"}>
                      {result.cyclone_detected ? "DETECTED" : "NO SYSTEM"}
                    </strong>
                    <div className="text-[10px] text-slate-400 mt-1">{(result.cyclone_probability * 100).toFixed(1)}% Probability</div>
                  </div>

                  <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80">
                    <span className="text-[10px] text-slate-500 block uppercase">MODEL B: CONFIDENCE</span>
                    <strong className="text-cyan-300 text-sm">{(result.classification_confidence * 100).toFixed(0)}%</strong>
                    <div className="text-[10px] text-slate-400 mt-1">IMD Standards Tier {result.classification_tier}</div>
                  </div>

                  <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80">
                    <span className="text-[10px] text-slate-500 block uppercase">MODEL C: 12H FORECAST</span>
                    <strong className="text-amber-300 text-sm">{result.predicted_wind_speed_kts} kts</strong>
                    <div className="text-[10px] text-slate-400 mt-1">Trend: {result.trend}</div>
                  </div>
                </div>
              </div>

              {/* Decoupled Prototype Risk Index Breakdown */}
              <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-2">
                    <ShieldAlert className="h-5 w-5 text-amber-400" />
                    <h3 className="text-base font-bold text-white">Prototype Risk Index (PRI: {result.risk_score}/100)</h3>
                  </div>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-400 border border-slate-800">
                    HEURISTIC MODEL
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {result.risk?.contributing_factors?.map((f, idx) => (
                    <div key={idx} className="p-3 bg-slate-950/70 border border-slate-800/80 rounded-xl space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-semibold text-slate-300">{f.factor}</span>
                        <span className="font-mono font-bold text-cyan-400">{f.score.toFixed(1)} / {f.max_score}</span>
                      </div>
                      <div className="text-[11px] font-mono text-slate-400">{f.metric}</div>
                      <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden mt-1">
                        <div 
                          className="h-full bg-amber-500 rounded-full"
                          style={{ width: `${Math.min(100, Math.round((f.score / f.max_score) * 100))}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>

                <div className="p-3 rounded-xl bg-amber-950/20 border border-amber-800/30 text-[11px] text-amber-300/90 flex items-start gap-2">
                  <Info className="h-4 w-4 shrink-0 mt-0.5 text-amber-400" />
                  <p>{result.risk?.disclaimer || result.disclaimer}</p>
                </div>
              </div>

              {/* Explainable AI: Feature Contributions */}
              <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <div className="flex items-center gap-2">
                    <Activity className="h-5 w-5 text-cyan-400" />
                    <h3 className="text-base font-bold text-white">Explainable AI: Key Feature Contributions</h3>
                  </div>
                  <span className="text-[11px] font-mono text-slate-400">SHAP / GRADIENT ATTRIBUTION</span>
                </div>

                <div className="space-y-3">
                  {result.explanation?.map((item, idx) => {
                    const isEscalating = item.impact === "ESCALATING";
                    const isMitigating = item.impact === "MITIGATING";
                    const badgeColor = isEscalating
                      ? "bg-rose-950 text-rose-300 border-rose-800"
                      : isMitigating
                      ? "bg-emerald-950 text-emerald-300 border-emerald-800"
                      : "bg-slate-900 text-slate-300 border-slate-800";

                    return (
                      <div key={idx} className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800/80 space-y-1.5">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-white text-xs">{item.feature}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-mono text-slate-400">{item.value}</span>
                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${badgeColor}`}>
                              {item.impact}
                            </span>
                          </div>
                        </div>

                        {/* Importance progress bar */}
                        <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${isEscalating ? "bg-rose-500" : isMitigating ? "bg-emerald-500" : "bg-cyan-500"}`}
                            style={{ width: `${Math.round(item.importance * 100)}%` }}
                          ></div>
                        </div>

                        <p className="text-[11px] text-slate-400 leading-relaxed font-sans">{item.description}</p>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Multi-Horizon Trajectory Table */}
              <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-3">
                <h4 className="text-sm font-bold text-white">Multi-Horizon Model C Trajectory Forecast (+6h, +12h, +24h)</h4>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800">
                      <tr>
                        <th className="py-2 px-3">Lead Time</th>
                        <th className="py-2 px-3">Position</th>
                        <th className="py-2 px-3">Sustained Wind</th>
                        <th className="py-2 px-3">Central Pressure</th>
                        <th className="py-2 px-3">Category</th>
                        <th className="py-2 px-3">Trend</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {(result.multi_horizon_forecast || result.multi_horizon_predictions)?.map((m, idx) => (
                        <tr key={idx}>
                          <td className="py-2.5 px-3 font-bold text-cyan-400">+{m.lead_time_hours} Hours</td>
                          <td className="py-2.5 px-3 text-slate-300">{m.predicted_latitude}°N, {m.predicted_longitude}°E</td>
                          <td className="py-2.5 px-3 text-amber-300 font-bold">{m.predicted_wind_speed_kts} kts</td>
                          <td className="py-2.5 px-3 text-slate-200">{m.predicted_pressure_hpa} hPa</td>
                          <td className="py-2.5 px-3 text-cyan-300">{m.classification}</td>
                          <td className="py-2.5 px-3 text-slate-300">{m.trend}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Data Provenance & Transparency */}
              <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-slate-400 space-y-1">
                <div className="flex items-center gap-1.5 font-bold text-slate-300">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                  <span>Data Provenance Attribution</span>
                </div>
                <div>Sources: {(result.sources || result.data_sources)?.join(" • ")}</div>
                <div className="text-slate-500 font-mono text-[10px] pt-1">
                  DISCLAIMER: {result.disclaimer}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
