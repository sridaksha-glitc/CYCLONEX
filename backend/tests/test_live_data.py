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

import json
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.services.cyclone_discovery import CycloneDiscoveryService
from app.services.weather_adapter import WeatherAdapter

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


# 5. OpenWeather Key Configured
@pytest.mark.anyio
async def test_openweather_key_configured():
    """Verify WeatherAdapter and /live/analyze when OPENWEATHER_API_KEY is configured."""
    dummy_key = "test_configured_key_12345"
    mock_payload = {
        "coord": {"lon": 97.6, "lat": 15.6},
        "weather": [{"id": 500, "main": "Rain", "description": "light rain"}],
        "main": {"temp": 29.5, "humidity": 84.0, "pressure": 996.0},
        "wind": {"speed": 15.0, "deg": 210.0},
        "clouds": {"all": 88},
        "name": "Mawlamyine",
        "dt": 1727500000
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_payload

    with patch.object(settings, "OPENWEATHER_API_KEY", dummy_key):
        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_resp
            obs = await WeatherAdapter.fetch_weather(15.6, 97.6, force_live=True, data_mode="LIVE")
            assert obs["status"] == "CONNECTED"
            assert obs["data_mode"] == "LIVE"
            assert obs["temperature_c"] == 29.5
            assert obs["humidity_pct"] == 84.0
            assert obs["pressure_hpa"] == 996.0
            assert obs["wind_speed_kts"] == round(15.0 * 1.94384, 1)
            assert obs["source"] == "OpenWeather Current Weather (Live Telemetry)"

    # Also verify live/analyze endpoint fuses live weather properly
    mock_discovery = {
        "active": True,
        "systems": [
            {
                "active": True,
                "source": "IMD_RSMC_PUBLIC_BULLETIN",
                "latitude": 15.6,
                "longitude": 97.6,
                "system_type": "Depression",
                "issue_datetime": "28.09.2026 0915 IST"
            }
        ],
        "bulletin_url": "https://rsmcnewdelhi.imd.gov.in/uploads/bulletin1.pdf"
    }
    with patch.object(settings, "OPENWEATHER_API_KEY", dummy_key):
        with patch.object(CycloneDiscoveryService, "discover_latest_bulletin", new_callable=AsyncMock) as mock_disc, \
             patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_disc.return_value = mock_discovery
            mock_get.return_value = mock_resp

            res = client.post("/api/v1/live/analyze", json={"data_mode": "LIVE"})
            assert res.status_code == 200
            data = res.json()
            assert data["weather"]["status"] == "CONNECTED"
            assert data["weather"]["temperature"] == 29.5
            assert data["data_mode"] == "LIVE"


# 6. OpenWeather Key Missing
@pytest.mark.anyio
async def test_openweather_key_missing_preserves_cyclone_info():
    """Verify that when OPENWEATHER_API_KEY is missing, OPENWEATHER_NOT_CONFIGURED status is returned without fake data, and IMD discovered cyclone telemetry is preserved."""
    with patch.object(settings, "OPENWEATHER_API_KEY", ""):
        # Weather adapter returns clear unconfigured status without fake data
        obs = await WeatherAdapter.fetch_weather(15.6, 97.6, force_live=True, data_mode="LIVE")
        assert obs["status"] == "OPENWEATHER_NOT_CONFIGURED"
        assert obs["temperature_c"] is None
        assert obs["humidity_pct"] is None
        assert obs["pressure_hpa"] is None
        assert obs["wind_speed_kts"] is None
        assert obs["wind_speed_kmh"] is None

        # End-to-end endpoint preserves discovered bulletin cyclone info
        mock_discovery = {
            "active": True,
            "systems": [
                {
                    "active": True,
                    "source": "IMD_RSMC_PUBLIC_BULLETIN",
                    "bulletin_number": "1",
                    "issue_datetime": "28.09.2026 0915 IST",
                    "system_type": "Depression",
                    "latitude": 15.6,
                    "longitude": 97.6,
                    "region": "North Andaman Sea",
                    "forecast_intensity": "Deep Depression",
                    "source_url": "https://rsmcnewdelhi.imd.gov.in/bulletin1.pdf"
                }
            ],
            "bulletin_url": "https://rsmcnewdelhi.imd.gov.in/bulletin1.pdf",
            "timestamp": "2026-09-28T03:45:00Z"
        }
        with patch.object(CycloneDiscoveryService, "discover_latest_bulletin", new_callable=AsyncMock) as mock_disc:
            mock_disc.return_value = mock_discovery
            res = client.post("/api/v1/live/analyze", json={"data_mode": "LIVE"})
            assert res.status_code == 200
            data = res.json()

            # Status and telemetry of weather
            assert data["weather"]["status"] == "OPENWEATHER_NOT_CONFIGURED"
            assert data["weather"]["temperature"] is None
            assert data["weather"]["humidity"] is None
            assert data["weather"]["wind_speed"] is None

            # Discovered IMD cyclone is preserved intact
            assert data["data_mode"] == "LIVE"
            assert data["status"] == "ACTIVE_SYSTEM"
            assert data["system"]["active"] is True
            assert data["system"]["latitude"] == 15.6
            assert data["system"]["longitude"] == 97.6
            assert data["system"]["classification"] == "Depression"
            assert data["system"]["forecast_intensity"] == "Deep Depression"
            assert data["system"]["source"] == "IMD_RSMC_PUBLIC_BULLETIN"


# 7. OpenWeather API Failure
def test_openweather_api_failure_returns_source_error():
    """Verify that if OpenWeather API returns an error, OPENWEATHER_SOURCE_ERROR is returned (never silently switches to DEMO)."""
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

    with patch.object(settings, "OPENWEATHER_API_KEY", "dummy_failing_key"), \
         patch.object(CycloneDiscoveryService, "discover_latest_bulletin", new_callable=AsyncMock) as mock_disc, \
         patch("app.services.weather_adapter.WeatherAdapter.fetch_weather", side_effect=ValueError("OPENWEATHER_SOURCE_ERROR: OpenWeather API returned HTTP 401 (Unauthorized).")):
        mock_disc.return_value = mock_discovery

        res = client.post("/api/v1/live/analyze", json={"data_mode": "LIVE"})
        assert res.status_code == 502
        detail = res.json()["detail"]
        assert "OPENWEATHER_SOURCE_ERROR" in detail
        assert "DEMO" not in detail


# 8. API Key is Never Exposed in Response JSON
def test_openweather_key_never_exposed_in_response_json():
    """Verify that the secret API key is never exposed in response JSON under success, error, or unconfigured states."""
    secret_key = "CYCLONEX_CONFIDENTIAL_SECRET_TOKEN_DO_NOT_LEAK"

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
        "bulletin_url": "https://rsmcnewdelhi.imd.gov.in/bulletin.pdf"
    }

    # Case A: Successful call
    mock_weather = {
        "status": "CONNECTED",
        "temperature_c": 28.5,
        "humidity_pct": 80.0,
        "pressure_hpa": 1000.0,
        "wind_speed_kts": 30.0,
        "wind_direction_deg": 220.0,
        "source": "OpenWeather Current Weather (Live Telemetry)",
        "observed_at": "2026-09-28T12:00:00Z"
    }
    with patch.object(settings, "OPENWEATHER_API_KEY", secret_key), \
         patch.object(CycloneDiscoveryService, "discover_latest_bulletin", new_callable=AsyncMock) as mock_disc, \
         patch("app.services.weather_adapter.WeatherAdapter.fetch_weather", new_callable=AsyncMock) as mock_w:
        mock_disc.return_value = mock_discovery
        mock_w.return_value = mock_weather

        res = client.post("/api/v1/live/analyze", json={"data_mode": "LIVE"})
        assert res.status_code == 200
        assert secret_key not in res.text
        assert secret_key not in json.dumps(res.json())

    # Case B: Error state (502)
    with patch.object(settings, "OPENWEATHER_API_KEY", secret_key), \
         patch.object(CycloneDiscoveryService, "discover_latest_bulletin", new_callable=AsyncMock) as mock_disc, \
         patch("app.services.weather_adapter.WeatherAdapter.fetch_weather", side_effect=ValueError(f"OPENWEATHER_SOURCE_ERROR: connection refused while calling with {secret_key}")):
        mock_disc.return_value = mock_discovery

        res = client.post("/api/v1/live/analyze", json={"data_mode": "LIVE"})
        assert res.status_code == 502
        assert secret_key not in res.text
        assert secret_key not in json.dumps(res.json())
        assert "[REDACTED]" in res.json()["detail"]


# 9. API Key is Never Printed in Logs
@pytest.mark.anyio
async def test_openweather_key_never_printed_in_logs(caplog):
    """Verify that the secret API key is scrubbed by SensitiveDataFilter and never printed in logs."""
    import logging
    secret_key = "ULTRA_CONFIDENTIAL_KEY_777888999"

    with caplog.at_level(logging.DEBUG):
        with patch.object(settings, "OPENWEATHER_API_KEY", secret_key):
            with patch("httpx.AsyncClient.get", side_effect=RuntimeError(f"HTTP connection failed: appid={secret_key}")):
                with pytest.raises(ValueError):
                    await WeatherAdapter.fetch_weather(15.6, 97.6, force_live=True, data_mode="LIVE")

    assert secret_key not in caplog.text


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
