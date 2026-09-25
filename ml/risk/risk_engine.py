from typing import Dict, Any, List, Tuple
from pydantic import BaseModel, Field

class PrototypeRiskAssessment(BaseModel):
    risk_score: int = Field(..., ge=0, le=100, description="Prototype Risk Index (0-100)")
    risk_level: str = Field(..., description="LOW | MODERATE | HIGH | EXTREME")
    contributing_factors: List[Dict[str, Any]]
    label: str = "CYCLONEX PROTOTYPE RISK INDEX"
    disclaimer: str = (
        "NOT AN OFFICIAL METEOROLOGICAL WARNING. "
        "The CYCLONEX Prototype Risk Index is a decision-support heuristic engineered exclusively for "
        "research and simulation drills. It does NOT replace official warning bulletins from IMD, WMO, or RSMC."
    )

class CycloneRiskEngine:
    """
    Independent Risk Calculation Engine.
    Decoupled from ML model internals; receives structured inference outputs and environmental context
    to calculate the CYCLONEX Prototype Risk Index (0 to 100).
    """

    @classmethod
    def evaluate_risk(
        cls,
        wind_speed_kts: float,
        central_pressure_hpa: float,
        classification_tier: int,
        trend: str,
        rapid_intensification: bool = False,
        confidence: float = 0.90,
        cdo_symmetry: float = 0.65
    ) -> PrototypeRiskAssessment:
        factors = []

        # 1. Wind Kinetic Energy Hazard (0 to 45 pts)
        # 150 kts = max point scale
        wind_component = min(45.0, (wind_speed_kts / 150.0) * 45.0)
        factors.append({
            "factor": "Surface Wind Field Hazard",
            "score": round(wind_component, 1),
            "max_score": 45.0,
            "metric": f"{wind_speed_kts:.1f} kts ({round(wind_speed_kts * 1.852, 1)} km/h)"
        })

        # 2. Barometric Deepening Hazard (0 to 30 pts)
        # Pressure deficit below standard sea level (1013.25 hPa)
        p_def = max(0.0, 1013.25 - central_pressure_hpa)
        pressure_component = min(30.0, (p_def / 85.0) * 30.0)
        factors.append({
            "factor": "Central Barometric Deficit",
            "score": round(pressure_component, 1),
            "max_score": 30.0,
            "metric": f"{central_pressure_hpa:.1f} hPa (deficit: {p_def:.1f} hPa)"
        })

        # 3. Dynamic Intensification Factor (0 to 15 pts)
        if rapid_intensification:
            trend_score = 15.0
            trend_desc = "Rapid Intensification Active (+15 pts)"
        elif trend == "INTENSIFYING":
            trend_score = 10.0
            trend_desc = "Vortex Intensifying (+10 pts)"
        elif trend == "STEADY":
            trend_score = 5.0
            trend_desc = "Steady State (+5 pts)"
        else: # WEAKENING
            trend_score = 2.0
            trend_desc = "System Weakening (+2 pts)"

        factors.append({
            "factor": "Dynamic Intensification Trend",
            "score": round(trend_score, 1),
            "max_score": 15.0,
            "metric": trend_desc
        })

        # 4. Satellite Organization & Model Confidence (0 to 10 pts)
        coherence_score = (cdo_symmetry * 6.0) + (confidence * 4.0)
        factors.append({
            "factor": "Convective Symmetry & Model Confidence",
            "score": round(coherence_score, 1),
            "max_score": 10.0,
            "metric": f"CDO: {cdo_symmetry:.2f}, Conf: {confidence:.2f}"
        })

        # Total Aggregate Risk Score [0, 100]
        total_raw = wind_component + pressure_component + trend_score + coherence_score
        risk_score = int(round(min(100.0, max(5.0, total_raw))))

        # Tier Thresholds
        if risk_score >= 81:
            risk_level = "EXTREME"
        elif risk_score >= 61:
            risk_level = "HIGH"
        elif risk_score >= 36:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        return PrototypeRiskAssessment(
            risk_score=risk_score,
            risk_level=risk_level,
            contributing_factors=factors
        )
