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
    assert data["status"] == "DISPATCHED"
    assert data["risk_score"] == 68
