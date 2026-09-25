from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from app.models.schemas import AnalyzeRequest, AnalyzeResponse, MultiHorizonPrediction
from app.services.weather_adapter import WeatherAdapter
from app.services.ml_engine import ml_engine
from app.services.risk_engine import RiskEngine
from app.services.explainability import ExplainabilityService
from app.services.alert_service import alert_service
from app.services.supabase_client import storage_service

router = APIRouter()

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_cyclone_system(req: AnalyzeRequest):
    """
    Primary Unified Integration Endpoint.
    Fuses multi-source satellite imagery, meteorological telemetry, and climatological models
    to run Detection (Model A), Classification (Model B), Prediction (Model C),
    Explainable AI, and Prototype Risk Index calculation.
    """
    data_sources = []
    data_mode = "DEMO"

    # 1. Resolve Weather Parameters (provided vs fetched)
    temp = req.temperature
    humidity = req.humidity
    pressure = req.pressure
    wind_kmh = req.wind_speed
    wind_heading = req.wind_direction

    if None in [temp, humidity, pressure, wind_kmh]:
        weather_obs = await WeatherAdapter.fetch_weather(
            req.latitude, 
            req.longitude, 
            force_live=req.force_live_weather
        )
        if temp is None: temp = weather_obs["temperature_c"]
        if humidity is None: humidity = weather_obs["humidity_pct"]
        if pressure is None: pressure = weather_obs["pressure_hpa"]
        if wind_kmh is None: wind_kmh = weather_obs["wind_speed_kmh"]
        if wind_heading is None: wind_heading = weather_obs["wind_direction_deg"]
        
        data_sources.append(weather_obs["source"])
        if weather_obs["data_mode"] == "LIVE":
            data_mode = "LIVE"
    else:
        data_sources.append("Direct User In-Situ Input")

    # Unit conversions: km/h to knots
    wind_kts = round(wind_kmh / 1.852, 1)

    # 2. Extract Satellite Features (Model A Feature Extractor)
    image_features = ml_engine.extract_image_features(req.satellite_image)
    if req.satellite_image:
        data_sources.append("Satellite IR/Visible Image (User Provided)")
    else:
        data_sources.append("Synthetic Satellite Proxy Features")

    # 3. Model A: Cyclone Detection
    detected, prob = ml_engine.detect_cyclone(image_features, wind_kts, pressure)

    # 4. Model B: IMD/WMO Multi-Source Classification
    class_name, class_abbr, class_conf, tier_idx = ml_engine.classify_cyclone(
        wind_kts=wind_kts,
        pressure_hpa=pressure,
        image_features=image_features,
        temperature_c=temp,
        humidity_pct=humidity
    )

    # 5. Model C: Short-term 6h/12h/24h Prediction
    pred_res = ml_engine.predict_short_term(
        current_lat=req.latitude,
        current_lon=req.longitude,
        wind_kts=wind_kts,
        pressure_hpa=pressure,
        movement_speed_kmh=15.0,
        movement_direction_deg=wind_heading or 340.0,
        sst=temp
    )

    h12 = pred_res["horizons"][1] # 12h horizon primary
    trend = pred_res["trend"]
    rapid_intensification = pred_res["rapid_intensification"]

    # 6. Prototype Risk Engine
    risk_score, risk_level, breakdown = RiskEngine.calculate_risk(
        wind_speed_kts=wind_kts,
        central_pressure_hpa=pressure,
        trend=trend,
        rapid_intensification=rapid_intensification,
        cdo_symmetry=image_features["cdo_symmetry"],
        confidence=class_conf
    )

    # 7. Explainable AI Feature Attribution
    explanations = ExplainabilityService.generate_explanations(
        wind_kts=wind_kts,
        pressure_hpa=pressure,
        temperature_c=temp,
        humidity_pct=humidity,
        cdo_symmetry=image_features["cdo_symmetry"],
        core_temp_k=image_features["core_temp_k"],
        trend=trend,
        rapid_intensification=rapid_intensification
    )

    # 8. Automated Alert Dispatch if High/Extreme Risk
    if risk_score >= 60:
        await alert_service.dispatch_alert({
            "cyclone_name": req.cyclone_name or f"Track Cell ({req.latitude:.1f}N, {req.longitude:.1f}E)",
            "classification": class_name,
            "severity": "WARNING" if risk_score < 80 else "EMERGENCY",
            "risk_score": risk_score,
            "risk_level": risk_level,
            "wind_speed_kts": wind_kts,
            "pressure_hpa": pressure,
            "latitude": req.latitude,
            "longitude": req.longitude
        })

    # Log model run audit
    storage_service.log_model_run(
        model_name="cyclonex_fusion_v1",
        inputs=req.model_dump(exclude={"satellite_image"}),
        outputs={
            "cyclone_detected": detected,
            "classification": class_name,
            "risk_score": risk_score,
            "predicted_wind_speed": h12["predicted_wind_speed_kmh"]
        }
    )

    return AnalyzeResponse(
        cyclone_detected=detected,
        cyclone_probability=prob,
        classification=class_name,
        classification_confidence=class_conf,
        predicted_wind_speed=h12["predicted_wind_speed_kmh"],
        predicted_wind_speed_kts=h12["predicted_wind_speed_kts"],
        predicted_pressure_hpa=h12["predicted_pressure_hpa"],
        trend=trend,
        risk_score=risk_score,
        risk_level=risk_level,
        explanation=explanations,
        model_version=ml_engine.model_version,
        data_mode=data_mode,
        multi_horizon_predictions=[
            MultiHorizonPrediction(
                lead_time_hours=h["lead_time_hours"],
                predicted_wind_speed_kmh=h["predicted_wind_speed_kmh"],
                predicted_wind_speed_kts=h["predicted_wind_speed_kts"],
                predicted_pressure_hpa=h["predicted_pressure_hpa"],
                predicted_latitude=h["predicted_latitude"],
                predicted_longitude=h["predicted_longitude"],
                classification=h["classification"],
                trend=h["trend"],
                confidence=h["confidence"]
            ) for h in pred_res["horizons"]
        ],
        data_sources=data_sources,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
