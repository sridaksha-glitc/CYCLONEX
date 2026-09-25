-- ==============================================================================
-- CYCLONEX SUPABASE SCHEMA MIGRATION: 01_initial_schema.sql
-- Tables: cyclones, weather_observations, satellite_images, predictions, alerts, model_runs
-- ==============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Cyclones Registry
CREATE TABLE IF NOT EXISTS cyclones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(32) UNIQUE NOT NULL,               -- e.g. "BOB-01-2024", "ARB-02-2023"
    name VARCHAR(100) NOT NULL,                    -- e.g. "Remal", "Biparjoy", "Michaung"
    basin VARCHAR(50) NOT NULL DEFAULT 'North Indian Ocean', -- Bay of Bengal / Arabian Sea
    status VARCHAR(50) NOT NULL DEFAULT 'ACTIVE',  -- ACTIVE, DISSIPATED, ARCHIVED
    classification VARCHAR(100) NOT NULL,          -- e.g. "Severe Cyclonic Storm"
    current_lat DOUBLE PRECISION NOT NULL,
    current_lon DOUBLE PRECISION NOT NULL,
    max_sustained_wind_kts DOUBLE PRECISION NOT NULL,
    central_pressure_hpa DOUBLE PRECISION NOT NULL,
    movement_speed_kmh DOUBLE PRECISION DEFAULT 15.0,
    movement_direction_deg DOUBLE PRECISION DEFAULT 340.0,
    risk_level VARCHAR(20) NOT NULL DEFAULT 'MODERATE', -- LOW, MODERATE, HIGH, EXTREME
    risk_score INTEGER NOT NULL DEFAULT 50,
    data_mode VARCHAR(20) NOT NULL DEFAULT 'DEMO',  -- LIVE, DEMO, HISTORICAL
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. Weather Observations (Multi-sensor and In-situ)
CREATE TABLE IF NOT EXISTS weather_observations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cyclone_id UUID REFERENCES cyclones(id) ON DELETE CASCADE,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    sea_surface_temp_c DOUBLE PRECISION,
    air_temperature_c DOUBLE PRECISION,
    relative_humidity_pct DOUBLE PRECISION,
    surface_pressure_hpa DOUBLE PRECISION NOT NULL,
    wind_speed_kts DOUBLE PRECISION NOT NULL,
    wind_direction_deg DOUBLE PRECISION,
    vertical_wind_shear_kts DOUBLE PRECISION,
    source VARCHAR(50) NOT NULL DEFAULT 'OpenWeather', -- OpenWeather, Buoy, In-situ, DemoAdapter
    data_mode VARCHAR(20) NOT NULL DEFAULT 'DEMO',     -- LIVE, DEMO, HISTORICAL
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Satellite Images Metadata
CREATE TABLE IF NOT EXISTS satellite_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cyclone_id UUID REFERENCES cyclones(id) ON DELETE SET NULL,
    sensor VARCHAR(100) NOT NULL DEFAULT 'INSAT-3D/3DR', -- INSAT-3D, GOES-16, Himawari-8
    channel VARCHAR(50) NOT NULL DEFAULT 'IR-10.8um',     -- IR-10.8um, VIS-0.65um, WaterVapor
    image_url TEXT NOT NULL,
    storage_path TEXT,
    min_core_temp_k DOUBLE PRECISION,
    eye_detected BOOLEAN DEFAULT FALSE,
    cdo_symmetry_score DOUBLE PRECISION,
    data_mode VARCHAR(20) NOT NULL DEFAULT 'DEMO',
    captured_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. Predictions (6h, 12h, 24h short-term intensity & trajectory)
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cyclone_id UUID REFERENCES cyclones(id) ON DELETE CASCADE,
    lead_time_hours INTEGER NOT NULL,              -- 6, 12, 24, 48
    predicted_lat DOUBLE PRECISION NOT NULL,
    predicted_lon DOUBLE PRECISION NOT NULL,
    predicted_wind_kts DOUBLE PRECISION NOT NULL,
    predicted_pressure_hpa DOUBLE PRECISION NOT NULL,
    predicted_classification VARCHAR(100) NOT NULL,
    trend VARCHAR(30) NOT NULL DEFAULT 'INTENSIFYING', -- INTENSIFYING, STEADY, WEAKENING
    confidence_score DOUBLE PRECISION NOT NULL,
    model_version VARCHAR(50) NOT NULL DEFAULT 'v1.0',
    data_mode VARCHAR(20) NOT NULL DEFAULT 'DEMO',
    valid_time TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 5. Automated Alerts
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cyclone_id UUID REFERENCES cyclones(id) ON DELETE SET NULL,
    alert_type VARCHAR(50) NOT NULL,               -- RAPID_INTENSIFICATION, LANDFALL_WARNING, GALE_FORCE
    severity VARCHAR(20) NOT NULL,                 -- ADVISORY, WATCH, WARNING, EMERGENCY
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    risk_score INTEGER NOT NULL,
    recipient_channels TEXT[] DEFAULT ARRAY['webhook', 'dashboard'],
    dispatch_status VARCHAR(30) DEFAULT 'SENT',    -- PENDING, SENT, FAILED, DISMISSED
    dispatched_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 6. Model Runs (Inference audit log for Explainable AI & Provenance)
CREATE TABLE IF NOT EXISTS model_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(100) NOT NULL,              -- cyclone_detector_v1, classifier_v1, predictor_v1
    model_version VARCHAR(50) NOT NULL,
    inputs JSONB NOT NULL,
    outputs JSONB NOT NULL,
    explanation JSONB,                             -- SHAP / feature contributions
    data_mode VARCHAR(20) NOT NULL DEFAULT 'DEMO',
    latency_ms DOUBLE PRECISION,
    executed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indices for performance
CREATE INDEX IF NOT EXISTS idx_cyclones_status ON cyclones(status);
CREATE INDEX IF NOT EXISTS idx_weather_recorded_at ON weather_observations(recorded_at);
CREATE INDEX IF NOT EXISTS idx_predictions_cyclone_id ON predictions(cyclone_id);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
CREATE INDEX IF NOT EXISTS idx_model_runs_executed_at ON model_runs(executed_at);
