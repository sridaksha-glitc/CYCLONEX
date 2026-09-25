import math
import numpy as np
from datetime import datetime, timezone
from typing import List, Dict, Any, Union, Optional
from PIL import Image

from ml.data.schemas.unified import UnifiedObservation

class CycloneDataPreprocessor:
    """
    Preprocessing pipeline for multi-source cyclone intelligence.
    Handles:
      1. Missing value imputation grounded in Atkinson-Holliday physics
      2. Numerical feature normalization
      3. Feature vectorization
      4. Image resizing, normalization, and brightness temperature extraction
      5. Timestamp cyclogenesis seasonality processing
      6. Temporal sequence and delta calculation
    """

    # Atmospheric Baseline Norms (North Indian Ocean / Arabian Sea)
    BASELINE_SST_C = 28.5
    BASELINE_HUMIDITY_PCT = 80.0
    BASELINE_SEA_PRESSURE_HPA = 1013.25
    MIN_PRESSURE_BOUND_HPA = 870.0
    MAX_PRESSURE_BOUND_HPA = 1030.0

    # --------------------------------------------------------------------------
    # 1. Missing Value Handling
    # --------------------------------------------------------------------------
    @classmethod
    def impute_missing_values(cls, obs: UnifiedObservation) -> UnifiedObservation:
        """
        Fills missing meteorological and vision values using atmospheric physics.
        Uses Atkinson-Holliday empirical relationships to bind pressure and wind.
        """
        data = obs.model_dump()

        # Temperature imputation
        if data["temperature"] is None:
            data["temperature"] = cls.BASELINE_SST_C

        # Humidity imputation
        if data["humidity"] is None:
            data["humidity"] = cls.BASELINE_HUMIDITY_PCT

        # Wind & Pressure Cross-Imputation via Atkinson-Holliday
        # V_max = 6.7 * (1010 - P_c)^0.644
        if data["pressure"] is None and data["wind_speed_kts"] is not None:
            w_kts = max(5.0, data["wind_speed_kts"])
            p_def = (w_kts / 6.7) ** (1.0 / 0.644)
            data["pressure"] = round(1010.0 - p_def, 1)

        elif data["wind_speed_kts"] is None and data["pressure"] is not None:
            p_def = max(0.0, 1010.0 - data["pressure"])
            w_kts = round(6.7 * (p_def ** 0.644), 1)
            data["wind_speed_kts"] = w_kts
            data["wind_speed"] = round(w_kts * 1.852, 1)

        elif data["pressure"] is None and data["wind_speed_kts"] is None:
            data["pressure"] = 1006.0
            data["wind_speed_kts"] = 25.0
            data["wind_speed"] = 46.3

        if data["wind_speed"] is None and data["wind_speed_kts"] is not None:
            data["wind_speed"] = round(data["wind_speed_kts"] * 1.852, 1)

        if data["wind_direction"] is None:
            data["wind_direction"] = 180.0

        # Image features default
        if data["image_features"] is None:
            data["image_features"] = {
                "cdo_symmetry": 0.65,
                "min_brightness_temp_k": 220.0
            }

        return UnifiedObservation(**data)

    # --------------------------------------------------------------------------
    # 2. Numerical Feature Normalization
    # --------------------------------------------------------------------------
    @classmethod
    def normalize_features(cls, features: Dict[str, float]) -> Dict[str, float]:
        """
        Min-max normalizes physical variables into the range [0.0, 1.0].
        """
        normalized = {}

        # Wind speed (0 to 160 kts)
        w = features.get("wind_kts", 30.0)
        normalized["norm_wind"] = float(np.clip(w / 160.0, 0.0, 1.0))

        # Pressure deficit (0 to 100 hPa)
        p = features.get("pressure_hpa", 1005.0)
        p_def = max(0.0, 1013.25 - p)
        normalized["norm_pressure_deficit"] = float(np.clip(p_def / 100.0, 0.0, 1.0))

        # Sea Surface Temp (24.0°C to 32.0°C)
        sst = features.get("sst_c", 28.5)
        normalized["norm_sst"] = float(np.clip((sst - 24.0) / 8.0, 0.0, 1.0))

        # Humidity (40% to 100%)
        rh = features.get("humidity_pct", 80.0)
        normalized["norm_humidity"] = float(np.clip((rh - 40.0) / 60.0, 0.0, 1.0))

        # Satellite CDO symmetry (0.0 to 1.0)
        cdo = features.get("cdo_symmetry", 0.65)
        normalized["norm_cdo_symmetry"] = float(np.clip(cdo, 0.0, 1.0))

        return normalized

    # --------------------------------------------------------------------------
    # 3. Numerical Feature Extraction
    # --------------------------------------------------------------------------
    @classmethod
    def extract_feature_vector(cls, obs: UnifiedObservation) -> np.ndarray:
        """
        Extracts a dense numerical vector [wind_kts, p_deficit, sst, humidity, cdo_symmetry, core_temp_k]
        ready for ML Model B and Model C inference.
        """
        clean_obs = cls.impute_missing_values(obs)

        w_kts = clean_obs.wind_speed_kts or 25.0
        p_def = max(0.0, 1013.25 - (clean_obs.pressure or 1005.0))
        sst = clean_obs.temperature or 28.5
        rh = clean_obs.humidity or 80.0
        cdo = (clean_obs.image_features and clean_obs.image_features.get("cdo_symmetry")) or 0.65
        ir_temp = (clean_obs.image_features and clean_obs.image_features.get("min_brightness_temp_k")) or 220.0

        return np.array([w_kts, p_def, sst, rh, cdo, ir_temp], dtype=np.float32)

    # --------------------------------------------------------------------------
    # 4. Image Resize & Normalization
    # --------------------------------------------------------------------------
    @classmethod
    def preprocess_image(
        cls, 
        image_input: Union[str, Image.Image, np.ndarray],
        target_size: tuple = (128, 128)
    ) -> np.ndarray:
        """
        Resizes and normalizes an input image to grayscale float32 array in [0.0, 1.0].
        """
        if isinstance(image_input, str):
            img = Image.open(image_input).convert("L")
        elif isinstance(image_input, np.ndarray):
            img = Image.fromarray(image_input).convert("L")
        else:
            img = image_input.convert("L")

        resized = img.resize(target_size, Image.Resampling.BILINEAR)
        arr = np.array(resized, dtype=np.float32) / 255.0
        return arr

    # --------------------------------------------------------------------------
    # 5. Timestamp & Cyclogenesis Seasonality Processing
    # --------------------------------------------------------------------------
    @classmethod
    def process_timestamp(cls, dt: datetime) -> Dict[str, Any]:
        """
        Computes UTC ISO representation, epoch timestamp, and cyclical sine/cosine
        day of year encoding to model North Indian Ocean pre/post monsoon cyclone seasons.
        """
        day_of_year = dt.timetuple().tm_yday
        sin_doy = math.sin(2.0 * math.pi * day_of_year / 365.25)
        cos_doy = math.cos(2.0 * math.pi * day_of_year / 365.25)

        # Primary cyclogenesis windows: Pre-monsoon (April-June) and Post-monsoon (Oct-Dec)
        month = dt.month
        is_cyclone_season = (month in [4, 5, 6, 10, 11, 12])

        return {
            "iso_timestamp": dt.isoformat(),
            "epoch_seconds": int(dt.timestamp()),
            "day_of_year": day_of_year,
            "sin_day_of_year": round(sin_doy, 4),
            "cos_day_of_year": round(cos_doy, 4),
            "is_cyclone_season": is_cyclone_season
        }

    # --------------------------------------------------------------------------
    # 6. Sequence Construction & Temporal Derivatives
    # --------------------------------------------------------------------------
    @classmethod
    def construct_temporal_sequence(
        cls, 
        observations: List[UnifiedObservation], 
        window_size: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Orders observations chronologically and constructs sequential steps with
        temporal derivatives (delta pressure, delta wind, forward translation speed, heading).
        """
        if not observations:
            return []

        # Impute and sort chronologically
        cleaned = [cls.impute_missing_values(o) for o in observations]
        cleaned.sort(key=lambda x: x.timestamp)

        sequences = []
        for i in range(len(cleaned)):
            curr = cleaned[i]
            delta_p_6h = 0.0
            delta_w_6h = 0.0
            trans_speed_kmh = 15.0
            trans_heading_deg = 345.0

            if i > 0:
                prev = cleaned[i - 1]
                dt_h = max(0.5, (curr.timestamp - prev.timestamp).total_seconds() / 3600.0)

                # Pressure & wind deltas (normalized to 6h rate)
                rate = 6.0 / dt_h
                delta_p_6h = round(((curr.pressure or 1005.0) - (prev.pressure or 1005.0)) * rate, 2)
                delta_w_6h = round(((curr.wind_speed_kts or 30.0) - (prev.wind_speed_kts or 30.0)) * rate, 2)

                # Translation vector
                dy = (curr.latitude - prev.latitude) * 111.0
                dx = (curr.longitude - prev.longitude) * 111.0 * math.cos(math.radians((curr.latitude + prev.latitude) / 2.0))
                dist = math.sqrt(dx**2 + dy**2)
                trans_speed_kmh = round(dist / dt_h, 1)
                deg = math.degrees(math.atan2(dx, dy))
                trans_heading_deg = round((deg + 360.0) % 360.0, 1)

            feature_vec = cls.extract_feature_vector(curr)

            sequences.append({
                "timestamp": curr.timestamp.isoformat(),
                "latitude": curr.latitude,
                "longitude": curr.longitude,
                "wind_speed_kts": curr.wind_speed_kts,
                "pressure_hpa": curr.pressure,
                "delta_pressure_6h": delta_p_6h,
                "delta_wind_6h": delta_w_6h,
                "forward_speed_kmh": trans_speed_kmh,
                "forward_direction_deg": trans_heading_deg,
                "feature_vector": feature_vec.tolist(),
                "data_mode": curr.data_mode.value
            })

        return sequences
