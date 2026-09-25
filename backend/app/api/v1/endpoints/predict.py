from fastapi import APIRouter
from app.models.schemas import PredictRequest, PredictResponse
from app.services.ml_engine import ml_engine

router = APIRouter()

@router.post("/predict", response_model=PredictResponse)
def predict_cyclone(req: PredictRequest):
    """
    Model C: Short-term (6h, 12h, 24h) Intensity & Track Progression.
    """
    lead_time = req.lead_time_hours or 12
    pred_res = ml_engine.predict_short_term(
        current_lat=req.latitude,
        current_lon=req.longitude,
        wind_kts=req.wind_speed_kts,
        pressure_hpa=req.pressure_hpa,
        movement_speed_kmh=req.movement_speed_kmh or 15.0,
        movement_direction_deg=req.movement_direction_deg or 340.0,
        delta_p_6h=req.delta_pressure_6h or -2.0,
        delta_w_6h=req.delta_wind_6h or 5.0
    )

    # Pick matching horizon or default to 12h
    horizon = pred_res["horizons"][1]
    for h in pred_res["horizons"]:
        if h["lead_time_hours"] == lead_time:
            horizon = h
            break

    return PredictResponse(
        lead_time_hours=horizon["lead_time_hours"],
        predicted_wind_speed_kts=horizon["predicted_wind_speed_kts"],
        predicted_wind_speed_kmh=horizon["predicted_wind_speed_kmh"],
        predicted_pressure_hpa=horizon["predicted_pressure_hpa"],
        predicted_latitude=horizon["predicted_latitude"],
        predicted_longitude=horizon["predicted_longitude"],
        trend=horizon["trend"],
        confidence_score=horizon["confidence"],
        rapid_intensification_flag=pred_res["rapid_intensification"],
        data_mode="DEMO",
        model_version="v1.0-predictor"
    )
