from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
import numpy as np

class BaseCycloneDetector(ABC):
    """
    Interface for Model A: Cyclone Detection.
    Accepts image features or processed image array, returns binary detection and probability.
    """
    @abstractmethod
    def detect(self, image_features: Dict[str, float]) -> Tuple[bool, float]:
        """
        Returns:
            (cyclone_detected: bool, cyclone_probability: float)
        """
        pass

class BaseCycloneClassifier(ABC):
    """
    Interface for Model B: Cyclone Classification.
    Accepts fused multi-source feature vector, returns authoritative category and confidence.
    """
    @abstractmethod
    def classify(self, feature_vector: np.ndarray) -> Dict[str, Any]:
        """
        Returns:
            {
                "classification": str,
                "tier": int,
                "abbreviation": str,
                "confidence": float,
                "class_probabilities": Dict[str, float]
            }
        """
        pass

class BaseCyclonePredictor(ABC):
    """
    Interface for Model C: Short-Term Intensity & Trend Prediction.
    Accepts spatiotemporal and atmospheric trajectory features, returns future intensity & trend.
    """
    @abstractmethod
    def predict(self, feature_vector: np.ndarray) -> Dict[str, Any]:
        """
        Returns:
            {
                "predicted_wind_speed_kts": float,
                "predicted_wind_speed_kmh": float,
                "predicted_pressure_hpa": float,
                "trend": str,  # INTENSIFYING | STEADY | WEAKENING
                "rapid_intensification": bool,
                "confidence": float
            }
        """
        pass
