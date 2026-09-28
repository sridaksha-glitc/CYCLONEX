/**
 * CYCLONEX Centralized API Client
 * Connects Next.js Command Center to FastAPI backend.
 * Provides resilient fallbacks for offline demonstrations.
 */

export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL || 
  process.env.NEXT_PUBLIC_API_URL || 
  "https://cyclonex-backend.vercel.app"
).replace(/\/$/, "");

export interface RiskFactor {
  factor: string;
  score: number;
  max_score: number;
  metric: string;
}

export interface RiskAssessment {
  risk_score: number;
  risk_level: "LOW" | "MODERATE" | "HIGH" | "EXTREME";
  contributing_factors: RiskFactor[];
  label: string;
  disclaimer: string;
}

export interface ForecastHorizon {
  lead_time_hours: number;
  predicted_wind_speed_kts: number;
  predicted_wind_speed_kmh: number;
  predicted_pressure_hpa: number;
  predicted_latitude: number;
  predicted_longitude: number;
  classification: string;
  trend: string;
  confidence: number;
}

export interface FeatureExplanation {
  feature: string;
  value: any;
  importance: number;
  impact: "ESCALATING" | "MITIGATING" | "NEUTRAL";
  description: string;
}

export interface AnalyzeRequest {
  latitude: number;
  longitude: number;
  temperature?: number | null;
  humidity?: number | null;
  pressure?: number | null;
  wind_speed?: number | null;
  wind_speed_kts?: number | null;
  wind_direction?: number | null;
  satellite_image?: string | null;
  satellite_image_path?: string | null;
  cyclone_id?: string | null;
  cyclone_name?: string | null;
  data_mode?: "DEMO" | "HISTORICAL" | "LIVE";
  force_live_weather?: boolean;
}

export interface AnalyzeResponse {
  cyclone_detected: boolean;
  cyclone_probability: number;
  classification: string;
  classification_confidence: number;
  classification_tier: number;
  predicted_wind_speed: number;
  predicted_wind_speed_kts: number;
  predicted_pressure_hpa: number;
  trend: string;
  rapid_intensification: boolean;
  multi_horizon_forecast: ForecastHorizon[];
  multi_horizon_predictions?: ForecastHorizon[];
  risk: RiskAssessment;
  risk_score: number;
  risk_level: "LOW" | "MODERATE" | "HIGH" | "EXTREME";
  explanation: FeatureExplanation[];
  model_version: string;
  data_mode: "DEMO" | "HISTORICAL" | "LIVE";
  sources: string[];
  data_sources?: string[];
  timestamp: string;
  disclaimer: string;
}

export interface CycloneItem {
  id: string;
  code: string;
  name: string;
  basin: string;
  status: string;
  classification: string;
  current_lat: number;
  current_lon: number;
  max_sustained_wind_kts: number;
  central_pressure_hpa: number;
  movement_speed_kmh: number;
  movement_direction_deg: number;
  risk_level: "LOW" | "MODERATE" | "HIGH" | "EXTREME";
  risk_score: number;
  data_mode: "DEMO" | "HISTORICAL" | "LIVE";
  started_at: string;
  last_updated_at: string;
}

export interface CycloneListResponse {
  total: number;
  active_count: number;
  cyclones: CycloneItem[];
}

export interface AlertItem {
  id: string;
  cyclone_id?: string;
  cyclone_name: string;
  title: string;
  message: string;
  severity: "ADVISORY" | "WATCH" | "WARNING" | "EMERGENCY";
  risk_score: number;
  risk_level: "LOW" | "MODERATE" | "HIGH" | "EXTREME";
  n8n_dispatched: boolean;
  channels: string[];
  dispatched_at: string;
}

export interface AlertListResponse {
  total: number;
  alerts: AlertItem[];
}

// 5 Canonical Benchmark Scenarios for STEP 12
export interface BenchmarkScenario {
  id: string;
  title: string;
  category: string;
  data_mode: "DEMO" | "HISTORICAL" | "LIVE";
  description: string;
  payload: AnalyzeRequest;
}

