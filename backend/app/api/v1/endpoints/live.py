"""
CYCLONEX — Live Auto-Discovery & Real-Time Intelligence Endpoint
GET /api/v1/live/discover — Public IMD RSMC National Bulletin Discovery
POST /api/v1/live/analyze — Multi-Source Live AI Analysis
Queries IMD / RSMC New Delhi for public National Bulletins, pulls real-time OpenWeather
telemetry and INSAT satellite imagery, and runs multi-source AI fusion inference.
Requires NO manual coordinates from the user and NO IMD API key.
"""

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    LiveAnalyzeRequest,
    LiveAnalyzeResponse,
    LiveDiscoverResponse,
)
from app.services.cyclone_discovery import CycloneDiscoveryService
from app.services.weather_adapter import WeatherAdapter, _sanitize_secret
from app.services.satellite_service import SatelliteService
from app.services.supabase_client import storage_service
from app.services.alert_service import alert_service
from app.config import settings

from ml.inference.pipeline import inference_pipeline, StructuredPrediction
from ml.data.schemas.unified import UnifiedObservation, DataMode

logger = logging.getLogger("cyclonex.live")
router = APIRouter()


@router.get("/live/discover", response_model=LiveDiscoverResponse, tags=["Live Auto Discovery"])
async def live_discover_bulletin(force_refresh: bool = False):
    """
    Public IMD / RSMC National Bulletin Discovery.
    Discovers, downloads, and extracts active tropical systems from public bulletins without requiring an API key.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    try:
        discovery = await CycloneDiscoveryService.discover_latest_bulletin(force_refresh=force_refresh)
    except RuntimeError as re:
        err_msg = str(re)
        if "LIVE SOURCE UNAVAILABLE" in err_msg:
            raise HTTPException(status_code=503, detail="LIVE SOURCE UNAVAILABLE")
        elif "BULLETIN PARSE FAILED" in err_msg:
            raise HTTPException(status_code=502, detail="BULLETIN PARSE FAILED")
        raise HTTPException(status_code=500, detail=err_msg)

    systems = discovery.get("systems", [])
    return LiveDiscoverResponse(
        status="success",
        data_mode="LIVE",
        source="IMD_RSMC_PUBLIC_BULLETIN",
        active_systems=systems,
        message=discovery.get("message") if not discovery.get("active") else f"Found {len(systems)} active system(s)",
        bulletin_url=discovery.get("bulletin_url"),
        timestamp=discovery.get("timestamp", now_iso)
    )


@router.get("/live/system", tags=["Live Auto Discovery"])
async def get_live_system_status():
    """Returns the latest auto-discovered North Indian Ocean system status from IMD RSMC."""
    return await CycloneDiscoveryService.discover_active_system()


@router.post("/live/analyze", response_model=LiveAnalyzeResponse, tags=["Live Auto Discovery"])
async def live_auto_analyze(req: LiveAnalyzeRequest = LiveAnalyzeRequest()):
    """
    Execute full automated end-to-end live analysis.
    1. Discovers latest public IMD/RSMC National Bulletin.
    2. Parses active tropical system coordinates & intensity.
    3. If no active system: returns clean NO_ACTIVE_SYSTEM response.
    4. If active: queries OpenWeather & INSAT telemetry and executes ML pipeline.
    Preserves full source provenance without requiring manual coordinate entry.
    """
    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Discover current active IMD National Bulletin
    try:
        discovery = await CycloneDiscoveryService.discover_latest_bulletin(force_refresh=req.force_refresh)
    except RuntimeError as re:
        err_msg = str(re)
        if "LIVE SOURCE UNAVAILABLE" in err_msg:
            raise HTTPException(status_code=503, detail="LIVE SOURCE UNAVAILABLE")
        elif "BULLETIN PARSE FAILED" in err_msg:
            raise HTTPException(status_code=502, detail="BULLETIN PARSE FAILED")
        raise HTTPException(status_code=500, detail=f"LIVE_SOURCE_ERROR: {err_msg}")

    # 2. If NO active cyclone or disturbance exists
    systems = discovery.get("systems", [])
    if not discovery.get("active", False) or not systems:
        bulletin_url = discovery.get("bulletin_url")
        return LiveAnalyzeResponse(
            data_mode="LIVE",
            status="NO_ACTIVE_SYSTEM",
            message="NO ACTIVE TROPICAL SYSTEM DETECTED",
            system={
                "active": False,
                "message": "NO ACTIVE TROPICAL SYSTEM DETECTED",
                "source": "IMD_RSMC_PUBLIC_BULLETIN",
                "observed_at": discovery.get("timestamp", now_iso),
                "source_url": bulletin_url
            },
            weather=None,
            satellite=None,
            historical_baseline={
                "source": "NOAA IBTrACS",
                "status": "CONNECTED (REFERENCE)"
            },
            analysis=None,
            forecast=None,
            risk=None,
            explanation=None,
            provenance={
                "cyclone_source": "IMD/RSMC Public National Bulletin",
                "weather_source": "OpenWeather (Monitoring Standby)",
                "satellite_source": "IMD INSAT (Monitoring Standby)",
                "historical_source": "NOAA IBTrACS Historical Baseline"
            },
            data_sources=[
                "IMD/RSMC Public National Bulletin",
                "NOAA IBTrACS Historical Baseline"
            ],
            source_timestamp=discovery.get("timestamp", now_iso),
            source_url=bulletin_url,
            timestamp=now_iso,
            disclaimer="NOT AN OFFICIAL METEOROLOGICAL WARNING. LIVE INPUT DATA ≠ OFFICIAL METEOROLOGICAL FORECAST."
        )

    # 3. Active system discovered — extract coordinates and parameters
    active_sys = systems[0]
    lat = float(active_sys["latitude"])
    lon = float(active_sys["longitude"])
    system_name = active_sys.get("system_name") or f"Active System ({active_sys.get('system_type', 'Depression')})"
    system_class = active_sys.get("system_type", "Depression")
    
    current_wind_kmph = active_sys.get("current_wind_kmph")
    imd_wind_kts = round(current_wind_kmph / 1.852, 1) if current_wind_kmph else 30.0
    imd_pressure = active_sys.get("central_pressure_hpa") or 998.0
    source_url = active_sys.get("source_url") or discovery.get("bulletin_url")
    source_ts = active_sys.get("issue_datetime") or discovery.get("timestamp", now_iso)

    # 4. Fetch Live OpenWeather Telemetry at system coordinates
    try:
        weather_obs = await WeatherAdapter.fetch_weather(
            lat,
            lon,
            force_live=True,
            data_mode="LIVE"
        )
    except ValueError as val_err:
        err_msg = str(val_err)
        clean_err = _sanitize_secret(err_msg, settings.OPENWEATHER_API_KEY)
        logger.error(f"Live weather lookup failed in live auto analyze: {clean_err}")
        raise HTTPException(status_code=502, detail=clean_err)

    weather_status = weather_obs.get("status", "CONNECTED")
    temp_c = weather_obs.get("temperature_c")
    humidity_pct = weather_obs.get("humidity_pct")
    surface_pressure = weather_obs.get("pressure_hpa") or imd_pressure
    wind_kts = weather_obs.get("wind_speed_kts") or imd_wind_kts
    wind_deg = weather_obs.get("wind_direction_deg") or 220.0
    weather_obs_time = weather_obs.get("observed_at")

    # 5. Fetch Live INSAT Satellite Product
    sat_obs = await SatelliteService.fetch_live_satellite(lat, lon)
    sat_status = "CONNECTED" if sat_obs.get("available") else "UNAVAILABLE"
    sat_source_name = sat_obs.get("source", "IMD INSAT-3D NRT")
    sat_obs_time = sat_obs.get("acquisition_timestamp")
    sat_features = sat_obs.get("image_features") if sat_obs.get("available") else None
    sat_path = sat_obs.get("local_path") if sat_obs.get("available") else None

    # 6. Execute ML Inference Pipeline
    weather_source_name = (
        weather_obs.get("source", "OpenWeather Current Weather (Live Telemetry)")
        if weather_status == "CONNECTED"
        else "OpenWeather Current Weather (Unconfigured)"
    )
    data_sources = [
        "IMD/RSMC Public National Bulletin",
        weather_source_name,
        sat_source_name if sat_status == "CONNECTED" else "IMD INSAT NRT (Unavailable)",
        "HISTORICAL BASELINE — IBTrACS"
    ]

    observation_id = str(uuid.uuid4())
    obs = UnifiedObservation(
        observation_id=observation_id,
        timestamp=now_iso,
        latitude=lat,
        longitude=lon,
        temperature=temp_c,
        humidity=humidity_pct,
        pressure=surface_pressure,
        wind_speed_kts=wind_kts,
        wind_direction=wind_deg,
        image_path=sat_path,
        image_features=sat_features,
        data_mode=DataMode.LIVE,
        source=",".join(data_sources)
    )

    pred: StructuredPrediction = inference_pipeline.predict_observation(obs)

    # 7. Format Multi-Horizon Predictions
    forecast_list = []
    for h in pred.multi_horizon_forecast:
        forecast_list.append({
            "lead_time_hours": h["lead_time_hours"],
            "predicted_latitude": h["predicted_latitude"],
            "predicted_longitude": h["predicted_longitude"],
            "predicted_wind_speed_kts": h["predicted_wind_speed_kts"],
            "predicted_wind_speed_kmh": h["predicted_wind_speed_kmh"],
            "predicted_pressure_hpa": h["predicted_pressure_hpa"],
            "classification": h.get("predicted_classification") or h.get("classification", pred.classification),
            "trend": h.get("trend", "MAINTAINING"),
            "confidence": h.get("confidence", 0.85)
        })

    explanation_list = [
        {
            "feature": e.feature,
            "value": e.observed_value,
            "importance": e.importance_weight,
            "impact": e.impact,
            "description": e.explanation
        }
        for e in pred.explanation
    ]

    # 8. Persist System & Predictions
    cyclone_id = f"live-{observation_id[:8]}"
    storage_service.record_weather_observation({
        "id": observation_id,
        "cyclone_id": cyclone_id,
        "latitude": lat,
        "longitude": lon,
        "air_temperature_c": temp_c,
        "relative_humidity_pct": humidity_pct,
        "surface_pressure_hpa": surface_pressure,
        "wind_speed_kts": wind_kts,
        "wind_direction_deg": wind_deg,
        "source": ",".join(data_sources),
        "data_mode": "LIVE",
        "recorded_at": now_iso
    })

    storage_service.upsert_cyclone({
        "id": cyclone_id,
        "code": f"LIVE-{observation_id[:6].upper()}",
        "name": system_name,
        "basin": "Bay of Bengal" if lon > 80.0 else "Arabian Sea",
        "status": "ACTIVE" if pred.cyclone_detected else "DISSIPATED",
        "classification": pred.classification,
        "current_lat": lat,
        "current_lon": lon,
        "max_sustained_wind_kts": wind_kts,
        "central_pressure_hpa": surface_pressure,
        "movement_speed_kmh": active_sys.get("movement_speed_kmph") or 15.0,
        "movement_direction_deg": wind_deg,
        "risk_level": pred.risk.risk_level,
        "risk_score": pred.risk.risk_score,
        "data_mode": "LIVE",
        "started_at": source_ts,
        "last_updated_at": now_iso
    })

    # 9. Alert Dispatch if High/Extreme Risk
    if pred.risk.risk_score >= 60 and pred.cyclone_detected:
        await alert_service.dispatch_alert({
            "cyclone_id": cyclone_id,
            "cyclone_name": system_name,
            "classification": pred.classification,
            "severity": "WARNING" if pred.risk.risk_score < 80 else "EMERGENCY",
            "risk_score": pred.risk.risk_score,
            "risk_level": pred.risk.risk_level,
            "wind_speed_kts": wind_kts,
            "pressure_hpa": surface_pressure,
            "latitude": lat,
            "longitude": lon,
            "message": (
                f"{pred.classification} detected at {lat:.1f}N, {lon:.1f}E via IMD RSMC discovery. "
                f"Sustained wind: {wind_kts:.1f} kts, Pressure: {surface_pressure:.1f} hPa. "
                f"Prototype Risk Score: {pred.risk.risk_score}/100 ({pred.risk.risk_level})."
            )
        })

    # 10. Canonical LIVE Response Contract with Provenance
    return LiveAnalyzeResponse(
        data_mode="LIVE",
        status="ACTIVE_SYSTEM",
        message="ACTIVE SYSTEM ANALYZED",
        system={
            "active": True,
            "name": system_name,
            "latitude": lat,
            "longitude": lon,
            "classification": system_class,
            "wind_speed_kts": imd_wind_kts,
            "pressure_hpa": imd_pressure,
            "movement_direction": active_sys.get("movement_direction"),
            "movement_speed_kmh": active_sys.get("movement_speed_kmph"),
            "region": active_sys.get("region"),
            "forecast_intensity": active_sys.get("forecast_intensity"),
            "forecast_text": active_sys.get("forecast_text"),
            "next_bulletin": active_sys.get("next_bulletin"),
            "observed_at": source_ts,
            "source_url": source_url,
            "source": "IMD_RSMC_PUBLIC_BULLETIN"
        },
        weather={
            "status": weather_status,
            "temperature": temp_c,
            "humidity": humidity_pct,
            "pressure": surface_pressure if weather_status == "CONNECTED" else None,
            "wind_speed": wind_kts if weather_status == "CONNECTED" else None,
            "wind_direction": wind_deg if weather_status == "CONNECTED" else None,
            "observed_at": weather_obs_time,
            "source": weather_source_name
        },
        satellite={
            "status": sat_status,
            "source": sat_source_name,
            "product": "INSAT-3D/3DS Asian Sector Infrared (TIR-1 10.8µm)",
            "observed_at": sat_obs_time
        },
        historical_baseline={
            "source": "NOAA IBTrACS",
            "status": "CONNECTED"
        },
        analysis={
            "cyclone_detected": pred.cyclone_detected,
            "cyclone_probability": pred.cyclone_probability,
            "classification": pred.classification,
            "classification_confidence": pred.classification_confidence,
            "classification_tier": pred.classification_tier,
            "predicted_wind_speed_kts": pred.predicted_wind_speed_kts,
            "predicted_pressure_hpa": pred.predicted_pressure_hpa,
            "trend": pred.trend,
            "rapid_intensification": pred.rapid_intensification,
            "model_version": pred.model_version
        },
        forecast=forecast_list,
        risk={
            "risk_score": pred.risk.risk_score,
            "risk_level": pred.risk.risk_level,
            "label": pred.risk.label,
            "contributing_factors": [
                {
                    "factor": f["factor"],
                    "score": f["score"],
                    "max_score": f["max_score"],
                    "metric": f["metric"]
                }
                for f in pred.risk.contributing_factors
            ],
            "disclaimer": pred.risk.disclaimer
        },
        explanation=explanation_list,
        provenance={
            "cyclone_source": "IMD RSMC New Delhi (Public National Bulletin)",
            "weather_source": "OpenWeather Current Weather",
            "satellite_source": sat_source_name if sat_status == "CONNECTED" else "IMD INSAT (Unavailable)",
            "historical_source": "NOAA IBTrACS"
        },
        data_sources=data_sources,
        source_timestamp=source_ts,
        source_url=source_url,
        timestamp=now_iso,
        disclaimer="NOT AN OFFICIAL METEOROLOGICAL WARNING. LIVE INPUT DATA ≠ OFFICIAL METEOROLOGICAL FORECAST."
    )
