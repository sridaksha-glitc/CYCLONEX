import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert "version" in data

def test_api_v1_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert "subsystems" in data
    assert "ml_engine" in data["subsystems"]
    assert "weather_adapter" in data["subsystems"]

def test_analyze_endpoint_primary():
    payload = {
        "latitude": 13.5,
        "longitude": 80.2,
        "temperature": 28.4,
        "humidity": 84,
        "pressure": 978,
        "wind_speed": 110,
        "wind_direction": 180,
        "satellite_image": None
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    # Assert all required keys per problem specification
    assert "cyclone_detected" in data
    assert "cyclone_probability" in data
    assert "classification" in data
    assert "classification_confidence" in data
    assert "predicted_wind_speed" in data
    assert "trend" in data
    assert "risk_score" in data
    assert "risk_level" in data
    assert "explanation" in data
    assert "model_version" in data
    assert "data_mode" in data

    # Verify types
    assert isinstance(data["cyclone_detected"], bool)
    assert isinstance(data["risk_score"], int)
    assert data["risk_level"] in ["LOW", "MODERATE", "HIGH", "EXTREME"]
    assert len(data["explanation"]) > 0

def test_detect_endpoint():
    payload = {
        "latitude": 13.5,
        "longitude": 80.2,
        "cdo_symmetry": 0.85,
        "infrared_brightness_temp_k": 210.0
    }
    response = client.post("/api/v1/detect", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["cyclone_detected"] is True
    assert data["cyclone_probability"] > 0.5

def test_classify_endpoint():
    payload = {
        "wind_speed_kts": 55.0,
        "central_pressure_hpa": 985.0
    }
    response = client.post("/api/v1/classify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["classification"] == "Severe Cyclonic Storm"
    assert data["abbreviation"] == "SCS"

def test_predict_endpoint():
    payload = {
        "latitude": 21.4,
        "longitude": 89.2,
        "wind_speed_kts": 60.0,
        "pressure_hpa": 978.0,
        "lead_time_hours": 12
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "predicted_wind_speed_kts" in data
    assert "predicted_latitude" in data
    assert "trend" in data

def test_get_cyclones():
    response = client.get("/api/v1/cyclones")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 4
    assert data["active_count"] >= 2

def test_get_single_cyclone():
    response = client.get("/api/v1/cyclones/BOB-01-2024")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Cyclone Remal"
    assert data["classification"] == "Severe Cyclonic Storm"

def test_get_history():
    response = client.get("/api/v1/history")
    assert response.status_code == 200
    data = response.json()
    assert data["total_records"] >= 5
    assert data["data_mode"] == "HISTORICAL"

def test_trigger_alert():
    payload = {
        "cyclone_name": "Test Storm",
        "classification": "Cyclonic Storm",
        "severity": "WARNING",
        "risk_score": 68,
        "risk_level": "HIGH",
        "wind_speed_kts": 45.0,
        "pressure_hpa": 990.0,
        "latitude": 15.0,
        "longitude": 88.0
    }
    response = client.post("/api/v1/alerts", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["DISPATCHED", "SENT", "LOGGED_LOCALLY"]
    assert data["risk_score"] == 68


# ==============================================================================
# PHASE 3: END-TO-END INTEGRATION TEST SUITE (STEP 14)
# ==============================================================================

def test_analyze_demo_mode_input():
    payload = {
        "latitude": 12.8,
        "longitude": 85.4,
        "temperature": 29.5,
        "humidity": 82.0,
        "pressure": 998.0,
        "wind_speed_kts": 30.0,
        "wind_direction": 315.0,
        "cyclone_name": "Invest 91B",
        "data_mode": "DEMO"
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["data_mode"] == "DEMO"
    assert data["cyclone_detected"] is True
    assert "risk" in data
    assert data["risk"]["label"] == "CYCLONEX PROTOTYPE RISK INDEX"
    assert "NOT AN OFFICIAL METEOROLOGICAL WARNING" in data["risk"]["disclaimer"]

def test_analyze_historical_mode_input():
    payload = {
        "latitude": 21.4,
        "longitude": 89.2,
        "temperature": 28.5,
        "humidity": 86.0,
        "pressure": 978.0,
        "wind_speed_kts": 60.0,
        "wind_direction": 355.0,
        "cyclone_name": "Cyclone Remal",
        "data_mode": "HISTORICAL"
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["data_mode"] == "HISTORICAL"
    assert "NOAA IBTrACS Benchmark Track" in data["sources"]
    assert data["classification"] == "Severe Cyclonic Storm"
    assert data["classification_tier"] == 4

def test_analyze_invalid_input_validation():
    # Latitude > 90.0
    payload = {
        "latitude": 105.0,
        "longitude": 80.2,
        "pressure": 980.0,
        "wind_speed": 100.0
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 422

    # Pressure < 850.0
    payload_bad_pressure = {
        "latitude": 15.0,
        "longitude": 80.0,
        "pressure": 400.0
    }
    response_bad_pressure = client.post("/api/v1/analyze", json=payload_bad_pressure)
    assert response_bad_pressure.status_code == 422

def test_analyze_canonical_response_schema():
    payload = {
        "latitude": 18.0,
        "longitude": 85.0,
        "temperature": 28.0,
        "humidity": 85.0,
        "pressure": 975.0,
        "wind_speed_kts": 65.0,
        "data_mode": "DEMO"
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Step 4 canonical fields check
    expected_fields = [
        "cyclone_detected", "cyclone_probability", "classification",
        "classification_confidence", "classification_tier", "predicted_wind_speed_kts",
        "predicted_pressure_hpa", "trend", "rapid_intensification",
        "multi_horizon_forecast", "risk", "explanation", "model_version",
        "data_mode", "sources", "timestamp"
    ]
    for field in expected_fields:
        assert field in data, f"Missing required canonical field: {field}"

    assert len(data["multi_horizon_forecast"]) == 3
    horizons = [h["lead_time_hours"] for h in data["multi_horizon_forecast"]]
    assert horizons == [6, 12, 24]

def test_analyze_risk_assessment_details():
    payload = {
        "latitude": 22.0,
        "longitude": 68.0,
        "pressure": 955.0,
        "wind_speed_kts": 90.0,
        "data_mode": "DEMO"
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    risk = data["risk"]

    assert isinstance(risk["risk_score"], int)
    assert 0 <= risk["risk_score"] <= 100
    assert risk["risk_level"] in ["LOW", "MODERATE", "HIGH", "EXTREME"]
    assert len(risk["contributing_factors"]) >= 4
    for f in risk["contributing_factors"]:
        assert "factor" in f
        assert "score" in f
        assert "max_score" in f
        assert "metric" in f

def test_analyze_explainability_attribution():
    payload = {
        "latitude": 15.0,
        "longitude": 88.0,
        "pressure": 970.0,
        "wind_speed_kts": 70.0,
        "data_mode": "DEMO"
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    explanations = data["explanation"]
    assert len(explanations) >= 3

    for item in explanations:
        assert "feature" in item
        assert "importance" in item
        assert item["impact"] in ["ESCALATING", "MITIGATING", "NEUTRAL"]
        assert len(item["description"]) > 5

def test_analyze_persistence_behavior():
    from app.services.supabase_client import storage_service
    initial_weather_count = len(storage_service.get_weather_observations())
    initial_pred_count = len(storage_service.get_predictions())

    payload = {
        "latitude": 16.5,
        "longitude": 82.5,
        "pressure": 985.0,
        "wind_speed_kts": 50.0,
        "cyclone_name": "Persisted Test Storm",
        "data_mode": "DEMO"
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200

    new_weather_count = len(storage_service.get_weather_observations())
    new_pred_count = len(storage_service.get_predictions())

    assert new_weather_count > initial_weather_count
    assert new_pred_count > initial_pred_count

def test_analyze_weather_omission_fallback():
    # Do not supply temperature, humidity, pressure, or wind_speed
    payload = {
        "latitude": 13.0,
        "longitude": 80.0
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["predicted_wind_speed_kts"] is not None
    assert data["predicted_pressure_hpa"] is not None
    assert any("OpenWeather" in s or "Meteorological Climatology" in s for s in data["sources"])


def test_analyze_satellite_fallback():
    # Omitting satellite image triggers synthetic/proxy feature extraction seamlessly
    payload = {
        "latitude": 14.0,
        "longitude": 82.0,
        "pressure": 990.0,
        "wind_speed_kts": 45.0,
        "satellite_image": None
    }
    response = client.post("/api/v1/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["cyclone_detected"] is True
    assert any("Synthetic Proxy" in s for s in data["sources"])

