from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from PIL import Image
import numpy as np

from ml.data.schemas.unified import UnifiedObservation, DataMode
from ml.data.preprocessing import CycloneDataPreprocessor
from ml.model_registry import registry
from ml.models.detector import CycloneDetector
from ml.inference.explainability import CycloneExplainabilityEngine, FeatureAttribution
from ml.risk.risk_engine import CycloneRiskEngine, PrototypeRiskAssessment

class StructuredPrediction(BaseModel):
    """
    Standardized inference output entity for the CYCLONEX ML pipeline.
    """
    cyclone_detected: bool
    cyclone_probability: float
    classification: str
    classification_confidence: float
    classification_tier: int
    predicted_wind_speed: float     # In km/h per primary interface
    predicted_wind_speed_kts: float # In knots
    predicted_pressure_hpa: float
    trend: str                      # INTENSIFYING | STEADY | WEAKENING
    rapid_intensification: bool
    risk: PrototypeRiskAssessment
    explanation: List[FeatureAttribution]
    multi_horizon_forecast: List[Dict[str, Any]]
    model_version: str
    data_mode: str
    timestamp: str

class CycloneInferencePipeline:
    """
    End-to-end inference coordinator executing Models A, B, C, Explainability, and Risk Engine.
    Takes a UnifiedObservation and produces a StructuredPrediction.
    """

    def __init__(self):
        self.detector = registry.load_detector()
        self.classifier = registry.load_classifier()
        self.predictor = registry.load_predictor()
        self.version = "v1.0-production"

    def predict_observation(self, observation: UnifiedObservation) -> StructuredPrediction:
        """
        Executes multi-source fusion inference on the provided observation.
        """
        # 1. Missing value imputation & preprocessing
        clean_obs = CycloneDataPreprocessor.impute_missing_values(observation)

        # 2. Extract or resolve satellite vision features (Model A)
        img_features = clean_obs.image_features or {}
        if clean_obs.image_path:
            try:
                img = Image.open(clean_obs.image_path).convert("L")
                img_features = CycloneDetector.extract_image_features(img)
            except Exception:
                pass

        cdo_sym = float(img_features.get("cdo_symmetry", 0.65))
        core_temp = float(img_features.get("min_brightness_temp_k", 220.0))

        # Model A: Detection
        detected, prob = self.detector.detect({
            "cdo_symmetry": cdo_sym,
            "core_temp_k": core_temp,
            "spiral_curvature": float(img_features.get("spiral_curvature", 0.60)),
            "eye_detected": float(img_features.get("eye_detected", 0.0))
        })

        # 3. Model B: Classification
        feat_vec_b = CycloneDataPreprocessor.extract_feature_vector(clean_obs)
        class_res = self.classifier.classify(feat_vec_b)

        # 4. Model C: Trajectory & Short-Term Prediction
        dt_info = CycloneDataPreprocessor.process_timestamp(clean_obs.timestamp)
        is_season = 1.0 if dt_info["is_cyclone_season"] else 0.0

        # Features for C: [lat, lon, wind_kts, pressure, delta_w_6h, delta_p_6h, forward_speed, forward_heading, sst, is_season]
        feat_vec_c = np.array([
            clean_obs.latitude,
            clean_obs.longitude,
            clean_obs.wind_speed_kts or 30.0,
            clean_obs.pressure or 1005.0,
            5.0,   # baseline delta wind
            -2.0,  # baseline delta pressure
            16.0,  # forward speed km/h
            clean_obs.wind_direction or 345.0,
            clean_obs.temperature or 28.5,
            is_season
        ], dtype=np.float32)

        pred_res = self.predictor.predict(feat_vec_c)

        # 5. Explainable AI Feature Attribution
        wind_kts = clean_obs.wind_speed_kts or 30.0
        pressure_hpa = clean_obs.pressure or 1005.0
        sst = clean_obs.temperature or 28.5
        rh = clean_obs.humidity or 80.0

        explanations = CycloneExplainabilityEngine.attribute_features(
            wind_kts=wind_kts,
            pressure_hpa=pressure_hpa,
            sst_c=sst,
            humidity_pct=rh,
            cdo_symmetry=cdo_sym,
            core_temp_k=core_temp,
            trend=pred_res["trend"],
            rapid_intensification=pred_res["rapid_intensification"]
        )

        # 6. Decoupled Risk Calculation
        risk_assessment = CycloneRiskEngine.evaluate_risk(
            wind_speed_kts=wind_kts,
            central_pressure_hpa=pressure_hpa,
            classification_tier=class_res["tier"],
            trend=pred_res["trend"],
            rapid_intensification=pred_res["rapid_intensification"],
            confidence=class_res["confidence"],
            cdo_symmetry=cdo_sym
        )

        return StructuredPrediction(
            cyclone_detected=detected,
            cyclone_probability=prob,
            classification=class_res["classification"],
            classification_confidence=class_res["confidence"],
            classification_tier=class_res["tier"],
            predicted_wind_speed=pred_res["predicted_wind_speed_kmh"],
            predicted_wind_speed_kts=pred_res["predicted_wind_speed_kts"],
            predicted_pressure_hpa=pred_res["predicted_pressure_hpa"],
            trend=pred_res["trend"],
            rapid_intensification=pred_res["rapid_intensification"],
            risk=risk_assessment,
            explanation=explanations,
            multi_horizon_forecast=pred_res["horizons"],
            model_version=self.version,
            data_mode=clean_obs.data_mode.value,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

# Global pipeline singleton
inference_pipeline = CycloneInferencePipeline()
