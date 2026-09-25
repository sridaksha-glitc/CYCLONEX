"use client";

import { useState, useEffect } from "react";
import { 
  Bell, 
  ShieldAlert, 
  AlertTriangle, 
  CheckCircle2, 
  Send, 
  RefreshCw, 
  Compass, 
  Clock,
  Radio
} from "lucide-react";
import { fetchAlerts, dispatchAlert, AlertItem } from "@/lib/api";

export default function AlertsCenterPage() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Manual Trigger Form States
  const [stormName, setStormName] = useState("Invest 91B Cell");
  const [classification, setClassification] = useState("Deep Depression");
  const [severity, setSeverity] = useState("WARNING");
  const [riskScore, setRiskScore] = useState(65);
  const [windKts, setWindKts] = useState(35);
  const [pressureHpa, setPressureHpa] = useState(994);
  const [lat, setLat] = useState(14.2);
  const [lon, setLon] = useState(84.5);
  const [customMsg, setCustomMsg] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [successNotice, setSuccessNotice] = useState<string | null>(null);

  const loadAlerts = async () => {
    try {
      const data = await fetchAlerts();
      setAlerts(data.alerts || []);
    } catch (e) {
      console.error("Alerts fetch error:", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, []);

  const handleTriggerAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setSuccessNotice(null);

    try {
      const payload = {
        cyclone_name: stormName,
        classification,
        severity,
        risk_score: riskScore,
        risk_level: riskScore >= 80 ? "EXTREME" : riskScore >= 60 ? "HIGH" : "MODERATE",
        wind_speed_kts: windKts,
        pressure_hpa: pressureHpa,
        latitude: lat,
        longitude: lon,
        message: customMsg || undefined
      };

      const data = await dispatchAlert(payload);
      setSuccessNotice(`Alert '${data.title}' successfully dispatched! n8n webhook triggered: ${data.n8n_dispatched ? 'YES' : 'LOGGED LOCALLY'}`);
      loadAlerts();
    } catch (err: any) {
      console.error(err);
    } finally {
      setSubmitting(false);
    }
  };


  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="border-b border-slate-800 pb-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-2 text-xs font-mono text-amber-400 mb-1">
            <Radio className="h-4 w-4 animate-pulse" />
            <span>AUTOMATED INCIDENT DISPATCH & n8n WEBHOOKS</span>
          </div>
          <h1 className="text-3xl font-black text-white">Cyclone Alert Center</h1>
          <p className="text-slate-400 text-sm mt-1">
            Automated alerting engine monitoring real-time threshold breaches (PRI &ge; 60) and dispatching multi-channel broadcasts.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-slate-900 border border-slate-800 px-4 py-2 rounded-xl text-xs font-mono">
            <span className="text-slate-400 block text-[10px]">n8n WEBHOOK ENDPOINT</span>
            <span className="text-cyan-400 font-bold">http://localhost:5678/webhook/cyclonex-alert</span>
          </div>
        </div>
      </div>

      {successNotice && (
        <div className="p-4 rounded-xl bg-emerald-950/60 border border-emerald-700 text-emerald-300 text-xs flex items-center gap-2 font-mono">
          <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />
          <span>{successNotice}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Manual Alert Dispatch Modal / Form (5 Cols) */}
        <div className="lg:col-span-5 space-y-6">
          <form onSubmit={handleTriggerAlert} className="glass-panel p-6 rounded-2xl border border-slate-800 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Bell className="h-4 w-4 text-amber-400" />
                <span>Simulate Automated Dispatch</span>
              </h2>
              <span className="text-[10px] font-mono text-slate-500">TEST WEBHOOK</span>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="text-[11px] font-mono text-slate-400 block mb-1">Cyclone Name / Tag</label>
                <input
                  type="text"
                  required
                  value={stormName}
                  onChange={(e) => setStormName(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white text-xs font-mono focus:outline-none focus:border-amber-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-mono text-slate-400 block mb-1">IMD Classification</label>
                  <select
                    value={classification}
                    onChange={(e) => setClassification(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white text-xs font-mono focus:outline-none focus:border-amber-500"
                  >
                    <option value="Depression">Depression</option>
                    <option value="Deep Depression">Deep Depression</option>
                    <option value="Cyclonic Storm">Cyclonic Storm</option>
                    <option value="Severe Cyclonic Storm">Severe Cyclonic Storm</option>
                    <option value="Very Severe Cyclonic Storm">Very Severe Cyclonic Storm</option>
                    <option value="Extremely Severe Cyclonic Storm">Extremely Severe Cyclonic Storm</option>
                    <option value="Super Cyclonic Storm">Super Cyclonic Storm</option>
                  </select>
                </div>

                <div>
                  <label className="text-[11px] font-mono text-slate-400 block mb-1">Severity Tier</label>
                  <select
                    value={severity}
                    onChange={(e) => setSeverity(e.target.value)}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white text-xs font-mono focus:outline-none focus:border-amber-500"
                  >
                    <option value="ADVISORY">ADVISORY</option>
                    <option value="WATCH">WATCH</option>
                    <option value="WARNING">WARNING</option>
                    <option value="EMERGENCY">EMERGENCY</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-[11px] font-mono text-slate-400 block mb-1">Risk Score</label>
                  <input
                    type="number"
                    min="1"
                    max="100"
                    value={riskScore}
                    onChange={(e) => setRiskScore(parseInt(e.target.value))}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white text-xs font-mono focus:outline-none focus:border-amber-500"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-mono text-slate-400 block mb-1">Wind (kts)</label>
                  <input
                    type="number"
                    value={windKts}
                    onChange={(e) => setWindKts(parseFloat(e.target.value))}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white text-xs font-mono focus:outline-none focus:border-amber-500"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-mono text-slate-400 block mb-1">Pressure (hPa)</label>
                  <input
                    type="number"
                    value={pressureHpa}
                    onChange={(e) => setPressureHpa(parseFloat(e.target.value))}
                    className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white text-xs font-mono focus:outline-none focus:border-amber-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-mono text-slate-400 block mb-1">Custom Advisory Bulletin Text</label>
                <textarea
                  rows={3}
                  value={customMsg}
                  onChange={(e) => setCustomMsg(e.target.value)}
                  placeholder="Enter specific evacuation or emergency briefing details..."
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-white text-xs focus:outline-none focus:border-amber-500"
                ></textarea>
              </div>
            </div>

            <button
              type="submit"
              disabled={submitting}
              className="w-full py-3 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-black text-xs tracking-wider uppercase transition-all shadow-lg shadow-amber-500/20 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {submitting ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin text-slate-950" />
                  <span>Transmitting Payload...</span>
                </>
              ) : (
                <>
                  <Send className="h-4 w-4 text-slate-950" />
                  <span>Transmit Alert to n8n Webhook</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right Column: Alert History Log (7 Cols) */}
        <div className="lg:col-span-7 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-rose-400" />
              <span>Dispatched Advisory & Warning Logs</span>
            </h2>
            <span className="text-xs font-mono text-slate-400">{alerts.length} Total Records</span>
          </div>

          <div className="space-y-3">
            {alerts.map((al, idx) => {
              const isEmergency = al.severity === "EMERGENCY";
              const isWarning = al.severity === "WARNING";
              const badgeColor = isEmergency
                ? "bg-rose-950 text-rose-300 border-rose-800"
                : isWarning
                ? "bg-amber-950 text-amber-300 border-amber-800"
                : "bg-blue-950 text-blue-300 border-blue-800";

              return (
                <div key={idx} className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-3 hover:border-slate-700 transition-colors">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800/80 pb-2.5">
                    <div>
                      <span className="text-[10px] font-mono text-cyan-400 font-bold tracking-wider">{al.cyclone_name}</span>
                      <h3 className="text-sm font-bold text-white">{al.title}</h3>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold border ${badgeColor}`}>
                        {al.severity}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-900 text-slate-300 border border-slate-800">
                        RISK {al.risk_score}/100
                      </span>
                    </div>
                  </div>

                  <p className="text-slate-300 text-xs leading-relaxed font-sans">{al.message}</p>

                  <div className="flex flex-wrap items-center justify-between gap-2 text-[10px] font-mono text-slate-500 pt-1">
                    <div className="flex items-center gap-3">
                      <span>CHANNELS: {al.channels?.join(", ") || "webhook, dashboard"}</span>
                      <span>•</span>
                      <span className={al.n8n_dispatched ? "text-emerald-400 font-bold" : "text-slate-400"}>
                        n8n: {al.n8n_dispatched ? "DISPATCHED" : "LOGGED"}
                      </span>
                    </div>
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {al.dispatched_at ? new Date(al.dispatched_at).toLocaleString() : "Just now"}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
