import pytest
import numpy as np
from datetime import datetime, timezone

from ml.data.schemas.unified import UnifiedObservation, DataMode
from ml.model_registry import registry
from ml.models.detector import CycloneDetector
from ml.models.classifier import CycloneClassifier, IMD_CATEGORIES
from ml.models.predictor import CyclonePredictor
from ml.inference.pipeline import CycloneInferencePipeline, StructuredPrediction, inference_pipeline
from ml.risk.risk_engine import CycloneRiskEngine, PrototypeRiskAssessment
from ml.inference.explainability import CycloneExplainabilityEngine

# ------------------------------------------------------------------------------
# 1. Model Registry & Loading Tests
# ------------------------------------------------------------------------------
def test_model_registry_list_and_metrics():
    models = registry.list_models()
    assert len(models) == 3

    keys = [m["key"] for m in models]
    assert "model_a" in keys
    assert "model_b" in keys
    assert "model_c" in keys

    metrics = registry.get_metrics()
    assert "models" in metrics
    assert "model_a" in metrics["models"]
    assert "model_b" in metrics["models"]
    assert "model_c" in metrics["models"]

    # Check Model A real metrics
    ma = metrics["models"]["model_a"]
    assert "accuracy" in ma and ma["accuracy"] >= 0.90
    assert "f1_score" in ma
    assert "confusion_matrix" in ma

    # Check Model B real metrics
    mb = metrics["models"]["model_b"]
    assert "accuracy" in mb and mb["accuracy"] >= 0.95
    assert "f1_macro" in mb
    assert len(mb["confusion_matrix"]) == 8 # 8 IMD categories

    # Check Model C real metrics
    mc = metrics["models"]["model_c"]
    assert "mae_knots" in mc and mc["mae_knots"] < 5.0
    assert "rmse_knots" in mc
    assert "r2_score" in mc and mc["r2_score"] >= 0.80

def test_model_loading_artifacts():
    det = registry.load_detector()
    assert isinstance(det, CycloneDetector)
    assert det.classifier is not None

    clf = registry.load_classifier()
    assert isinstance(clf, CycloneClassifier)
    assert clf.classifier is not None

    pred = registry.load_predictor()
    assert isinstance(pred, CyclonePredictor)
    assert pred.regressor is not None

# ------------------------------------------------------------------------------
# 2. Individual Model Unit Tests
# ------------------------------------------------------------------------------
def test_model_a_detection():
    det = registry.load_detector()

    # Cyclone signature (high symmetry, cold core)
    cyclone_feats = {
        "cdo_symmetry": 0.85,
        "core_temp_k": 208.0,
        "spiral_curvature": 0.75,
        "eye_detected": 1.0
    }
    det_res, prob = det.detect(cyclone_feats)
    assert det_res is True
    assert prob >= 0.70

    # Calm / non-cyclone signature
    calm_feats = {
        "cdo_symmetry": 0.20,
        "core_temp_k": 280.0,
        "spiral_curvature": 0.15,
        "eye_detected": 0.0
    }
    calm_res, calm_prob = det.detect(calm_feats)
    assert calm_res is False
    assert calm_prob <= 0.40

def test_model_b_classification():
    clf = registry.load_classifier()

    # Severe Cyclonic Storm (48 - 63 kts)
    vec_scs = np.array([55.0, 25.0, 29.0, 84.0, 0.75, 212.0], dtype=np.float32)
    res_scs = clf.classify(vec_scs)
    assert res_scs["classification"] == "Severe Cyclonic Storm"
    assert res_scs["tier"] == 4
    assert res_scs["abbreviation"] == "SCS"
    assert res_scs["confidence"] >= 0.65

    # Extremely Severe Cyclonic Storm (90 - 119 kts)
    vec_escs = np.array([100.0, 55.0, 29.5, 88.0, 0.90, 202.0], dtype=np.float32)
    res_escs = clf.classify(vec_escs)
    assert res_escs["classification"] == "Extremely Severe Cyclonic Storm"
    assert res_escs["tier"] == 6

