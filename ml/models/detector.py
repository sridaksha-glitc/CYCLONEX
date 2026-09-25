import math
from typing import Dict, Any, Tuple, Optional
import numpy as np
from PIL import Image

from ml.models.base import BaseCycloneDetector

class CycloneDetector(BaseCycloneDetector):
    """
    Model A: Cyclone Detection.
    Lightweight computer vision model extracting structural features from satellite IR/visible imagery
    and classifying the presence of an organized cyclonic system.
    """

    def __init__(self, classifier_model=None, version: str = "v1.0-detector"):
        self.classifier = classifier_model
        self.version = version

    @classmethod
    def extract_image_features(cls, image_input: Optional[Image.Image]) -> Dict[str, float]:
        """
        Extracts structural computer vision metrics from a satellite image:
        - CDO symmetry score (quadrant variance around centroid)
        - Cloud-top core brightness temperature (Kelvin proxy)
        - Spiral curvature gradient magnitude
        - Eye pattern detection
        """
        if image_input is None:
            return {
                "cdo_symmetry": 0.65,
                "core_temp_k": 220.0,
                "spiral_curvature": 0.60,
                "eye_detected": 0.0,
                "is_synthetic_proxy": True
            }

        try:
            # Grayscale 128x128 array
            gray = image_input.convert("L").resize((128, 128))
            arr = np.array(gray, dtype=np.float32)

            # Central 40x40 core
            center_x, center_y = 64, 64
            core = arr[center_y - 20:center_y + 20, center_x - 20:center_x + 20]

            # Quadrant symmetry check
            q1 = arr[:64, 64:]
            q2 = arr[:64, :64]
            q3 = arr[64:, :64]
            q4 = arr[64:, 64:]
            means = [float(np.mean(q1)), float(np.mean(q2)), float(np.mean(q3)), float(np.mean(q4))]
            mean_all = float(np.mean(means)) + 1e-5
            std_q = float(np.std(means))
            symmetry = max(0.05, min(0.98, 1.0 - (std_q / mean_all)))

            # IR Brightness Temp conversion approximation (200K - 290K range)
            min_val = float(np.min(core))
            core_temp_k = 200.0 + (min_val / 255.0) * 80.0

            # Gradient magnitude as proxy for spiral bands
            gy, gx = np.gradient(arr)
            grad_mag = float(np.mean(np.sqrt(gx**2 + gy**2)))
            curvature = min(1.0, grad_mag / 25.0)

            # Eye detection: warm/dark core surrounded by cold dense overcast
            eye_present = 1.0 if (float(np.mean(core)) > float(np.mean(arr)) * 1.15 and symmetry > 0.75) else 0.0

            return {
                "cdo_symmetry": round(symmetry, 3),
                "core_temp_k": round(core_temp_k, 1),
                "spiral_curvature": round(curvature, 3),
                "eye_detected": eye_present,
                "is_synthetic_proxy": False
            }
        except Exception:
            return {
                "cdo_symmetry": 0.65,
                "core_temp_k": 220.0,
                "spiral_curvature": 0.60,
                "eye_detected": 0.0,
                "is_synthetic_proxy": True
            }

    def detect(self, image_features: Dict[str, float]) -> Tuple[bool, float]:
        """
        Predicts binary cyclone detection and probability.
        Uses trained classifier if available, or calibrated logistic response.
        """
        cdo = image_features.get("cdo_symmetry", 0.65)
        core_temp = image_features.get("core_temp_k", 220.0)
        curvature = image_features.get("spiral_curvature", 0.60)
        eye = image_features.get("eye_detected", 0.0)

        if self.classifier is not None:
            vec = np.array([[cdo, core_temp, curvature, eye]], dtype=np.float32)
            prob = float(self.classifier.predict_proba(vec)[0][1])
            detected = bool(prob >= 0.50)
            return detected, round(prob, 3)

        # Calibrated baseline logistic response
        # High symmetry, cold cloud core (<230K), high curvature, eye pattern -> high probability
        logit = (cdo * 4.2) + (curvature * 2.5) + (eye * 1.8) - ((core_temp - 210.0) * 0.05) - 3.2
        prob = 1.0 / (1.0 + math.exp(-max(-10.0, min(10.0, logit))))
        detected = bool(prob >= 0.50)
        return detected, round(prob, 3)
