"""
CYCLONEX — Public IMD/RSMC National Bulletin Discovery Tests
Validates:
1. Known bulletin test fixture parsing (latitude == 15.6, longitude == 97.6, system_type == "Depression", forecast_intensity contains "Deep Depression").
2. GET /api/v1/live/discover endpoint with active systems.
3. GET /api/v1/live/discover endpoint with tranquil/no systems.
4. POST /api/v1/live/analyze endpoint with live bulletin and mocked OpenWeather.
5. LIVE_SOURCE_ERROR returned when required live source fails (no silent DEMO fallback).
6. Satellite unavailability handling (UNAVAILABLE status, no demo images substituted).
7. LIVE mode never uses historical storm or DEMO data as current.
8. Complete provenance tracking (data_mode == LIVE, data_sources, source_timestamp, source_url).
9. DEMO endpoint remains working and completely separate.
10. Error handling: LIVE SOURCE UNAVAILABLE, BULLETIN PARSE FAILED, NO ACTIVE TROPICAL SYSTEM DETECTED.
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.services.cyclone_discovery import CycloneDiscoveryService

client = TestClient(app)


# 1. Known Bulletin Structure Parser Test
def test_national_bulletin_parser_known_fixture():
    """
    Verify parsing of known National Bulletin test fixture:
    National Bulletin No. 1
    Date: 28.09.2026
    Issue: 0915 IST
    System: Depression
    Latitude: 15.6 N
    Longitude: 97.6 E
    Region: North Andaman Sea and adjoining Myanmar coast
    Forecast: likely to intensify into Deep Depression during next 12 hours
    Movement: north-northwestwards
    """
    fixture = """
