# CYCLONEX 🌀
### Multi-Source AI/ML Tropical Cyclone Intelligence & Early Risk Assessment Platform

> **Hackathon Prototype Notice:**  
> CYCLONEX is a research prototype and decision-support index built for evaluation under strict hackathon criteria.  
> It is **NOT** an operational public meteorological warning system.  
> CYCLONEX maintains strict provenance boundaries between **REAL**, **HISTORICAL**, and **SIMULATED/DEMO** observations and never presents synthetic values as real operational warnings. Refer exclusively to official bulletins from the **India Meteorological Department (IMD)** and the **World Meteorological Organization (WMO)** for life-safety warnings.

---

## 1. System Architecture

```
                     CYCLONEX
                          │
          ┌───────────────┼────────────────┐
          │               │                │
          ▼               ▼                ▼
      SATELLITE       OPENWEATHER       IBTrACS
         DATA            DATA          HISTORICAL
          │               │                │
          └───────────────┼────────────────┘
                          ▼
                 DATA PREPROCESSING
                          │
                          ▼
                 FEATURE EXTRACTION
                          │
             ┌────────────┼────────────┐
             │            │            │
             ▼            ▼            ▼
         IMAGE         WEATHER      HISTORICAL
         FEATURES      FEATURES     FEATURES
             │            │            │
             └────────────┼────────────┘
                          ▼
                   FEATURE FUSION
                          │
         ┌────────────────┼────────────────┐
         ▼                ▼                ▼
     DETECTION       CLASSIFICATION     PREDICTION
         │                │                │
         └────────────────┼────────────────┘
                          ▼
                   AI EXPLANATION
                          │
                          ▼
                   RISK ENGINE
                          │
             ┌────────────┴────────────┐
             ▼                         ▼
        SUPABASE                    FASTAPI
             │                         │
             └────────────┬────────────┘
                          ▼
                   NEXT.JS DASHBOARD
                          │
             ┌────────────┼────────────┐
             ▼            ▼            ▼
            MAP      PREDICTION      ALERTS
                                       │
                                       ▼
                                      n8n
```

---

## 2. Core Subsystems & ML Pipeline

1. **Model A — Cyclone Detection:**
   * **Input:** Satellite Infrared (IR 10.8µm) or visible spectral imagery / proxy parameters.
   * **Output:** `cyclone_detected: bool`, `cyclone_probability: float`.
   * **Method:** Lightweight computer vision feature extraction calculating CDO (Central Dense Overcast) quadrant symmetry, minimum core brightness temperature ($T_B$), and spiral curvature gradients.

2. **Model B — Multi-Source Cyclone Classification:**
   * **Input:** Fused feature vector (satellite CDO symmetry + 10m sustained winds + central barometric pressure deficit + sea surface temperature).
   * **Output:** Authoritative IMD / WMO Category (e.g. *Low Pressure Area, Depression, Deep Depression, Cyclonic Storm, Severe Cyclonic Storm, Very Severe Cyclonic Storm, Extremely Severe Cyclonic Storm, Super Cyclonic Storm*).
   * **Meteorological Grounding:** Grounded in the empirical Atkinson-Holliday wind-pressure physics relationship:
     $$V_{max} = 6.7 \times (1010 - P_c)^{0.644}$$

3. **Model C — Short-term Trajectory & Intensity Prediction:**
   * **Input:** Current coordinates, sustained winds, central pressure, 6-hour barometric delta ($\Delta P_{6h}$), heading vector.
   * **Output:** 6-hour, 12-hour, and 24-hour forecast horizons (wind speed, central pressure, coordinate trajectory, rapid intensification alert).

4. **Multi-Source Feature Fusion:**
   * Weighted integration of visual convective organization (30%), atmospheric surface pressure and winds (45%), and climatological sea surface temperature (25%).

5. **Explainable AI (XAI) Attribution:**
   * Generates feature contribution breakdowns with directional impact (*ESCALATING*, *MITIGATING*, *NEUTRAL*) and plain-language descriptions.

6. **Prototype Risk Index (PRI):**
   * Multi-factor decision-support score from 0 to 100 categorizing risks into `LOW` (0-35), `MODERATE` (36-60), `HIGH` (61-80), and `EXTREME` (81-100).
   * Clearly marked as a **non-operational decision-support index**.

7. **Automated Alerting Engine (n8n):**
   * Webhook-triggered workflow (`POST http://localhost:5678/webhook/cyclonex-alert`) evaluating risk scores $\ge 60$ and dispatching structured multi-channel bulletins.

---

## 3. Technology Stack

