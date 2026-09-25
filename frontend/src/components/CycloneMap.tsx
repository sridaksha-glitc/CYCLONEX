"use client";

import { useState } from "react";
import { Layers, ZoomIn, ZoomOut, AlertTriangle, Compass, Navigation } from "lucide-react";

interface StormPoint {
  id: string;
  name: string;
  code: string;
  lat: number;
  lon: number;
  wind_kts: number;
  pressure: number;
  category: string;
  risk_level: string;
  risk_score: number;
  status: string;
  data_mode: string;
}

interface CycloneMapProps {
  cyclones: StormPoint[];
  selectedCycloneId?: string;
  onSelectCyclone?: (c: StormPoint) => void;
}

export function CycloneMap({ cyclones, selectedCycloneId, onSelectCyclone }: CycloneMapProps) {
  const [showCone, setShowCone] = useState(true);
  const [showWindField, setShowWindField] = useState(true);
  const [selectedId, setSelectedId] = useState<string>(selectedCycloneId || cyclones[0]?.id);

  // Basin bounding box: Lat 4°N to 26°N, Lon 64°E to 96°E
  const minLat = 4.0;
  const maxLat = 26.0;
  const minLon = 64.0;
  const maxLon = 96.0;

  // Convert lat/lon to SVG percentage coordinates
  const getCoords = (lat: number, lon: number) => {
    const x = ((lon - minLon) / (maxLon - minLon)) * 100;
    const y = ((maxLat - lat) / (maxLat - minLat)) * 100;
    return { x: Math.max(5, Math.min(95, x)), y: Math.max(5, Math.min(95, y)) };
  };

  const activeStorm = cyclones.find((c) => c.id === selectedId) || cyclones[0];

  return (
    <div className="relative w-full h-[540px] bg-slate-950 rounded-xl border border-slate-800 overflow-hidden shadow-2xl">
      {/* Map Control Toolbar */}
      <div className="absolute top-4 left-4 z-20 flex flex-wrap gap-2">
        <button
          onClick={() => setShowCone(!showCone)}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium border backdrop-blur transition-all flex items-center gap-1.5 ${
            showCone
              ? "bg-cyan-950/80 border-cyan-500/50 text-cyan-300"
              : "bg-slate-900/80 border-slate-700 text-slate-400"
          }`}
        >
          <Navigation className="h-3.5 w-3.5" />
          <span>Forecast Cone</span>
        </button>

        <button
          onClick={() => setShowWindField(!showWindField)}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium border backdrop-blur transition-all flex items-center gap-1.5 ${
            showWindField
              ? "bg-blue-950/80 border-blue-500/50 text-blue-300"
              : "bg-slate-900/80 border-slate-700 text-slate-400"
          }`}
        >
          <Compass className="h-3.5 w-3.5" />
          <span>Wind Radii (34/50/64kt)</span>
        </button>
      </div>

      {/* Basin Legend & Mode Tag */}
      <div className="absolute top-4 right-4 z-20 bg-slate-900/85 backdrop-blur border border-slate-800 p-2.5 rounded-lg text-[11px] font-mono text-slate-300">
        <div className="text-cyan-400 font-bold mb-1 flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-cyan-400 animate-ping"></span>
          INSAT-3D/3DR RADAR SCAN
        </div>
        <div>BASIN: NIO (BoB / Arabian Sea)</div>
        <div className="text-slate-400">PROJECTION: MERCATOR TROPICAL</div>
      </div>

      {/* SVG Canvas Map */}
      <svg className="w-full h-full" viewBox="0 0 1000 600" preserveAspectRatio="none">
        <defs>
          <radialGradient id="radarGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#050b14" stopOpacity="0" />
          </radialGradient>

          <linearGradient id="coneGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.4" />
            <stop offset="100%" stopColor="#ef4444" stopOpacity="0.1" />
          </linearGradient>

          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Ocean Background */}
        <rect width="1000" height="600" fill="#050e1c" />

        {/* Lat / Lon Grid Lines */}
        {[10, 15, 20, 25].map((lat) => {
          const { y } = getCoords(lat, 80);
          const py = (y / 100) * 600;
          return (
            <g key={lat}>
              <line x1="0" y1={py} x2="1000" y2={py} stroke="#1e293b" strokeDasharray="3 3" />
              <text x="15" y={py - 5} fill="#475569" fontSize="10" fontFamily="monospace">
                {lat}°N
              </text>
            </g>
          );
        })}

        {[70, 75, 80, 85, 90].map((lon) => {
          const { x } = getCoords(15, lon);
          const px = (x / 100) * 1000;
          return (
            <g key={lon}>
              <line x1={px} y1="0" x2={px} y2="600" stroke="#1e293b" strokeDasharray="3 3" />
              <text x={px + 5} y="585" fill="#475569" fontSize="10" fontFamily="monospace">
                {lon}°E
              </text>
            </g>
          );
        })}

        {/* Coastline Stylized Polygons (India, Bangladesh, Myanmar, Sri Lanka) */}
        {/* Gujarat / West Coast */}
        <path
          d="M 170 120 L 220 220 L 260 270 L 320 370 L 390 470 L 440 540 L 460 520 L 430 420 L 480 340 L 610 280 L 730 210 L 780 180 L 800 130"
          fill="none"
          stroke="#334155"
          strokeWidth="2.5"
          strokeLinecap="round"
        />

        {/* Sri Lanka Stylized Island */}
        <polygon points="460,490 480,510 475,540 450,530" fill="#1e293b" stroke="#475569" strokeWidth="1.5" />

        {/* Bay of Bengal & Bangladesh Delta */}
        <path
          d="M 730 210 Q 770 160 820 170 Q 860 200 890 280 L 920 400"
          fill="none"
          stroke="#334155"
          strokeWidth="2.5"
        />

        {/* Forecast Cone for Active Storm */}
        {showCone && activeStorm && (
          <g>
            {(() => {
              const { x, y } = getCoords(activeStorm.lat, activeStorm.lon);
              const px = (x / 100) * 1000;
              const py = (y / 100) * 600;

              // Forecast points (6h, 12h, 24h heading northward)
              const p6x = px + 15;
              const p6y = py - 40;
              const p12x = px + 25;
              const p12y = py - 85;
              const p24x = px + 45;
              const p24y = py - 160;

              return (
                <>
                  {/* Uncertainty polygon */}
                  <polygon
                    points={`${px},${py} ${p24x - 65},${p24y} ${p24x + 65},${p24y}`}
                    fill="url(#coneGrad)"
                    stroke="#06b6d4"
                    strokeWidth="1"
                    strokeDasharray="4 4"
                  />
                  {/* Predicted Track Line */}
                  <path
                    d={`M ${px} ${py} Q ${p6x} ${p6y} ${p12x} ${p12y} T ${p24x} ${p24y}`}
                    fill="none"
                    stroke="#38bdf8"
                    strokeWidth="3"
                    strokeDasharray="5 5"
                  />
                  {/* Forecast Waypoints */}
                  <circle cx={p6x} cy={p6y} r="5" fill="#38bdf8" />
                  <circle cx={p12x} cy={p12y} r="6" fill="#f59e0b" />
                  <circle cx={p24x} cy={p24y} r="7" fill="#ef4444" />

                  <text x={p6x + 8} y={p6y + 3} fill="#94a3b8" fontSize="10" fontFamily="monospace">+6h</text>
                  <text x={p12x + 8} y={p12y + 3} fill="#f59e0b" fontSize="10" fontFamily="monospace">+12h (Landfall)</text>
                  <text x={p24x + 8} y={p24y + 3} fill="#ef4444" fontSize="10" fontFamily="monospace">+24h (Inland)</text>
                </>
              );
            })()}
          </g>
        )}

        {/* Cyclones Markers */}
        {cyclones.map((c) => {
          const { x, y } = getCoords(c.lat, c.lon);
          const px = (x / 100) * 1000;
          const py = (y / 100) * 600;
          const isSelected = c.id === selectedId;

          const isExtreme = c.risk_level === "EXTREME";
          const isHigh = c.risk_level === "HIGH";
          const color = isExtreme ? "#ef4444" : isHigh ? "#f59e0b" : "#06b6d4";

          return (
            <g
              key={c.id}
              className="cursor-pointer transition-transform hover:scale-110"
              onClick={() => {
                setSelectedId(c.id);
                if (onSelectCyclone) onSelectCyclone(c);
              }}
            >
              {/* Wind Radii Concentric Circles */}
              {showWindField && (
                <>
                  <circle cx={px} cy={py} r={c.wind_kts * 0.9} fill="none" stroke={color} strokeOpacity="0.2" strokeWidth="1" strokeDasharray="3 3" />
                  <circle cx={px} cy={py} r={c.wind_kts * 0.55} fill="none" stroke={color} strokeOpacity="0.35" strokeWidth="1.5" />
                  <circle cx={px} cy={py} r={c.wind_kts * 0.28} fill="none" stroke={color} strokeOpacity="0.6" strokeWidth="1.5" />
                </>
              )}

              {/* Pulsing Eye Warning */}
              <circle cx={px} cy={py} r="22" fill={color} fillOpacity="0.25" className="animate-pulse" />
              <circle cx={px} cy={py} r="14" fill={color} fillOpacity="0.6" />
              <circle cx={px} cy={py} r="6" fill="#ffffff" filter="url(#glow)" />

              {/* Label Card */}
              <rect
                x={px + 12}
                y={py - 30}
                width="145"
                height="45"
                rx="6"
                fill="#090f1d"
                stroke={isSelected ? "#38bdf8" : "#1e293b"}
                strokeWidth={isSelected ? "2" : "1"}
              />
              <text x={px + 20} y={py - 15} fill="#ffffff" fontSize="12" fontWeight="bold">
                {c.name}
              </text>
              <text x={px + 20} y={py - 2} fill={color} fontSize="10" fontFamily="monospace">
                {c.category} • {c.wind_kts} kts
              </text>
            </g>
          );
        })}
      </svg>

      {/* Selected Storm Quick Info Panel Overlay */}
      {activeStorm && (
        <div className="absolute bottom-4 left-4 z-20 bg-slate-900/90 backdrop-blur border border-slate-800 p-4 rounded-xl max-w-sm text-xs shadow-2xl">
          <div className="flex items-center justify-between gap-2 mb-2">
            <div>
              <span className="text-[10px] text-cyan-400 font-mono font-bold tracking-wider">{activeStorm.code}</span>
              <h4 className="text-sm font-bold text-white">{activeStorm.name}</h4>
            </div>
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                activeStorm.risk_level === "EXTREME"
                  ? "bg-rose-950 text-rose-300 border border-rose-800"
                  : activeStorm.risk_level === "HIGH"
                  ? "bg-amber-950 text-amber-300 border border-amber-800"
                  : "bg-cyan-950 text-cyan-300 border border-cyan-800"
              }`}
            >
              {activeStorm.risk_level} RISK ({activeStorm.risk_score}/100)
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-slate-300 font-mono text-[11px] mb-2">
            <div className="bg-slate-950/60 p-1.5 rounded">
              <span className="text-slate-500 block text-[9px]">MAX WINDS</span>
              <strong className="text-white text-xs">{activeStorm.wind_kts} kts</strong> ({Math.round(activeStorm.wind_kts * 1.852)} km/h)
            </div>
            <div className="bg-slate-950/60 p-1.5 rounded">
              <span className="text-slate-500 block text-[9px]">CENTRAL PRESSURE</span>
              <strong className="text-white text-xs">{activeStorm.pressure} hPa</strong>
            </div>
            <div className="bg-slate-950/60 p-1.5 rounded">
              <span className="text-slate-500 block text-[9px]">COORDINATES</span>
              <span>{activeStorm.lat}°N, {activeStorm.lon}°E</span>
            </div>
            <div className="bg-slate-950/60 p-1.5 rounded">
              <span className="text-slate-500 block text-[9px]">DATA PROVENANCE</span>
              <span className="text-cyan-400 font-semibold">{activeStorm.data_mode}</span>
            </div>
          </div>

          <div className="text-[10px] text-slate-400 flex items-center justify-between border-t border-slate-800/80 pt-1.5">
            <span>Class: {activeStorm.category}</span>
            <span className="text-slate-500 font-mono">STATUS: {activeStorm.status}</span>
          </div>
        </div>
      )}
    </div>
  );
}