National Bulletin No. 1
Date: 28.09.2026
Issue: 0915 IST
System: Depression
Latitude: 15.6 N
Longitude: 97.6 E
Region: North Andaman Sea and adjoining Myanmar coast
Forecast: likely to intensify into Deep Depression during next 12 hours
Movement: north-northwestwards
"""
    result = CycloneDiscoveryService.parse_bulletin_text(fixture, source_url="https://rsmcnewdelhi.imd.gov.in/test.pdf")
    assert result["active"] is True
    assert len(result["systems"]) == 1
    sys = result["systems"][0]

    # Required assertions from prompt
    assert sys["latitude"] == 15.6
    assert sys["longitude"] == 97.6
    assert sys["system_type"] == "Depression"
    assert "Deep Depression" in sys["forecast_intensity"]

    # Exact field assertions
    assert sys["movement_direction"] == "north-northwestwards"
    assert sys["region"] == "North Andaman Sea and adjoining Myanmar coast"
    assert sys["source"] == "IMD_RSMC_PUBLIC_BULLETIN"
    assert sys["data_mode"] == "LIVE"
    assert sys["current_wind_kmph"] is None  # Never invented
    assert sys["central_pressure_hpa"] is None  # Never invented
    assert sys["system_name"] is None  # Never invented


# 2. GET /api/v1/live/discover with active systems
def test_live_discover_endpoint_active_system():
    """Verify GET /api/v1/live/discover returns active systems parsed from public bulletin."""
    mock_discovery = {
        "active": True,
        "systems": [
            {
                "active": True,
                "source": "IMD_RSMC_PUBLIC_BULLETIN",
                "bulletin_number": "1",
                "issue_datetime": "28.09.2026 0915 IST",
                "system_type": "Depression",
                "system_name": None,
                "latitude": 15.6,
                "longitude": 97.6,
                "movement_direction": "north-northwestwards",
                "movement_speed_kmph": None,
                "region": "North Andaman Sea and adjoining Myanmar coast",
                "current_wind_kmph": None,
                "central_pressure_hpa": None,
                "forecast_intensity": "Deep Depression",
                "forecast_text": "likely to intensify into Deep Depression during next 12 hours",
                "next_bulletin": "1230 IST",
                "source_url": "https://rsmcnewdelhi.imd.gov.in/uploads/bulletin1.pdf",
                "data_mode": "LIVE"
            }
        ],
        "source": "IMD_RSMC_PUBLIC_BULLETIN",
        "bulletin_url": "https://rsmcnewdelhi.imd.gov.in/uploads/bulletin1.pdf",
        "timestamp": "2026-09-28T03:45:00Z"
    }

    with patch.object(CycloneDiscoveryService, "discover_latest_bulletin", new_callable=AsyncMock) as mock_disc:
        mock_disc.return_value = mock_discovery

        res = client.get("/api/v1/live/discover")
        assert res.status_code == 200
        data = res.json()

        assert data["status"] == "success"
        assert data["data_mode"] == "LIVE"
        assert data["source"] == "IMD_RSMC_PUBLIC_BULLETIN"
        assert len(data["active_systems"]) == 1
        sys = data["active_systems"][0]
        assert sys["latitude"] == 15.6
        assert sys["longitude"] == 97.6
        assert sys["system_type"] == "Depression"
        assert sys["forecast_intensity"] == "Deep Depression"


# 3. GET /api/v1/live/discover with tranquil conditions
def test_live_discover_endpoint_no_active_system():
    """Verify GET /api/v1/live/discover returns clean empty systems when tranquil."""
    mock_calm = {
        "active": False,
        "systems": [],
        "source": "IMD_RSMC_PUBLIC_BULLETIN",
        "message": "NO ACTIVE TROPICAL SYSTEM DETECTED",
        "bulletin_url": "https://rsmcnewdelhi.imd.gov.in/uploads/No Cyclone.pdf",
        "timestamp": "2026-09-28T04:00:00Z"
    }

    with patch.object(CycloneDiscoveryService, "discover_latest_bulletin", new_callable=AsyncMock) as mock_disc:
        mock_disc.return_value = mock_calm

        res = client.get("/api/v1/live/discover")
        assert res.status_code == 200
        data = res.json()

        assert data["status"] == "success"
        assert data["data_mode"] == "LIVE"
        assert data["source"] == "IMD_RSMC_PUBLIC_BULLETIN"
        assert data["active_systems"] == []
        assert "NO ACTIVE TROPICAL SYSTEM DETECTED" in data["message"]


# 4. POST /api/v1/live/analyze with live bulletin & mocked OpenWeather
def test_live_analyze_endpoint_success():
    """Verify POST /api/v1/live/analyze fuses discovered bulletin coordinates with live weather telemetry."""
    mock_discovery = {
        "active": True,
        "systems": [
            {
                "active": True,
                "source": "IMD_RSMC_PUBLIC_BULLETIN",
                "bulletin_number": "1",
                "issue_datetime": "28.09.2026 0915 IST",
                "system_type": "Depression",
                "system_name": None,
                "latitude": 15.6,
                "longitude": 97.6,
                "movement_direction": "north-northwestwards",
                "movement_speed_kmph": None,
                "region": "North Andaman Sea and adjoining Myanmar coast",
                "current_wind_kmph": None,
                "central_pressure_hpa": None,
                "forecast_intensity": "Deep Depression",
                "forecast_text": "likely to intensify into Deep Depression during next 12 hours",
                "next_bulletin": "1230 IST",
                "source_url": "https://rsmcnewdelhi.imd.gov.in/uploads/bulletin1.pdf",
                "data_mode": "LIVE"
            }
        ],
        "source": "IMD_RSMC_PUBLIC_BULLETIN",
        "bulletin_url": "https://rsmcnewdelhi.imd.gov.in/uploads/bulletin1.pdf",
        "timestamp": "2026-09-28T03:45:00Z"
    }

    mock_weather = {
        "source": "OpenWeather Current Weather (Live Telemetry)",
        "temperature_c": 28.5,
        "humidity_pct": 84.0,
        "pressure_hpa": 998.0,
        "wind_speed_kts": 30.0,
        "wind_direction_deg": 215.0,
        "observed_at": "2026-09-28T03:45:00Z"
    }

    with patch.object(CycloneDiscoveryService, "discover_latest_bulletin", new_callable=AsyncMock) as mock_disc, \
         patch("app.services.weather_adapter.WeatherAdapter.fetch_weather", new_callable=AsyncMock) as mock_w:
        mock_disc.return_value = mock_discovery
        mock_w.return_value = mock_weather

        res = client.post("/api/v1/live/analyze", json={"data_mode": "LIVE"})
        assert res.status_code == 200
        data = res.json()

        assert data["data_mode"] == "LIVE"
        assert data["status"] == "ACTIVE_SYSTEM"
        assert data["system"]["latitude"] == 15.6
        assert data["system"]["longitude"] == 97.6
        assert data["system"]["classification"] == "Depression"

        # Check provenance
        assert "IMD/RSMC Public National Bulletin" in data["data_sources"]
        assert "OpenWeather Current Weather (Live Telemetry)" in data["data_sources"]
        assert data["source_url"] == "https://rsmcnewdelhi.imd.gov.in/uploads/bulletin1.pdf"
        assert data["source_timestamp"] == "28.09.2026 0915 IST"


# 5. LIVE_SOURCE_ERROR returned when required live weather fails (no silent DEMO fallback)
def test_live_analyze_missing_weather_returns_explicit_error():
    """Verify that if live weather retrieval fails, an explicit LIVE_SOURCE_ERROR is returned (never falls back to DEMO)."""
    mock_discovery = {
        "active": True,
        "systems": [
            {
                "active": True,
                "source": "IMD_RSMC_PUBLIC_BULLETIN",
                "latitude": 15.6,
                "longitude": 97.6,
                "system_type": "Depression"
            }
        ],
        "source": "IMD_RSMC_PUBLIC_BULLETIN",
        "bulletin_url": "https://rsmcnewdelhi.imd.gov.in/bulletin.pdf"
    }

    with patch.object(CycloneDiscoveryService, "discover_latest_bulletin", new_callable=AsyncMock) as mock_disc, \
         patch("app.services.weather_adapter.WeatherAdapter.fetch_weather", side_effect=ValueError("LIVE WEATHER UNAVAILABLE: OPENWEATHER_API_KEY is not configured on the backend.")):
        mock_disc.return_value = mock_discovery

        res = client.post("/api/v1/live/analyze", json={"data_mode": "LIVE"})
        assert res.status_code == 400
        detail = res.json()["detail"]
        assert "LIVE_SOURCE_ERROR" in detail
        assert "OPENWEATHER_API_KEY" in detail


# 6. Satellite Unavailability Handling
def test_satellite_unavailability_explicitly_reported():
    """Verify satellite unavailability reports UNAVAILABLE without substituting demo assets."""
    mock_discovery = {
        "active": True,
        "systems": [
            {
                "active": True,
                "source": "IMD_RSMC_PUBLIC_BULLETIN",
                "latitude": 15.6,
                "longitude": 97.6,
                "system_type": "Depression"
            }
        ]
    }
    mock_weather = {
        "source": "OpenWeather Current Weather",
        "temperature_c": 28.0,
        "humidity_pct": 80.0,
        "pressure_hpa": 1000.0,
        "wind_speed_kts": 25.0,
        "wind_direction_deg": 180.0,
        "observed_at": "2026-09-28T03:45:00Z"
    }
    mock_sat_unavail = {
        "source": "IMD INSAT NRT (Unavailable)",
        "acquisition_timestamp": None,
        "available": False
    }

    with patch.object(CycloneDiscoveryService, "discover_latest_bulletin", new_callable=AsyncMock) as mock_disc, \
         patch("app.services.weather_adapter.WeatherAdapter.fetch_weather", new_callable=AsyncMock) as mock_w, \
         patch("app.services.satellite_service.SatelliteService.fetch_live_satellite", new_callable=AsyncMock) as mock_s:
        mock_disc.return_value = mock_discovery
        mock_w.return_value = mock_weather
        mock_s.return_value = mock_sat_unavail

        res = client.post("/api/v1/live/analyze", json={"data_mode": "LIVE"})
        assert res.status_code == 200
        data = res.json()
        assert data["satellite"]["status"] == "UNAVAILABLE"
        assert not any("remal_ir_2024.png" in str(v) for v in data["satellite"].values())


# 7. No active system returns clean NO_ACTIVE_SYSTEM
def test_live_analyze_no_active_system_response():
    """Verify that when no active cyclone is detected, POST /api/v1/live/analyze returns NO_ACTIVE_SYSTEM."""
    mock_calm = {
        "active": False,
        "systems": [],
        "source": "IMD_RSMC_PUBLIC_BULLETIN",
        "message": "NO ACTIVE TROPICAL SYSTEM DETECTED",
        "bulletin_url": "https://rsmcnewdelhi.imd.gov.in/uploads/No Cyclone.pdf",
        "timestamp": "2026-09-28T04:00:00Z"
    }

    with patch.object(CycloneDiscoveryService, "discover_latest_bulletin", new_callable=AsyncMock) as mock_disc:
        mock_disc.return_value = mock_calm

        res = client.post("/api/v1/live/analyze", json={"data_mode": "LIVE"})
        assert res.status_code == 200
        data = res.json()

        assert data["status"] == "NO_ACTIVE_SYSTEM"
        assert data["system"]["active"] is False
        assert data["message"] == "NO ACTIVE TROPICAL SYSTEM DETECTED"
        assert "REMAL" not in str(data)
        assert "AMPHAN" not in str(data)


# 8. Complete Provenance Tracking
def test_live_analyze_provenance_contract():
    """Verify data_mode, data_sources, source_timestamp, and source_url are populated."""
    mock_discovery = {
        "active": True,
        "systems": [
            {
                "active": True,
                "source": "IMD_RSMC_PUBLIC_BULLETIN",
                "latitude": 15.6,
                "longitude": 97.6,
                "system_type": "Depression",
                "issue_datetime": "28.09.2026 0915 IST",
                "source_url": "https://rsmcnewdelhi.imd.gov.in/bulletin1.pdf"
            }
        ],
        "bulletin_url": "https://rsmcnewdelhi.imd.gov.in/bulletin1.pdf",
        "timestamp": "2026-09-28T03:45:00Z"
    }
    mock_weather = {
        "source": "OpenWeather Current Weather",
        "temperature_c": 28.5,
        "humidity_pct": 82.0,
        "pressure_hpa": 998.0,
        "wind_speed_kts": 30.0,
        "wind_direction_deg": 210.0,
        "observed_at": "2026-09-28T03:45:00Z"
    }

    with patch.object(CycloneDiscoveryService, "discover_latest_bulletin", new_callable=AsyncMock) as mock_disc, \
         patch("app.services.weather_adapter.WeatherAdapter.fetch_weather", new_callable=AsyncMock) as mock_w:
        mock_disc.return_value = mock_discovery
        mock_w.return_value = mock_weather

        res = client.post("/api/v1/live/analyze", json={"data_mode": "LIVE"})
        assert res.status_code == 200
        data = res.json()

        assert data["data_mode"] == "LIVE"
        assert "IMD/RSMC Public National Bulletin" in data["data_sources"]
        assert data["source_timestamp"] == "28.09.2026 0915 IST"
        assert data["source_url"] == "https://rsmcnewdelhi.imd.gov.in/bulletin1.pdf"


# 9. DEMO Endpoint Remains Working
def test_demo_endpoint_remains_working():
    """Verify guaranteed hackathon DEMO endpoint operates reliably with Remal benchmark telemetry."""
    res_demo = client.post("/api/v1/demo")
    assert res_demo.status_code == 200
    data = res_demo.json()
    assert data["data_mode"] == "DEMO"
    assert data["cyclone_detected"] is True
    assert data["classification"] is not None
    assert data["risk_score"] > 0
    assert len(data["multi_horizon_forecast"]) == 3

    res_analyze_demo = client.post("/api/v1/analyze", json={"data_mode": "DEMO", "latitude": 21.4, "longitude": 89.2})
    assert res_analyze_demo.status_code == 200
    assert res_analyze_demo.json()["data_mode"] == "DEMO"


# 10. Error Handling: LIVE SOURCE UNAVAILABLE & BULLETIN PARSE FAILED
def test_discovery_error_handling_responses():
    """Verify explicit error handling when public IMD site is down or PDF parse fails."""
    # Test LIVE SOURCE UNAVAILABLE (503)
    with patch.object(CycloneDiscoveryService, "discover_latest_bulletin", side_effect=RuntimeError("LIVE SOURCE UNAVAILABLE")):
        res = client.get("/api/v1/live/discover")
        assert res.status_code == 503
        assert "LIVE SOURCE UNAVAILABLE" in res.json()["detail"]

    # Test BULLETIN PARSE FAILED (502)
    with patch.object(CycloneDiscoveryService, "discover_latest_bulletin", side_effect=RuntimeError("BULLETIN PARSE FAILED")):
        res = client.get("/api/v1/live/discover")
        assert res.status_code == 502
        assert "BULLETIN PARSE FAILED" in res.json()["detail"]
