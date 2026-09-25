# CYCLONEX System Architecture & Specifications

**Multi-Source AI/ML Tropical Cyclone Intelligence & Early Risk Assessment Platform**

---

## 1. System Overview

CYCLONEX is an end-to-end meteorological intelligence platform designed to ingest multi-source observational data (Satellite IR/visible imagery, OpenWeather atmospheric telemetry, and historical IBTrACS cyclogenesis patterns) to perform:
1. **Model A (Detection):** Computer-vision based cyclone formation identification.
2. **Model B (Classification):** IMD/WMO standard 8-tier tropical cyclone categorization.
3. **Model C (Short-Term Prediction):** 6h, 12h, and 24h intensity trajectory (wind speed & central pressure deficit) and track progression.
4. **Transparent Risk Engine:** Prototype Risk Index ($PRI \in [0, 100]$) with decision-support tiers (LOW, MODERATE, HIGH, EXTREME).
5. **Explainable AI (XAI):** Feature-importance breakdown explaining model predictions.
6. **Unified Persistence & Offline Reliability:** Supabase PostgreSQL cloud sync with automatic local zero-latency fallback.
7. **Automated Alerting:** n8n webhook workflow dispatching multi-channel advisories and emergency warnings.
8. **Scientific Command Center:** High-performance Next.js 14/15 interface with geospatial tracking, radar analytics, and real-time monitoring.

---

## 2. High-Level Data Flow

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

## 3. Provenance & Meteorological Honesty Guarantees

* **Real Data:** Fetched live from OpenWeather API or authoritative sensors when configured.
* **Historical Data:** Benchmark observations sourced from verified historical storm tracks (Cyclone Remal 2024, Cyclone Biparjoy 2023, Cyclone Michaung 2023, Cyclone Amphan 2020).
* **Demonstration / Simulated Data:** Deterministic meteorological mock adapters explicitly labeled with `data_mode: "DEMO"`.
* **Prototype Risk Index:** Explicitly declared on UI and API responses as a **decision-support heuristic**, NOT an official meteorological warning.

---

## 4. REST API Endpoint Catalog

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Server uptime & system health check |
| `GET` | `/api/v1/health` | Comprehensive subsystem diagnostic (DB, ML, Weather) |
| `POST` | `/api/v1/ingest` | Ingest multi-sensor observation data |
| `POST` | `/api/v1/detect` | Model A: Satellite image cyclone detection |
| `POST` | `/api/v1/classify` | Model B: Multi-source cyclone classification |
| `POST` | `/api/v1/predict` | Model C: 6h / 12h / 24h intensity trajectory |
| `POST` | `/api/v1/analyze` | **Primary Unified Endpoint:** Multi-source fusion inference |
| `GET` | `/api/v1/cyclones` | List active & historical cyclones |
| `GET` | `/api/v1/cyclones/{id}` | Detailed cyclone telemetry, tracks & predictions |
| `GET` | `/api/v1/history` | Historical cyclone analogs & climatology |
| `POST` | `/api/v1/alerts` | Trigger / dispatch automated alert to n8n webhook |
