import os
import json
import pytest
import numpy as np
from fastapi.testclient import TestClient

from backend.app.main import app
from ml.model_registry import registry
from ml.validation.benchmark import ScientificBenchmarkExperiment

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# ------------------------------------------------------------------------------
# 1. Feature Exclusion & Leakage Safety Tests
# ------------------------------------------------------------------------------
def test_wind_kts_excluded_from_scientific_benchmark_features():
    """
    Verify that wind_kts, wind_kmh, and any target-derived wind speed features
    are strictly excluded from the scientific benchmark inputs.
    """
    audit_path = os.path.join(REPO_ROOT, "ml", "validation", "feature_audit.json")
    results_path = os.path.join(REPO_ROOT, "ml", "validation", "scientific_benchmark_results.json")

    assert os.path.exists(audit_path), "ml/validation/feature_audit.json must exist"
    assert os.path.exists(results_path), "ml/validation/scientific_benchmark_results.json must exist"

    with open(audit_path, "r", encoding="utf-8") as f:
        audit = json.load(f)

    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    # 1. Verify excluded features list in both artifacts
    audit_excluded = [item["feature"] for item in audit.get("excluded_features", [])]
    results_excluded = results.get("excluded_features", [])

    assert any("wind_kts" in f for f in audit_excluded), "wind_kts must be explicitly listed in audit excluded_features"
    assert "wind_kts" in results_excluded, "wind_kts must be explicitly listed in results excluded_features"

    # 2. Verify features_used contains zero wind references
    benchmark_features = results.get("features_used", [])
    assert len(benchmark_features) > 0, "Benchmark must have features"
    for feat in benchmark_features:
        assert "wind" not in feat.lower(), f"Feature '{feat}' leaks wind speed"
        assert "wmo" not in feat.lower(), f"Feature '{feat}' leaks WMO wind"

    # 3. Verify benchmark experiment runtime feature generation
    exp = ScientificBenchmarkExperiment()
    X, y, cyclone_names, obs_ids = exp.load_data()
    # Check that feature vector dimension matches features_used
    assert X.shape[1] == len(benchmark_features)
    assert X.shape[0] == len(y)

# ------------------------------------------------------------------------------
# 2. Cyclone Group-Based Splitting Tests (Leave-One-Cyclone-Out)
# ------------------------------------------------------------------------------
def test_cyclone_groups_never_overlap_between_train_and_test():
    """
    Mathematically prove that no cyclone appears in both train and test partitions
    for any fold in Leave-One-Cyclone-Out cross validation.
    """
    results_path = os.path.join(REPO_ROOT, "ml", "validation", "scientific_benchmark_results.json")
    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    folds = results.get("folds", [])
    assert len(folds) >= 4, "Must have at least 4 LOCO folds for NIO storms"

    all_cyclones = results["dataset"]["cyclones"]

    for fold in folds:
        held_out = fold["held_out_cyclone"]
        train_cyclones = fold["train_cyclones"]

        # Crucial group-splitting assertion:
        assert held_out not in train_cyclones, f"Leakage detected: {held_out} present in training partition of {fold['fold_id']}"
        overlap = set(train_cyclones).intersection({held_out})
        assert len(overlap) == 0, f"Intersection between train and test cyclones must be empty, got {overlap}"

        # Verify train + test equals full cyclone set
        assert set(train_cyclones) | {held_out} == set(all_cyclones)
        assert fold["train_samples"] + fold["test_samples"] == results["dataset"]["total_observations"]

# ------------------------------------------------------------------------------
# 3. Results Artifact Integrity & Schema Tests
# ------------------------------------------------------------------------------
def test_results_artifact_is_valid():
    """
    Validate that scientific_benchmark_results.json is properly structured,
    non-empty, contains valid numerical metrics, and includes comparison blocks.
    """
    results_path = os.path.join(REPO_ROOT, "ml", "validation", "scientific_benchmark_results.json")
    with open(results_path, "r", encoding="utf-8") as f:
        results = json.load(f)

    assert results["experiment"] == "wind_excluded_cyclone_level_classification"
    assert results["status"] == "COMPLETED"
    assert results["split_strategy"] == "LEAVE_ONE_CYCLONE_OUT (LOCO)"

    metrics = results["aggregate_metrics"]
    assert 0.0 <= metrics["out_of_fold_accuracy"] <= 1.0
    assert 0.0 <= metrics["precision_macro"] <= 1.0
    assert 0.0 <= metrics["recall_macro"] <= 1.0
    assert 0.0 <= metrics["f1_macro"] <= 1.0
    assert len(metrics["confusion_matrix"]) == 8

    # Verify confusion matrix totals and adjacent-tier error diagnostics
    conf_mat = np.array(metrics["confusion_matrix"])
    total_obs = int(conf_mat.sum())
    correct = int(np.trace(conf_mat))
    errors = total_obs - correct

    assert total_obs == 26, f"Expected 26 total observations, got {total_obs}"
    assert correct == 7, f"Expected 7 correct predictions, got {correct}"
    assert errors == 19, f"Expected 19 errors, got {errors}"
    assert metrics["adjacent_tier_errors"] == 13, f"Expected 13 adjacent-tier errors, got {metrics['adjacent_tier_errors']}"
    assert round(metrics["adjacent_tier_agreement_among_errors"], 3) == 0.684
    assert round(metrics["exact_or_adjacent_agreement"], 3) == 0.769

    # Verify comparison section
    comparison = results["comparison"]
    assert "production_calibrated_benchmark" in comparison
    assert "scientific_validation_experiment" in comparison
    assert comparison["production_calibrated_benchmark"]["label"] == "DEFINITIONALLY LEAKED / CALIBRATION BENCHMARK"
    assert "SCIENTIFIC VALIDATION EXPERIMENT" in comparison["scientific_validation_experiment"]["label"]

    # Verify limitations section
    assert len(results["scientific_limitations"]) >= 2

