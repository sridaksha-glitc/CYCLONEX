from fastapi import APIRouter
from app.models.schemas import DetectRequest, DetectResponse
from app.services.ml_engine import ml_engine

router = APIRouter()

@router.post("/detect", response_model=DetectResponse)
def detect_cyclone(req: DetectRequest):
    """
    Model A: Cyclone Detection.
    Analyzes satellite imagery or infrared proxy metrics to detect cyclonic organization.
    """
    if req.cdo_symmetry is not None and req.infrared_brightness_temp_k is not None:
        features = {
            "cdo_symmetry": req.cdo_symmetry,
            "core_temp_k": req.infrared_brightness_temp_k,
            "spiral_curvature_score": 0.7,
            "eye_feature_present": False,
            "is_synthetic_proxy": True
        }
    else:
        features = ml_engine.extract_image_features(req.satellite_image)

    detected, prob = ml_engine.detect_cyclone(features, wind_kts=35.0, pressure_hpa=998.0)

    return DetectResponse(
        cyclone_detected=detected,
        cyclone_probability=prob,
        cdo_symmetry_score=features["cdo_symmetry"],
        core_temp_k=features["core_temp_k"],
        data_mode="LIVE" if req.satellite_image else "DEMO",
        model_version="v1.0-cv"
    )
