-- ==============================================================================
-- CYCLONEX SEED DATA: Benchmark Tropical Cyclones & Reference Observations
-- Clearly tagged with data_mode: HISTORICAL or DEMO
-- ==============================================================================

-- 1. Cyclone Remal (May 2024, Severe Cyclonic Storm, Bay of Bengal)
INSERT INTO cyclones (
    id, code, name, basin, status, classification, current_lat, current_lon, 
    max_sustained_wind_kts, central_pressure_hpa, movement_speed_kmh, movement_direction_deg, 
    risk_level, risk_score, data_mode, started_at, last_updated_at
) VALUES (
    'a1b2c3d4-e5f6-7890-abcd-ef1234567801',
    'BOB-01-2024',
    'Cyclone Remal',
    'Bay of Bengal',
    'ACTIVE',
    'Severe Cyclonic Storm',
    21.4,
    89.2,
    60.0,
    978.0,
    16.0,
    355.0,
    'HIGH',
    78,
    'HISTORICAL',
    '2024-05-24 12:00:00+00',
    '2024-05-26 18:00:00+00'
) ON CONFLICT (code) DO NOTHING;

-- 2. Cyclone Biparjoy (June 2023, Extremely Severe Cyclonic Storm, Arabian Sea)
INSERT INTO cyclones (
    id, code, name, basin, status, classification, current_lat, current_lon, 
    max_sustained_wind_kts, central_pressure_hpa, movement_speed_kmh, movement_direction_deg, 
    risk_level, risk_score, data_mode, started_at, last_updated_at
) VALUES (
    'a1b2c3d4-e5f6-7890-abcd-ef1234567802',
    'ARB-02-2023',
    'Cyclone Biparjoy',
    'Arabian Sea',
    'ARCHIVED',
    'Extremely Severe Cyclonic Storm',
    22.8,
    68.1,
    90.0,
    954.0,
    12.0,
    45.0,
    'EXTREME',
    92,
    'HISTORICAL',
    '2023-06-06 06:00:00+00',
    '2023-06-15 15:00:00+00'
) ON CONFLICT (code) DO NOTHING;

-- 3. Cyclone Michaung (Dec 2023, Super/Severe Cyclonic Storm, Bay of Bengal)
INSERT INTO cyclones (
    id, code, name, basin, status, classification, current_lat, current_lon, 
    max_sustained_wind_kts, central_pressure_hpa, movement_speed_kmh, movement_direction_deg, 
    risk_level, risk_score, data_mode, started_at, last_updated_at
) VALUES (
    'a1b2c3d4-e5f6-7890-abcd-ef1234567803',
    'BOB-06-2023',
    'Cyclone Michaung',
    'Bay of Bengal',
    'ARCHIVED',
    'Severe Cyclonic Storm',
    15.2,
    80.5,
    55.0,
    986.0,
    14.0,
    350.0,
    'HIGH',
    72,
    'HISTORICAL',
    '2023-12-01 00:00:00+00',
    '2023-12-05 12:00:00+00'
) ON CONFLICT (code) DO NOTHING;

-- 4. Simulated Active Scenario: Tropical Disturbance "Invest 91B"
INSERT INTO cyclones (
    id, code, name, basin, status, classification, current_lat, current_lon, 
    max_sustained_wind_kts, central_pressure_hpa, movement_speed_kmh, movement_direction_deg, 
    risk_level, risk_score, data_mode, started_at, last_updated_at
) VALUES (
    'a1b2c3d4-e5f6-7890-abcd-ef1234567804',
    'INVEST-91B',
    'Invest 91B (Early Stage)',
    'Bay of Bengal',
    'ACTIVE',
    'Deep Depression',
    12.8,
    85.4,
    30.0,
    998.0,
    18.0,
    315.0,
    'MODERATE',
    46,
    'DEMO',
    NOW() - INTERVAL '1 day',
    NOW()
) ON CONFLICT (code) DO NOTHING;

-- Seed Predictions for Active Storms
INSERT INTO predictions (
    cyclone_id, lead_time_hours, predicted_lat, predicted_lon, predicted_wind_kts, 
    predicted_pressure_hpa, predicted_classification, trend, confidence_score, model_version, data_mode, valid_time
) VALUES
('a1b2c3d4-e5f6-7890-abcd-ef1234567801', 6, 21.9, 89.1, 65.0, 974.0, 'Very Severe Cyclonic Storm', 'INTENSIFYING', 0.91, 'v1.0-fusion', 'HISTORICAL', NOW() + INTERVAL '6 hours'),
('a1b2c3d4-e5f6-7890-abcd-ef1234567801', 12, 22.4, 89.3, 70.0, 970.0, 'Very Severe Cyclonic Storm', 'INTENSIFYING', 0.88, 'v1.0-fusion', 'HISTORICAL', NOW() + INTERVAL '12 hours'),
('a1b2c3d4-e5f6-7890-abcd-ef1234567801', 24, 23.2, 89.7, 50.0, 984.0, 'Severe Cyclonic Storm', 'WEAKENING', 0.82, 'v1.0-fusion', 'HISTORICAL', NOW() + INTERVAL '24 hours'),
('a1b2c3d4-e5f6-7890-abcd-ef1234567804', 6, 13.4, 84.8, 35.0, 994.0, 'Cyclonic Storm', 'INTENSIFYING', 0.86, 'v1.0-fusion', 'DEMO', NOW() + INTERVAL '6 hours'),
('a1b2c3d4-e5f6-7890-abcd-ef1234567804', 12, 14.1, 84.2, 42.0, 990.0, 'Cyclonic Storm', 'INTENSIFYING', 0.83, 'v1.0-fusion', 'DEMO', NOW() + INTERVAL '12 hours'),
('a1b2c3d4-e5f6-7890-abcd-ef1234567804', 24, 15.3, 83.4, 52.0, 982.0, 'Severe Cyclonic Storm', 'INTENSIFYING', 0.79, 'v1.0-fusion', 'DEMO', NOW() + INTERVAL '24 hours');

-- Seed Alerts
INSERT INTO alerts (
    cyclone_id, alert_type, severity, title, message, risk_score, recipient_channels, dispatch_status
) VALUES
('a1b2c3d4-e5f6-7890-abcd-ef1234567801', 'LANDFALL_WARNING', 'WARNING', 'Landfall Trajectory Alert: Cyclone Remal', 'Cyclone Remal sustained winds 60 kts. Landfall anticipated near coastal Bengal/Bangladesh delta within 14 hours. High storm surge expected.', 78, ARRAY['webhook', 'dashboard', 'email'], 'SENT'),
('a1b2c3d4-e5f6-7890-abcd-ef1234567804', 'RAPID_INTENSIFICATION', 'WATCH', 'Development Alert: Invest 91B', 'Model C projects intensification from Deep Depression to Cyclonic Storm within 6 hours. Central pressure dropping towards 994 hPa.', 46, ARRAY['dashboard'], 'SENT');