export const BENCHMARK_SCENARIOS: BenchmarkScenario[] = [
  {
    id: "calm",
    title: "1. CALM / NO CYCLONE",
    category: "Baseline Non-Cyclonic",
    data_mode: "DEMO",
    description: "Equatorial open waters with ambient surface pressure (1012 hPa) and light trade breeze (15 kts).",
    payload: {
      latitude: 8.0,
      longitude: 78.0,
      temperature: 28.0,
      humidity: 68.0,
      pressure: 1012.0,
      wind_speed_kts: 14.0,
      wind_direction: 210.0,
      data_mode: "DEMO",
      cyclone_name: "Calm Southern Waters"
    }
  },
  {
    id: "disturbance",
    title: "2. DEVELOPING DISTURBANCE",
    category: "Deep Depression",
    data_mode: "DEMO",
    description: "Incipient low pressure vortex with moderate convection, 30 kts winds, and 998 hPa core.",
    payload: {
      latitude: 12.8,
      longitude: 85.4,
      temperature: 29.5,
      humidity: 82.0,
      pressure: 998.0,
      wind_speed_kts: 30.0,
      wind_direction: 315.0,
      data_mode: "DEMO",
      cyclone_name: "Invest 91B Disturbance"
    }
  },
  {
    id: "severe_storm",
    title: "3. SEVERE CYCLONIC STORM",
    category: "Severe Cyclonic Storm (Remal Baseline)",
    data_mode: "HISTORICAL",
    description: "Organized cyclonic vortex matching Cyclone Remal (May 2024), 60 kts winds, 978 hPa central pressure.",
    payload: {
      latitude: 21.4,
      longitude: 89.2,
      temperature: 28.5,
      humidity: 86.0,
      pressure: 978.0,
      wind_speed_kts: 60.0,
      wind_direction: 355.0,
      data_mode: "HISTORICAL",
      cyclone_name: "Cyclone Remal"
    }
  },
  {
    id: "intensifying",
    title: "4. INTENSIFYING STORM",
    category: "Rapidly Deepening Vortex",
    data_mode: "DEMO",
    description: "Developing cyclonic system experiencing positive heat flux and rapid barometric deepening to 968 hPa.",
    payload: {
      latitude: 15.5,
      longitude: 86.2,
      temperature: 30.2,
      humidity: 89.0,
      pressure: 968.0,
      wind_speed_kts: 70.0,
      wind_direction: 340.0,
      data_mode: "DEMO",
      cyclone_name: "Intensifying Vortex Cell"
    }
  },
  {
    id: "high_risk",
    title: "5. HIGH-RISK STORM",
    category: "Extremely Severe Cyclonic Storm",
    data_mode: "HISTORICAL",
    description: "Catastrophic storm matching Cyclone Biparjoy (June 2023), 90 kts sustained winds, 954 hPa core.",
    payload: {
      latitude: 22.8,
      longitude: 68.1,
      temperature: 30.5,
      humidity: 90.0,
      pressure: 954.0,
      wind_speed_kts: 90.0,
      wind_direction: 45.0,
      data_mode: "HISTORICAL",
      cyclone_name: "Cyclone Biparjoy"
    }
  }
];

/**
 * Standard Verified Demo Analysis Payload (Production Baseline)
 */
export const DEMO_ANALYSIS_PAYLOAD: AnalyzeRequest = {
  latitude: 15.2,
  longitude: 72.8,
  temperature: 27.5,
  humidity: 82,
  pressure: 978,
  wind_speed: 55,
  wind_speed_kts: 55,
  wind_direction: 285,
  satellite_image: "remal_ir_2024.png",
  satellite_image_path: "",
  cyclone_id: "DEMO-REMAL-2024",
  cyclone_name: "REMAL",
  data_mode: "DEMO",
  force_live_weather: false
};

export async function runDemoAnalysis(): Promise<AnalyzeResponse> {
  return analyzeCyclone(DEMO_ANALYSIS_PAYLOAD);
}

export async function analyzeCyclone(request: AnalyzeRequest): Promise<AnalyzeResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request)
  });

  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`Inference API error (${res.status}): ${errorText}`);
  }

  return await res.json();
}

export async function fetchCyclones(status?: string): Promise<CycloneListResponse> {
  const url = status 
    ? `${API_BASE_URL}/api/v1/cyclones?status=${encodeURIComponent(status)}`
    : `${API_BASE_URL}/api/v1/cyclones`;

  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to fetch cyclones: ${res.status}`);
  }
  return await res.json();
}

export async function fetchCycloneById(id: string): Promise<CycloneItem> {
  const res = await fetch(`${API_BASE_URL}/api/v1/cyclones/${encodeURIComponent(id)}`);
  if (!res.ok) {
    throw new Error(`Cyclone '${id}' not found (${res.status})`);
  }
  return await res.json();
}

export async function fetchAlerts(): Promise<AlertListResponse> {
  const res = await fetch(`${API_BASE_URL}/api/v1/alerts`);
  if (!res.ok) {
    throw new Error(`Failed to fetch alerts: ${res.status}`);
  }
  return await res.json();
}

export async function dispatchAlert(payload: {
  cyclone_name: string;
  classification: string;
  severity: string;
  risk_score: number;
  risk_level: string;
  wind_speed_kts: number;
  pressure_hpa: number;
  latitude: number;
  longitude: number;
  message?: string;
}): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v1/alerts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!res.ok) {
    throw new Error(`Failed to dispatch alert: ${res.status}`);
  }
  return await res.json();
}

export async function fetchSystemHealth(): Promise<any> {
  const res = await fetch(`${API_BASE_URL}/api/v1/health`);
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.status}`);
  }
  return await res.json();
}