* **Frontend:** Next.js (App Router), React, TypeScript, Tailwind CSS, Lucide icons, SVG/Canvas geospatial radar map.
* **Backend:** Python 3.13, FastAPI, Uvicorn, Pydantic v2.
* **Machine Learning:** scikit-learn, NumPy, SciPy, Pillow, Pandas.
* **ML Debugging:** Streamlit interactive diagnostic workbench.
* **Persistence:** Supabase PostgreSQL migrations + zero-downtime offline SQLite/in-memory fallback store.
* **Automation:** n8n workflow JSON (`automation/n8n/cyclonex_alert_workflow.json`).
* **API Testing:** Bruno HTTP collection (`bruno/CYCLONEX_API/`).

---

## 4. Quickstart Guide

### 1. Backend Setup & Tests
```bash
# Activate virtual environment
backend\venv\Scripts\activate

# Run test suite (10/10 tests covering all endpoints)
pytest

# Launch FastAPI backend server
backend\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation will be available at: `http://localhost:8000/docs`

### 2. Frontend Launch
```bash
cd frontend
npm run dev
```
Open `http://localhost:3000` to access the Scientific Command Center.

### 3. Streamlit ML Debugging Workbench
```bash
backend\venv\Scripts\streamlit.exe run ml/app_streamlit.py
```
Open `http://localhost:8501` to inspect Models A, B, and C parameters interactively.

---

## 5. Primary API Contract

### Unified Multi-Source Endpoint: `POST /api/v1/analyze`

**Request:**
```json
{
  "latitude": 13.5,
  "longitude": 80.2,
  "temperature": 28.4,
  "humidity": 84,
  "pressure": 978,
  "wind_speed": 110,
  "wind_direction": 180,
  "satellite_image": null
}
```

**Response:**
```json
{
  "cyclone_detected": true,
  "cyclone_probability": 0.94,
  "classification": "Severe Cyclonic Storm",
  "classification_confidence": 0.92,
  "predicted_wind_speed": 128.5,
  "predicted_wind_speed_kts": 69.4,
  "predicted_pressure_hpa": 972.0,
  "trend": "INTENSIFYING",
  "risk_score": 78,
  "risk_level": "HIGH",
  "explanation": [
    {
      "feature": "Central Atmospheric Pressure Deficit",
      "value": "978.0 hPa (Δ -35.0 hPa)",
      "importance": 0.34,
      "impact": "ESCALATING",
      "description": "Deep central barometric drop indicates intense low-pressure cyclonic vortex core."
    }
  ],
  "model_version": "v1.0-fusion",
  "data_mode": "DEMO",
  "multi_horizon_predictions": [
    {
      "lead_time_hours": 6,
      "predicted_wind_speed_kmh": 120.2,
      "predicted_wind_speed_kts": 64.9,
      "predicted_pressure_hpa": 974.5,
      "predicted_latitude": 14.1,
      "predicted_longitude": 80.0,
      "classification": "Very Severe Cyclonic Storm",
      "trend": "INTENSIFYING",
      "confidence": 0.88
    }
  ],
  "data_sources": [
    "Direct User In-Situ Input",
    "Synthetic Satellite Proxy Features"
  ],
  "timestamp": "2026-09-25T17:15:00Z",
  "disclaimer": "Non-operational research prototype. This decision-support index does not replace official meteorological warnings from IMD, WMO, or national weather agencies."
}
```

---

## 6. Authoritative IMD Cyclone Scale Reference

| Classification | Abbr | Sustained Winds (kts) | Sustained Winds (km/h) | Pressure Deficit |
| :--- | :--- | :--- | :--- | :--- |
| **Low Pressure Area** | LPA | < 17 kts | < 31 km/h | < 1.0 hPa |
| **Depression** | D | 17 – 27 kts | 31 – 49 km/h | 1.0 – 3.0 hPa |
| **Deep Depression** | DD | 28 – 33 kts | 50 – 61 km/h | 3.0 – 4.5 hPa |
| **Cyclonic Storm** | CS | 34 – 47 kts | 62 – 88 km/h | 4.5 – 8.5 hPa |
| **Severe Cyclonic Storm** | SCS | 48 – 63 kts | 89 – 117 km/h | 8.5 – 15.0 hPa |
| **Very Severe Cyclonic Storm** | VSCS | 64 – 89 kts | 118 – 166 km/h | 15.0 – 30.0 hPa |
| **Extremely Severe Cyclonic Storm** | ESCS | 90 – 119 kts | 167 – 221 km/h | 30.0 – 60.0 hPa |
| **Super Cyclonic Storm** | SuCS | ≥ 120 kts | ≥ 222 km/h | > 60.0 hPa |
