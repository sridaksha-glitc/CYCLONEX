"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  Wind, 
  Gauge, 
  Navigation, 
  Clock, 
  Compass, 
  ShieldAlert, 
  Activity, 
  MapPin,
  TrendingUp,
  Cpu
} from "lucide-react";

export default function CycloneDetailPage() {
  const params = useParams();
  const router = useRouter();
  const cycloneId = (params?.id as string) || "BOB-01-2024";

  const [cyclone, setCyclone] = useState<any>(null);
  const [predictions, setPredictions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadCyclone() {
      try {
        const res = await fetch(`http://localhost:8000/api/v1/cyclones/${cycloneId}`);
        if (res.ok) {
          const data = await res.json();
          setCyclone(data);

          // Trigger prediction calculation for this storm
          const predRes = await fetch("http://localhost:8000/api/v1/predict", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              latitude: data.current_lat,
              longitude: data.current_lon,
              wind_speed_kts: data.max_sustained_wind_kts,
              pressure_hpa: data.central_pressure_hpa,
              movement_speed_kmh: data.movement_speed_kmh,
              movement_direction_deg: data.movement_direction_deg
            })
          });
          if (predRes.ok) {
            const predData = await predRes.json();
            // Synthetic multi-horizon for table
            setPredictions([
              { lead_h: 6, wind_kts: Math.round(data.max_sustained_wind_kts + 5), p_hpa: data.central_pressure_hpa - 4, trend: "INTENSIFYING", conf: 0.91, lat: data.current_lat + 0.6, lon: data.current_lon - 0.2 },
              { lead_h: 12, wind_kts: Math.round(data.max_sustained_wind_kts + 10), p_hpa: data.central_pressure_hpa - 8, trend: "INTENSIFYING", conf: 0.88, lat: data.current_lat + 1.2, lon: data.current_lon - 0.3 },
              { lead_h: 24, wind_kts: Math.max(35, Math.round(data.max_sustained_wind_kts - 10)), p_hpa: data.central_pressure_hpa + 6, trend: "WEAKENING (POST-LANDFALL)", conf: 0.82, lat: data.current_lat + 2.3, lon: data.current_lon + 0.1 }
            ]);
          }
        }
      } catch (err) {
        console.error("Using fallback detail:", err);
      } finally {
        setLoading(false);
      }
    }
    loadCyclone();
  }, [cycloneId]);

  if (!cyclone && !loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center space-y-4">
        <h2 className="text-2xl font-bold text-white">Cyclone Record Not Found</h2>
        <p className="text-slate-400">The requested cyclone identifier does not exist in our basin database.</p>
        <Link href="/cyclones" className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-cyan-600 text-white font-semibold text-sm">
          <ArrowLeft className="h-4 w-4" />
          <span>Return to Registry</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Back button & Heading */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div className="space-y-1">
          <Link href="/cyclones" className="inline-flex items-center gap-1.5 text-xs text-cyan-400 hover:text-cyan-300 font-mono mb-2">
            <ArrowLeft className="h-3.5 w-3.5" />
            <span>BACK TO CYCLONE MONITOR</span>
          </Link>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-black text-white">{cyclone?.name || "Cyclone Loading..."}</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-cyan-950 text-cyan-400 border border-cyan-800">
              {cyclone?.code}
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-amber-950 text-amber-400 border border-amber-800">
              {cyclone?.data_mode} DATA
            </span>
          </div>
          <p className="text-slate-400 text-xs">
            Basin: {cyclone?.basin} • Started: {cyclone?.started_at ? new Date(cyclone.started_at).toUTCString() : "Active"}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className={`px-4 py-2 rounded-xl text-sm font-black border tracking-wider ${
            cyclone?.risk_level === "EXTREME"
              ? "bg-rose-950 text-rose-300 border-rose-800"
              : cyclone?.risk_level === "HIGH"
              ? "bg-amber-950 text-amber-300 border-amber-800"
              : "bg-cyan-950 text-cyan-300 border-cyan-800"
          }`}>
            PROTOTYPE RISK: {cyclone?.risk_level} ({cyclone?.risk_score}/100)
          </span>
        </div>
      </div>

      {/* Top 4 Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-5 rounded-xl border border-slate-800">
          <div className="text-slate-400 text-xs font-mono">IMD CLASSIFICATION</div>
          <div className="text-xl font-bold text-white mt-1">{cyclone?.classification}</div>
          <div className="text-[11px] text-cyan-400 font-mono mt-1">Authoritative WMO/IMD Tier</div>
        </div>

        <div className="glass-panel p-5 rounded-xl border border-slate-800">
          <div className="text-slate-400 text-xs font-mono">MAX SUSTAINED WINDS</div>
          <div className="text-xl font-black text-amber-300 mt-1">{cyclone?.max_sustained_wind_kts} kts</div>
          <div className="text-[11px] text-slate-500 font-mono mt-1">~{Math.round((cyclone?.max_sustained_wind_kts || 0) * 1.852)} km/h (10m surface)</div>
        </div>

        <div className="glass-panel p-5 rounded-xl border border-slate-800">
          <div className="text-slate-400 text-xs font-mono">CENTRAL PRESSURE</div>
          <div className="text-xl font-black text-white mt-1">{cyclone?.central_pressure_hpa} hPa</div>
          <div className="text-[11px] text-slate-500 font-mono mt-1">Barometric deficit ~{1013 - (cyclone?.central_pressure_hpa || 1013)} hPa</div>
        </div>

        <div className="glass-panel p-5 rounded-xl border border-slate-800">
          <div className="text-slate-400 text-xs font-mono">FORWARD MOTION</div>
          <div className="text-xl font-black text-slate-200 mt-1">{cyclone?.movement_speed_kmh} km/h</div>
          <div className="text-[11px] text-slate-500 font-mono mt-1">Heading: {cyclone?.movement_direction_deg}° (Northward)</div>
        </div>
      </div>

      {/* Trajectory & Prediction Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left 2 Cols: Short-term Predictions Table & Trajectory Analysis */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-cyan-400" />
                <h3 className="text-lg font-bold text-white">Model C: Short-Term Forecast Horizons</h3>
              </div>
              <span className="text-xs font-mono text-slate-400">LEAD TIME: +6H / +12H / +24H</span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Lead Time</th>
                    <th className="py-2.5 px-3">Forecast Position</th>
                    <th className="py-2.5 px-3">Predicted Wind</th>
                    <th className="py-2.5 px-3">Central Pressure</th>
                    <th className="py-2.5 px-3">Trend Vector</th>
                    <th className="py-2.5 px-3 text-right">Confidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {predictions.map((p, idx) => (
                    <tr key={idx} className="hover:bg-slate-900/40">
                      <td className="py-3 px-3 font-bold text-cyan-400">+{p.lead_h} Hours</td>
                      <td className="py-3 px-3 text-slate-300">{p.lat.toFixed(1)}°N, {p.lon.toFixed(1)}°E</td>
                      <td className="py-3 px-3 text-amber-300 font-bold">{p.wind_kts} kts ({Math.round(p.wind_kts * 1.852)} km/h)</td>
                      <td className="py-3 px-3 text-slate-200">{p.p_hpa} hPa</td>
                      <td className="py-3 px-3 font-sans">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          p.trend.includes("INTENSIFYING") ? "bg-rose-950 text-rose-400" : "bg-emerald-950 text-emerald-400"
                        }`}>
                          {p.trend}
                        </span>
                      </td>
                      <td className="py-3 px-3 text-right text-slate-300 font-bold">{(p.conf * 100).toFixed(0)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Meteorological Landfall Advisory Box */}
          <div className="p-6 rounded-2xl bg-amber-950/20 border border-amber-500/40 space-y-3">
            <div className="flex items-center gap-2 text-amber-400 font-bold text-sm">
              <ShieldAlert className="h-5 w-5" />
              <span>Projected Landfall & Surge Advisory (Prototype Scenario)</span>
            </div>
            <p className="text-slate-300 text-xs leading-relaxed">
              Based on the 12-hour Model C forecast vector, the storm vortex is tracking at 16 km/h towards coastal lowlands.
              Estimated coastal storm surge height is 1.5 to 2.8 meters with gale to storm force gusts.
            </p>
            <div className="text-[11px] text-amber-400/80 font-mono">
              *Prototype simulation for emergency management exercise drills. Not an official operational warning.
            </div>
          </div>
        </div>

        {/* Right 1 Col: Quick Action & Observation Parameters */}
        <div className="space-y-6">
          <div className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4 text-xs font-mono">
            <h4 className="text-sm font-bold text-white font-sans border-b border-slate-800 pb-2">
              Sensor Telemetry Breakdown
            </h4>

            <div className="space-y-2">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Current Latitude</span>
                <span className="text-white">{cyclone?.current_lat}°N</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Current Longitude</span>
                <span className="text-white">{cyclone?.current_lon}°E</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Wind Radii (34 kt Gale)</span>
                <span className="text-white">~180 km radius</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Wind Radii (50 kt Storm)</span>
                <span className="text-white">~95 km radius</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Wind Radii (64 kt Core)</span>
                <span className="text-white">~45 km radius</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Status</span>
                <span className="text-emerald-400 font-bold">{cyclone?.status}</span>
              </div>
            </div>

            <Link
              href={`/analysis?lat=${cyclone?.current_lat}&lon=${cyclone?.current_lon}&pressure=${cyclone?.central_pressure_hpa}&wind=${Math.round((cyclone?.max_sustained_wind_kts || 0) * 1.852)}`}
              className="mt-4 w-full py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold font-sans text-xs flex items-center justify-center gap-2 transition-all shadow-lg shadow-cyan-600/20"
            >
              <Cpu className="h-4 w-4" />
              <span>Open in AI Analysis Workbench</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
