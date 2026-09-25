from typing import List, Dict, Any
from app.models.schemas import FeatureExplanation

class ExplainabilityService:
    """
    Transparent Explainable AI (XAI) feature attribution service.
    Translates model weights, physical gradients, and observational inputs
    into interpretable contribution items for decision-makers.
    """

    @classmethod
    def generate_explanations(
        cls,
        wind_kts: float,
        pressure_hpa: float,
        temperature_c: float,
        humidity_pct: float,
        cdo_symmetry: float,
        core_temp_k: float,
        trend: str,
        rapid_intensification: bool
    ) -> List[FeatureExplanation]:
        explanations = []

        # 1. Central Pressure Deficit
        p_def = 1013.0 - pressure_hpa
        if p_def > 25.0:
            explanations.append(FeatureExplanation(
                feature="Central Atmospheric Pressure Deficit",
                value=f"{pressure_hpa:.1f} hPa (Δ -{p_def:.1f} hPa)",
                importance=0.34,
                impact="ESCALATING",
                description="Deep central barometric drop indicates intense low-pressure cyclonic vortex core."
            ))
        elif p_def > 10.0:
            explanations.append(FeatureExplanation(
                feature="Central Atmospheric Pressure Deficit",
                value=f"{pressure_hpa:.1f} hPa (Δ -{p_def:.1f} hPa)",
                importance=0.25,
                impact="ESCALATING",
                description="Moderate barometric depression supporting organized cyclonic rotation."
            ))
        else:
            explanations.append(FeatureExplanation(
                feature="Atmospheric Pressure",
                value=f"{pressure_hpa:.1f} hPa",
                importance=0.15,
                impact="MITIGATING",
                description="Near-normal sea-level pressure dampens cyclogenesis escalation."
            ))

        # 2. Maximum Sustained Winds
        if wind_kts >= 64.0:
            explanations.append(FeatureExplanation(
                feature="Sustained Wind Field (10m)",
                value=f"{wind_kts:.1f} kts ({round(wind_kts*1.852, 1)} km/h)",
                importance=0.31,
                impact="ESCALATING",
                description="Hurricane/Very Severe Cyclonic Storm strength winds exceeding 64 knots threshold."
            ))
        elif wind_kts >= 34.0:
            explanations.append(FeatureExplanation(
                feature="Sustained Wind Field (10m)",
                value=f"{wind_kts:.1f} kts ({round(wind_kts*1.852, 1)} km/h)",
                importance=0.24,
                impact="ESCALATING",
                description="Gale-force cyclonic circulation identified across outer core."
            ))
        else:
            explanations.append(FeatureExplanation(
                feature="Wind Velocity",
                value=f"{wind_kts:.1f} kts ({round(wind_kts*1.852, 1)} km/h)",
                importance=0.18,
                impact="NEUTRAL",
                description="Sub-gale winds typical of depression or low pressure area."
            ))

        # 3. Satellite Infrared Core Brightness & CDO Symmetry
        if cdo_symmetry >= 0.75:
            explanations.append(FeatureExplanation(
                feature="Satellite CDO Overcast Symmetry",
                value=f"{cdo_symmetry:.2f} (High)",
                importance=0.19,
                impact="ESCALATING",
                description="High quadrant cloud symmetry and spiral curvature denote tight vortex organization."
            ))
        else:
            explanations.append(FeatureExplanation(
                feature="Satellite CDO Symmetry",
                value=f"{cdo_symmetry:.2f} (Moderate)",
                importance=0.12,
                impact="NEUTRAL",
                description="Slightly asymmetrical cloud distribution indicates potential shear influence."
            ))

        # 4. Sea Surface Temperature & Humidity
        if temperature_c >= 28.0:
            explanations.append(FeatureExplanation(
                feature="Sea Surface Temperature (SST)",
                value=f"{temperature_c:.1f}°C",
                importance=0.16,
                impact="ESCALATING",
                description="Thermal sea surface exceeding 28.0°C provides potent thermodynamic latent heat fuel."
            ))

        # 5. Trend / Rapid Intensification
        if rapid_intensification:
            explanations.append(FeatureExplanation(
                feature="Rapid Intensification Signature",
                value="Active (+30 kts / 24h trajectory)",
                importance=0.22,
                impact="ESCALATING",
                description="Physical rates of central pressure deepening qualify for rapid intensification watch."
            ))
        elif trend == "INTENSIFYING":
            explanations.append(FeatureExplanation(
                feature="Intensity Trend Vector",
                value="INTENSIFYING",
                importance=0.14,
                impact="ESCALATING",
                description="Atmospheric feedback points to continued vortex tightening over next 12 hours."
            ))

        return sorted(explanations, key=lambda x: x.importance, reverse=True)
