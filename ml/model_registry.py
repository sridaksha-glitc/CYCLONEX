import os
import json
import joblib
from typing import Dict, Any, List, Optional

from ml.models.detector import CycloneDetector
from ml.models.classifier import CycloneClassifier
from ml.models.predictor import CyclonePredictor

class ModelRegistry:
    """
    Central repository for CYCLONEX ML model artifacts, versions, and evaluation metrics.
    Exposes metadata, training timestamps, file paths, and provides artifact loaders.
    """

    def __init__(self, artifacts_dir: Optional[str] = None):
        if not artifacts_dir:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            artifacts_dir = os.path.join(base_dir, "models", "artifacts")
        self.artifacts_dir = artifacts_dir
        self.metrics_file = os.path.join(self.artifacts_dir, "metrics.json")
        self._metrics_cache: Optional[Dict[str, Any]] = None

    def get_metrics(self) -> Dict[str, Any]:
        """
        Loads the structured evaluation metrics recorded during training.
        """
        if self._metrics_cache is not None:
            return self._metrics_cache

        if os.path.exists(self.metrics_file):
            with open(self.metrics_file, "r", encoding="utf-8") as f:
                self._metrics_cache = json.load(f)
                return self._metrics_cache
        return {
            "model_version": "v1.0",
            "models": {
                "model_a": {"status": "uninitialized"},
                "model_b": {"status": "uninitialized"},
                "model_c": {"status": "uninitialized"}
            }
        }

    def list_models(self) -> List[Dict[str, Any]]:
        """
        Enumerates all registered models with their artifact paths and evaluation summaries.
        """
        metrics = self.get_metrics()
        models_meta = metrics.get("models", {})

        return [
            {
                "key": "model_a",
                "name": "Model A — Cyclone Detection",
                "version": metrics.get("model_version", "v1.0"),
                "artifact_path": os.path.join(self.artifacts_dir, "detector_v1.joblib"),
                "training_timestamp": metrics.get("training_timestamp"),
                "metrics": models_meta.get("model_a", {})
            },
            {
                "key": "model_b",
                "name": "Model B — IMD 8-Tier Cyclone Classification",
                "version": metrics.get("model_version", "v1.0"),
                "artifact_path": os.path.join(self.artifacts_dir, "classifier_v1.joblib"),
                "training_timestamp": metrics.get("training_timestamp"),
                "metrics": models_meta.get("model_b", {})
            },
            {
                "key": "model_c",
                "name": "Model C — Short-term Trajectory & Intensity Predictor",
                "version": metrics.get("model_version", "v1.0"),
                "artifact_path": os.path.join(self.artifacts_dir, "predictor_v1.joblib"),
                "training_timestamp": metrics.get("training_timestamp"),
                "metrics": models_meta.get("model_c", {})
            }
        ]

    def load_detector(self) -> CycloneDetector:
        path = os.path.join(self.artifacts_dir, "detector_v1.joblib")
        clf = joblib.load(path) if os.path.exists(path) else None
        return CycloneDetector(classifier_model=clf)

    def load_classifier(self) -> CycloneClassifier:
        path = os.path.join(self.artifacts_dir, "classifier_v1.joblib")
        clf = joblib.load(path) if os.path.exists(path) else None
        return CycloneClassifier(classifier_model=clf)

    def load_predictor(self) -> CyclonePredictor:
        path = os.path.join(self.artifacts_dir, "predictor_v1.joblib")
        reg = joblib.load(path) if os.path.exists(path) else None
        return CyclonePredictor(regressor_model=reg)

# Global registry instance
registry = ModelRegistry()
