import math
from typing import Dict, Any, List, Optional
import numpy as np

from ml.models.base import BaseCyclonePredictor
from ml.models.classifier import IMD_CATEGORIES

class CyclonePredictor(BaseCyclonePredictor):
    """
    Model C: Short-term Intensity & Trend Predictor.
    Projects future maximum sustained winds, central pressure, trajectory position,
    and rapid intensification flags for +6h, +12h, and +24h forecast horizons.
    """

    def __init__(self, regressor_model=None, version: str = "v1.0-predictor"):
        self.regressor = regressor_model
        self.version = version

    def predict(self, feature_vector: np.ndarray) -> Dict[str, Any]:
        """
        Expected features:
        [lat, lon, wind_kts, pressure_hpa, delta_w_6h, delta_p_6h, forward_speed, forward_heading, sst, is_cyclone_season]
        """
        if feature_vector.ndim == 1:
            feature_vector = feature_vector.reshape(1, -1)

        lat = float(feature_vector[0, 0])
        lon = float(feature_vector[0, 1])
        wind_kts = float(feature_vector[0, 2])
        pressure_hpa = float(feature_vector[0, 3])
        dw6 = float(feature_vector[0, 4])
        dp6 = float(feature_vector[0, 5])
        speed_kmh = float(feature_vector[0, 6])
        heading_deg = float(feature_vector[0, 7])
        sst = float(feature_vector[0, 8])

        # 12-hour delta prediction
        if self.regressor is not None:
            pred_delta_12h_kts = float(self.regressor.predict(feature_vector)[0])
        else:
            # Calibrated meteorological physics baseline:
            # Deepening pressure (dp6 < 0) + warm SST (>28C) + positive 6h wind trend -> positive delta
            pred_delta_12h_kts = (-1.2 * dp6) + (0.5 * dw6) + (0.6 * max(0.0, sst - 28.0))

        # Trajectory translation
        rad = math.radians(heading_deg)
        d_lat_per_hr = (speed_kmh / 111.0) * math.cos(rad)
        d_lon_per_hr = (speed_kmh / (111.0 * max(0.2, math.cos(math.radians(lat))))) * math.sin(rad)

        horizons = []
        for lead_h in [6, 12, 24]:
            scale = lead_h / 12.0
            p_wind_kts = max(10.0, round(wind_kts + (pred_delta_12h_kts * scale), 1))
            p_wind_kmh = round(p_wind_kts * 1.852, 1)

            # Central pressure responds via Atkinson-Holliday gradient (~0.8 hPa per knot of wind)
            p_pres_hpa = round(pressure_hpa - (pred_delta_12h_kts * scale * 0.75), 1)
            p_lat = round(lat + (d_lat_per_hr * lead_h), 2)
            p_lon = round(lon + (d_lon_per_hr * lead_h), 2)

            # Determine category
            p_class = "Low Pressure Area"
            for cat in IMD_CATEGORIES:
                if cat["min_kts"] <= p_wind_kts <= cat["max_kts"]:
                    p_class = cat["name"]
                    break

            if p_wind_kts >= wind_kts + 3.0:
                h_trend = "INTENSIFYING"
            elif p_wind_kts <= wind_kts - 3.0:
                h_trend = "WEAKENING"
            else:
                h_trend = "STEADY"

            horizons.append({
                "lead_time_hours": lead_h,
                "predicted_wind_speed_kts": p_wind_kts,
                "predicted_wind_speed_kmh": p_wind_kmh,
                "predicted_pressure_hpa": p_pres_hpa,
                "predicted_latitude": p_lat,
                "predicted_longitude": p_lon,
                "predicted_classification": p_class,
                "trend": h_trend,
                "confidence": round(max(0.65, 0.92 - (lead_h * 0.008)), 2)
            })

        h12 = horizons[1]
        overall_trend = h12["trend"]
        is_rapid_intensification = bool(pred_delta_12h_kts >= 15.0) # >=30 kts in 24h

        return {
            "predicted_wind_speed_kts": h12["predicted_wind_speed_kts"],
            "predicted_wind_speed_kmh": h12["predicted_wind_speed_kmh"],
            "predicted_pressure_hpa": h12["predicted_pressure_hpa"],
            "trend": overall_trend,
            "rapid_intensification": is_rapid_intensification,
            "confidence": h12["confidence"],
            "horizons": horizons
        }