# ------------------------------------------------------------------------------
# 4. Honesty & Insufficient Data Handling Tests
# ------------------------------------------------------------------------------
def test_no_fabricated_result_when_data_is_insufficient():
    """
    Verify that when empirical data is insufficient (e.g., fewer than 2 cyclones),
    the experiment returns status 'INSUFFICIENT_DATA' and does not manufacture an accuracy.
    """
    exp = ScientificBenchmarkExperiment()

    # Pass 0 cyclones
    res_empty = exp.run_loco_experiment(cyclones_list=[], save_results=False)
    assert res_empty["status"] == "INSUFFICIENT_DATA"
    assert "reason" in res_empty
    assert res_empty["aggregate_metrics"] == {}
    assert "out_of_fold_accuracy" not in res_empty["aggregate_metrics"]

    # Pass single cyclone with minimal track
    single_storm = [{
        "cyclone_id": "TEST_001",
        "name": "TEST_STORM",
        "track": []
    }]
    res_single = exp.run_loco_experiment(cyclones_list=single_storm, save_results=False)
    assert res_single["status"] == "INSUFFICIENT_DATA"
    assert res_single["aggregate_metrics"] == {}

# ------------------------------------------------------------------------------
# 5. Production Baseline Model B Invariance Tests
# ------------------------------------------------------------------------------
def test_existing_production_model_b_remains_unchanged():
    """
    Confirm that the existing production Model B classifier, its metrics,
    and its inference behavior remain completely unaltered and functional.
    """
    # 1. Verify metrics.json remains intact
    assert os.path.exists(registry.metrics_file), "Existing production metrics.json must remain intact"
    metrics = registry.get_metrics()

    mb_metrics = metrics["models"]["model_b"]
    assert mb_metrics["accuracy"] >= 0.95
    assert mb_metrics["f1_macro"] >= 0.95

    # 2. Verify production Model B classifier artifact inference
    clf = registry.load_classifier()

    # Severe Cyclonic Storm vector: [wind_kts=55.0, p_deficit=25.0, lat=29.0, lon=84.0, cdo=0.75, core_temp=212.0]
    vec_scs = np.array([55.0, 25.0, 29.0, 84.0, 0.75, 212.0], dtype=np.float32)
    res_scs = clf.classify(vec_scs)
    assert res_scs["classification"] == "Severe Cyclonic Storm"
    assert res_scs["tier"] == 4
    assert res_scs["abbreviation"] == "SCS"
    assert res_scs["confidence"] >= 0.65

    # Cyclonic Storm vector: [wind_kts=40.0, ...]
    vec_cs = np.array([40.0, 15.0, 18.0, 88.0, 0.60, 230.0], dtype=np.float32)
    res_cs = clf.classify(vec_cs)
    assert res_cs["classification"] == "Cyclonic Storm"
    assert res_cs["tier"] == 3

# ------------------------------------------------------------------------------
# 6. API Validation Endpoint Read-Only Tests
# ------------------------------------------------------------------------------
def test_validation_api_endpoint():
    """
    Verify GET /api/v1/validation/scientific-benchmark returns 200 with both
    the scientific benchmark and feature audit.
    """
    client = TestClient(app)
    response = client.get("/api/v1/validation/scientific-benchmark")
    assert response.status_code == 200
    data = response.json()
    assert "scientific_benchmark" in data
    assert "feature_audit" in data
    assert data["scientific_benchmark"]["experiment"] == "wind_excluded_cyclone_level_classification"
    assert data["scientific_benchmark"]["aggregate_metrics"]["out_of_fold_accuracy"] == 0.2692
