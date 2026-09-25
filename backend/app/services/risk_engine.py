from typing import Tuple, Dict, Any

class RiskEngine:
    """
    CYCLONEX Prototype Risk Engine.
    Computes a transparent, multi-factor decision-support risk index (0 to 100).
    Explicitly labeled as a prototype decision-support tool, NOT an official cyclone warning.
    """

    @classmethod
    def calculate_risk(
        cls,
        wind_speed_kts: float,
        central_pressure_hpa: float,
        trend: str,
        rapid_intensification: bool = False,
        cdo_symmetry: float = 0.7,
        confidence: float = 0.9
    ) -> Tuple[int, str, Dict[str, Any]]:
        # 1. Wind Hazard Score (0 to 45 pts)
        # Max reference: 150 kts = max score
        wind_score = min(45.0, (wind_speed_kts / 150.0) * 45.0)

        # 2. Pressure Deficit Hazard (0 to 30 pts)
        # Standard sea level pressure: 1013.25 hPa
        # Extreme cyclone central pressure: ~910 hPa (delta ~103 hPa)
        p_def = max(0.0, 1013.0 - central_pressure_hpa)
        pressure_score = min(30.0, (p_def / 80.0) * 30.0)

        # 3. Dynamic Trend & Intensification Factor (0 to 15 pts)
        trend_score = 0.0
        if rapid_intensification:
            trend_score = 15.0
        elif trend == "INTENSIFYING":
            trend_score = 10.0
        elif trend == "STEADY":
            trend_score = 5.0
        else: # WEAKENING
            trend_score = 2.0

        # 4. Satellite Organization & Model Confidence (0 to 10 pts)
        visual_score = (cdo_symmetry * 6.0) + (confidence * 4.0)

        # Aggregate raw score
        total_score = wind_score + pressure_score + trend_score + visual_score
        risk_score = int(round(min(100.0, max(5.0, total_score))))

        # Determine Tier
        if risk_score >= 81:
            risk_level = "EXTREME"
        elif risk_score >= 61:
            risk_level = "HIGH"
        elif risk_score >= 36:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        breakdown = {
            "wind_hazard_component": round(wind_score, 1),
            "pressure_deficit_component": round(pressure_score, 1),
            "trend_intensification_component": round(trend_score, 1),
            "visual_confidence_component": round(visual_score, 1),
            "disclaimer": "Prototype decision-support index. Non-operational."
        }

        return risk_score, risk_level, breakdown
