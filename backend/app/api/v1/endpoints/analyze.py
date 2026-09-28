import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    ForecastHorizon,
    RiskAssessment,
    RiskFactor,
    FeatureExplanation,
)
from app.services.weather_adapter import WeatherAdapter
from app.services.satellite_service import SatelliteService
from app.services.alert_service import alert_service
from app.services.supabase_client import storage_service

from ml.inference.pipeline import inference_pipeline, StructuredPrediction
from ml.data.schemas.unified import UnifiedObservation, DataMode

logger = logging.getLogger("cyclonex.api.analyze")

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_cyclone_system(req: AnalyzeRequest):
    """
    Primary Unified Integration Endpoint for CYCLONEX.
    Fuses multi-source satellite imagery, meteorological telemetry, and historical baselines
    to execute:
      1. Model A Detection
      2. Model B Classification (IMD 8-tier standard)
      3. Model C Short-Term Trajectory & Intensity Prediction (6h, 12h, 24h)
      4. Explainable AI (Feature Attribution)
      5. Decoupled Prototype Risk Index
      6. Supabase & In-Memory Persistence
      7. Automated Emergency Alert Trigger (n8n integration)
    """
    data_sources: List[str] = []
    now_iso = datetime.now(timezone.utc).isoformat()
    
    # 1. Normalize data_mode
    mode_str = (req.data_mode or "DEMO").upper().strip()
    is_live = (mode_str == "LIVE") or req.force_live_weather
    if is_live:
        data_mode = "LIVE"
        enum_mode = DataMode.LIVE
    elif mode_str == "HISTORICAL":
        data_mode = "HISTORICAL"
        enum_mode = DataMode.HISTORICAL
    else:
        data_mode = "DEMO"
        enum_mode = DataMode.DEMO

    # Telemetry and provenance metadata tracking
    temp = req.temperature
    humidity = req.humidity
    pressure = req.pressure
    wind_kmh = req.wind_speed
    wind_kts = req.wind_speed_kts
    wind_heading = req.wind_direction

    weather_obs_time = None
    weather_status = "CONNECTED"
    satellite_obs_time = None
    satellite_source_name = None
    satellite_status = "NOT_REQUESTED"
    sat_image_path = req.satellite_image_path
    sat_image_features = None

    # 2. LIVE MODE: Automated external ingestion with strict failure handling
    if is_live:
        # A. Live Weather Telemetry via OpenWeather
        try:
            weather_obs = await WeatherAdapter.fetch_weather(
                req.latitude,
                req.longitude,
                force_live=True,
                data_mode="LIVE"
            )
        except ValueError as val_err:
            logger.error(f"Live weather failure: {val_err}")
            raise HTTPException(status_code=400, detail=str(val_err))

        # In LIVE mode, auto-populate meteorological telemetry from OpenWeather
        temp = weather_obs.get("temperature_c", 28.0) if temp is None else temp
        humidity = weather_obs.get("humidity_pct", 80.0) if humidity is None else humidity
        pressure = weather_obs.get("pressure_hpa", 1008.0) if pressure is None else pressure
        wind_kts = weather_obs.get("wind_speed_kts", 25.0) if wind_kts is None else wind_kts
        wind_kmh = weather_obs.get("wind_speed_kmh", round(wind_kts * 1.852, 1))
        wind_heading = weather_obs.get("wind_direction_deg", 180.0) if wind_heading is None else wind_heading
        weather_status = weather_obs.get("status", "CONNECTED")
        data_sources.append(weather_obs.get("source", "OpenWeather Current Weather (Live Telemetry)"))

        # B. Live Satellite Telemetry via MOSDAC / ISRO INSAT NRT
        sat_obs = await SatelliteService.fetch_live_satellite(req.latitude, req.longitude)
        if sat_obs.get("available"):
            sat_image_path = sat_obs.get("local_path")
            sat_image_features = sat_obs.get("image_features")
            satellite_obs_time = sat_obs.get("acquisition_timestamp")
            satellite_source_name = sat_obs.get("source")
            satellite_status = "CONNECTED"
            data_sources.append(satellite_source_name)
        else:
            sat_image_path = None
            sat_image_features = None
            satellite_obs_time = None
            satellite_source_name = "MOSDAC INSAT NRT (Unavailable)"
            satellite_status = "UNAVAILABLE"
            data_sources.append(satellite_source_name)

        # C. Authoritative Historical Climatology Reference Baseline
        data_sources.append("HISTORICAL BASELINE — IBTrACS")

    # 3. DEMO and HISTORICAL Modes: Local / In-Situ / Deterministic Execution
    else:
        # Convert units if only one was supplied
        if wind_kts is not None and wind_kmh is None:
            wind_kmh = round(wind_kts * 1.852, 1)
        elif wind_kmh is not None and wind_kts is None:
            wind_kts = round(wind_kmh / 1.852, 1)

        if None in [temp, humidity, pressure, wind_kts]:
            weather_obs = await WeatherAdapter.fetch_weather(
                req.latitude, 
                req.longitude, 
                force_live=False,
                data_mode=data_mode
            )
            if temp is None:
                temp = weather_obs.get("temperature_c", 28.0)
            if humidity is None:
                humidity = weather_obs.get("humidity_pct", 80.0)
            if pressure is None:
                pressure = weather_obs.get("pressure_hpa", 1005.0)
            if wind_kts is None:
                wind_kmh_fetched = weather_obs.get("wind_speed_kmh", 30.0)
                wind_kts = round(wind_kmh_fetched / 1.852, 1)
                wind_kmh = wind_kmh_fetched
            if wind_heading is None:
                wind_heading = weather_obs.get("wind_direction_deg", 340.0)
            
            data_sources.append(weather_obs.get("source", "Meteorological Climatology Model (DEMO ADAPTER)"))
        else:
            data_sources.append("In-Situ Sensor Telemetry")

        weather_obs_time = now_iso
        weather_status = "CONNECTED (DEMO/HISTORICAL)"

        # Satellite attribution for non-live modes
        if req.satellite_image_path:
            data_sources.append(f"Satellite File ({req.satellite_image_path})")
            satellite_status = "DEMO_FILE"
            satellite_source_name = f"Curated Archive ({req.satellite_image_path})"
        elif req.satellite_image:
            data_sources.append("Base64 Ingested Satellite Tile")
            satellite_status = "INGESTED"
            satellite_source_name = "User Ingested Imagery"
        else:
            data_sources.append("Synthetic Proxy Features (INSAT-3D Benchmark)")
            satellite_status = "DEMO_PROXY"
            satellite_source_name = "Synthetic Satellite Calibration Proxy"

        if data_mode == "HISTORICAL":
            data_sources.append("NOAA IBTrACS Benchmark Track")

    # 4. Construct UnifiedObservation for ML Pipeline
    observation_id = str(uuid.uuid4())
    obs = UnifiedObservation(
        observation_id=observation_id,
        timestamp=now_iso,
        latitude=req.latitude,
        longitude=req.longitude,
        temperature=temp,
        humidity=humidity,
        pressure=pressure,
        wind_speed_kts=wind_kts,
        wind_direction=wind_heading,
        image_path=sat_image_path,
        image_base64=req.satellite_image,
        image_features=sat_image_features,
        data_mode=enum_mode,
        source=",".join(data_sources)
    )

    # 5. Execute Full End-to-End ML Pipeline
    # Runs Preprocessing -> Model A -> Model B -> Model C -> XAI -> Risk Engine
    pred: StructuredPrediction = inference_pipeline.predict_observation(obs)

    # 5. Format Forecast Horizons
    forecast_list: List[ForecastHorizon] = []
    for h in pred.multi_horizon_forecast:
        forecast_list.append(
            ForecastHorizon(
                lead_time_hours=h["lead_time_hours"],
                predicted_wind_speed_kts=h["predicted_wind_speed_kts"],
                predicted_wind_speed_kmh=h["predicted_wind_speed_kmh"],
                predicted_pressure_hpa=h["predicted_pressure_hpa"],
                predicted_latitude=h["predicted_latitude"],
                predicted_longitude=h["predicted_longitude"],
                classification=h["predicted_classification"],
                trend=h["trend"],
                confidence=h["confidence"]
            )
        )

    # 6. Format Explainability Attributions
    explanation_list: List[FeatureExplanation] = []
    for item in pred.explanation:
        explanation_list.append(
            FeatureExplanation(
                feature=item.feature,
                value=item.observed_value,
                importance=item.importance_weight,
                impact=item.impact,
                description=item.explanation
            )
        )

    # 7. Format Risk Assessment Object
    risk_factors: List[RiskFactor] = []
    for f in pred.risk.contributing_factors:
        risk_factors.append(
            RiskFactor(
                factor=f["factor"],
                score=f["score"],
                max_score=f["max_score"],
                metric=f["metric"]
            )
        )

    risk_obj = RiskAssessment(
        risk_score=pred.risk.risk_score,
        risk_level=pred.risk.risk_level,
        contributing_factors=risk_factors,
        label=pred.risk.label,
        disclaimer=pred.risk.disclaimer
    )

    # 8. Multi-Source Persistence (Supabase + Local In-Memory Fallback)
    # A. Weather Observation Record
    storage_service.record_weather_observation({
        "latitude": req.latitude,
        "longitude": req.longitude,
        "sea_surface_temp_c": temp,
        "air_temperature_c": temp,
        "relative_humidity_pct": humidity,
        "surface_pressure_hpa": pressure,
        "wind_speed_kts": wind_kts,
        "wind_direction_deg": wind_heading,
        "source": ",".join(data_sources),
        "data_mode": data_mode,
        "recorded_at": now_iso
    })

    # B. Cyclone Entity Upsert
    cyclone_id = req.cyclone_id or f"cyc-{observation_id[:8]}"
    storm_name = req.cyclone_name or (
        f"Storm Cell ({req.latitude:.1f}N, {req.longitude:.1f}E)" if pred.cyclone_detected else "Calm Maritime Area"
    )

    storage_service.upsert_cyclone({
        "id": cyclone_id,
        "code": f"CYC-{observation_id[:6].upper()}",
        "name": storm_name,
        "basin": "Bay of Bengal" if req.longitude > 80.0 else "Arabian Sea",
        "status": "ACTIVE" if pred.cyclone_detected else "DISSIPATED",
        "classification": pred.classification,
        "current_lat": req.latitude,
        "current_lon": req.longitude,
        "max_sustained_wind_kts": wind_kts,
        "central_pressure_hpa": pressure,
        "movement_speed_kmh": 15.0,
        "movement_direction_deg": wind_heading or 340.0,
        "risk_level": pred.risk.risk_level,
        "risk_score": pred.risk.risk_score,
        "data_mode": data_mode,
        "started_at": now_iso,
        "last_updated_at": now_iso
    })

    # C. Prediction Records (for each horizon)
    for fh in forecast_list:
        storage_service.record_prediction({
            "cyclone_id": cyclone_id,
            "lead_time_hours": fh.lead_time_hours,
            "predicted_lat": fh.predicted_latitude,
            "predicted_lon": fh.predicted_longitude,
            "predicted_wind_kts": fh.predicted_wind_speed_kts,
            "predicted_pressure_hpa": fh.predicted_pressure_hpa,
            "predicted_classification": fh.classification,
            "trend": fh.trend,
            "confidence_score": fh.confidence,
            "model_version": pred.model_version,
            "data_mode": data_mode,
            "valid_time": now_iso
        })

    # D. Model Run Audit Log
    storage_service.log_model_run(
        model_name="cyclonex_fusion_v1",
        inputs=req.model_dump(exclude={"satellite_image"}),
        outputs={
            "cyclone_detected": pred.cyclone_detected,
            "classification": pred.classification,
            "risk_score": pred.risk.risk_score,
            "predicted_wind_speed_kts": pred.predicted_wind_speed_kts
        },
        explanation=[e.model_dump() for e in explanation_list]
    )

    # 9. Automated Alert Dispatch if High/Extreme Risk
    if pred.risk.risk_score >= 60 and pred.cyclone_detected:
        await alert_service.dispatch_alert({
            "cyclone_id": cyclone_id,
            "cyclone_name": storm_name,
            "classification": pred.classification,
            "severity": "WARNING" if pred.risk.risk_score < 80 else "EMERGENCY",
            "risk_score": pred.risk.risk_score,
            "risk_level": pred.risk.risk_level,
            "wind_speed_kts": wind_kts,
            "pressure_hpa": pressure,
            "latitude": req.latitude,
            "longitude": req.longitude,
            "message": (
                f"{pred.classification} detected at {req.latitude:.1f}N, {req.longitude:.1f}E. "
                f"Sustained wind: {wind_kts:.1f} kts, Core pressure: {pressure:.1f} hPa. "
                f"Prototype Risk Score: {pred.risk.risk_score}/100 ({pred.risk.risk_level})."
            )
        })

    # 10. Return Canonical Response Contract
    return AnalyzeResponse(
        cyclone_detected=pred.cyclone_detected,
        cyclone_probability=pred.cyclone_probability,
        classification=pred.classification,
        classification_confidence=pred.classification_confidence,
        classification_tier=pred.classification_tier,
        predicted_wind_speed=pred.predicted_wind_speed,
        predicted_wind_speed_kts=pred.predicted_wind_speed_kts,
        predicted_pressure_hpa=pred.predicted_pressure_hpa,
        trend=pred.trend,
        rapid_intensification=pred.rapid_intensification,
        multi_horizon_forecast=forecast_list,
        multi_horizon_predictions=forecast_list,
        risk=risk_obj,
        risk_score=pred.risk.risk_score,
        risk_level=pred.risk.risk_level,
        explanation=explanation_list,
        model_version=pred.model_version,
        data_mode=data_mode,
        sources=data_sources,
        data_sources=data_sources,
        timestamp=now_iso,
        disclaimer=pred.risk.disclaimer,
        current_temperature_c=temp,
        current_humidity_pct=humidity,
        current_pressure_hpa=pressure,
        current_wind_speed_kts=wind_kts,
        current_wind_direction_deg=wind_heading,
        weather_observation_time=weather_obs_time,
        weather_status=weather_status,
        satellite_observation_time=satellite_obs_time,
        satellite_source=satellite_source_name,
        satellite_status=satellite_status
    )


@router.post("/demo", response_model=AnalyzeResponse, tags=["Multi-Source AI Analysis"])
async def run_verified_demo_analysis():
    """
    Guaranteed Hackathon Benchmark Demonstration.
    Runs full AI fusion pipeline on historical Cyclone Remal benchmark telemetry.
    """
    demo_req = AnalyzeRequest(
        latitude=21.4,
        longitude=89.2,
        temperature=28.5,
        humidity=86.0,
        pressure=978.0,
        wind_speed_kts=60.0,
        wind_direction=355.0,
        cyclone_name="Cyclone Remal",
        data_mode="DEMO"
    )
    return await analyze_cyclone_system(demo_req)

