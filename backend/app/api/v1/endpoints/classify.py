from fastapi import APIRouter
from app.models.schemas import ClassifyRequest, ClassifyResponse
from app.services.ml_engine import ml_engine

router = APIRouter()

@router.post("/classify", response_model=ClassifyResponse)
def classify_cyclone(req: ClassifyRequest):
    """
    Model B: Authoritative IMD / WMO Cyclone Classification.
    Classifies tropical cyclone patterns strictly into official categories.
    """
    img_features = {
        "cdo_symmetry": req.cdo_symmetry or 0.72,
        "core_temp_k": req.cloud_top_temp_k or 215.0
    }

    class_name, class_abbr, conf, tier = ml_engine.classify_cyclone(
        wind_kts=req.wind_speed_kts,
        pressure_hpa=req.central_pressure_hpa,
        image_features=img_features
    )

    return ClassifyResponse(
        classification=class_name,
        abbreviation=class_abbr,
        classification_confidence=conf,
        wind_speed_kts=req.wind_speed_kts,
        central_pressure_hpa=req.central_pressure_hpa,
        imd_category_tier=tier,
        data_mode="HISTORICAL" if req.latitude is not None else "DEMO",
        model_version="v1.0-classifier"
    )