def test_model_c_prediction():
    pred = registry.load_predictor()

    # Deepening cyclone features: [lat, lon, wind_kts, pressure, dw6, dp6, speed, heading, sst, is_season]
    vec_c = np.array([18.0, 89.0, 50.0, 985.0, 8.0, -5.0, 16.0, 350.0, 29.5, 1.0], dtype=np.float32)
    res = pred.predict(vec_c)

    assert "predicted_wind_speed_kts" in res
    assert "predicted_pressure_hpa" in res
    assert res["trend"] == "INTENSIFYING"
    assert len(res["horizons"]) == 3
    assert res["horizons"][0]["lead_time_hours"] == 6
    assert res["horizons"][1]["lead_time_hours"] == 12
    assert res["horizons"][2]["lead_time_hours"] == 24

# ------------------------------------------------------------------------------
# 3. Decoupled Risk Engine Tests
# ------------------------------------------------------------------------------
def test_risk_engine_extremes():
    # 1. Catastrophic storm
    extreme_risk = CycloneRiskEngine.evaluate_risk(
        wind_speed_kts=135.0,
        central_pressure_hpa=915.0,
        classification_tier=7,
        trend="INTENSIFYING",
        rapid_intensification=True,
        confidence=0.95,
        cdo_symmetry=0.92
    )
    assert extreme_risk.risk_score >= 85
    assert extreme_risk.risk_level == "EXTREME"
    assert "NOT AN OFFICIAL METEOROLOGICAL WARNING" in extreme_risk.disclaimer

    # 2. Calm / early depression
    calm_risk = CycloneRiskEngine.evaluate_risk(
        wind_speed_kts=15.0,
        central_pressure_hpa=1010.0,
        classification_tier=0,
        trend="STEADY",
        rapid_intensification=False,
        confidence=0.85,
        cdo_symmetry=0.25
    )
    assert calm_risk.risk_score <= 35
    assert calm_risk.risk_level == "LOW"

# ------------------------------------------------------------------------------
# 4. End-to-End Inference Pipeline Tests
# ------------------------------------------------------------------------------
def test_inference_pipeline_execution():
    obs = UnifiedObservation(
        timestamp=datetime.now(timezone.utc),
        latitude=21.4,
        longitude=89.2,
        source="INSAT-3D + NOAA IBTrACS",
        data_mode=DataMode.HISTORICAL,
        cyclone_name="REMAL",
        temperature=28.5,
        humidity=84.0,
        pressure=978.0,
        wind_speed_kts=60.0,
        image_features={"cdo_symmetry": 0.82, "min_brightness_temp_k": 209.0}
    )

    pred: StructuredPrediction = inference_pipeline.predict_observation(obs)

    assert isinstance(pred, StructuredPrediction)
    assert pred.cyclone_detected is True
    assert pred.cyclone_probability >= 0.70
    assert pred.classification == "Severe Cyclonic Storm"
    assert pred.classification_confidence >= 0.65
    assert pred.predicted_wind_speed > 0
    assert pred.predicted_wind_speed_kts > 0
    assert pred.predicted_pressure_hpa < 1000.0
    assert pred.trend in ["INTENSIFYING", "STEADY", "WEAKENING"]
    assert pred.model_version == "v1.0-production"
    assert pred.data_mode == "HISTORICAL"

    # Risk object checks
    assert isinstance(pred.risk, PrototypeRiskAssessment)
    assert pred.risk.risk_level in ["MODERATE", "HIGH", "EXTREME"]
    assert len(pred.risk.contributing_factors) >= 4

    # Explainability checks
    assert len(pred.explanation) >= 3
    assert pred.explanation[0].impact in ["ESCALATING", "MITIGATING", "NEUTRAL"]
    assert pred.explanation[0].importance_weight > 0.0
