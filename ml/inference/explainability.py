from typing import List, Dict, Any
from pydantic import BaseModel, Field

class FeatureAttribution(BaseModel):
    feature: str
    observed_value: Any
    importance_weight: float = Field(..., ge=0.0, le=1.0)
    impact: str  # ESCALATING | MITIGATING | NEUTRAL
    explanation: str

class CycloneExplainabilityEngine:
    """
    Transparent feature attribution engine for CYCLONEX multi-source inference.
    Maps physical gradients, model feature importances, and atmospheric thresholds
    into interpretable contribution items for decision-makers.
    """

    @classmethod
    def attribute_features(
        cls,
        wind_kts: float,
        pressure_hpa: float,
        sst_c: float,
        humidity_pct: float,
        cdo_symmetry: float,
        core_temp_k: float,
        trend: str,
        rapid_intensification: bool
    ) -> List[FeatureAttribution]:
        attributions: List[FeatureAttribution] = []

        # 1. Barometric Pressure Deficit
        p_def = max(0.0, 1013.25 - pressure_hpa)
        if p_def >= 25.0:
            attributions.append(FeatureAttribution(
                feature="Central Barometric Pressure Deficit",
                observed_value=f"{pressure_hpa:.1f} hPa (Δ -{p_def:.1f} hPa)",
                importance_weight=0.32,
                impact="ESCALATING",
                explanation="Deep core barometric depression drives rapid cyclonic angular momentum and vortex convergence."
            ))
        elif p_def >= 10.0:
            attributions.append(FeatureAttribution(
                feature="Central Barometric Pressure Deficit",
                observed_value=f"{pressure_hpa:.1f} hPa (Δ -{p_def:.1f} hPa)",
                importance_weight=0.22,
                impact="ESCALATING",
                explanation="Moderate barometric drop supporting organized cyclonic rotation."
            ))
        else:
            attributions.append(FeatureAttribution(
                feature="Central Barometric Pressure",
                observed_value=f"{pressure_hpa:.1f} hPa",
                importance_weight=0.14,
                impact="MITIGATING",
                explanation="Near-ambient atmospheric pressure limits vortex deepening."
            ))

        # 2. Maximum Sustained 10m Wind Field
        if wind_kts >= 64.0:
            attributions.append(FeatureAttribution(
                feature="10m Sustained Wind Field",
                observed_value=f"{wind_kts:.1f} kts ({round(wind_kts * 1.852, 1)} km/h)",
                importance_weight=0.28,
                impact="ESCALATING",
                explanation="Hurricane / Very Severe Cyclonic Storm strength core exceeds critical structural damage thresholds."
            ))
        elif wind_kts >= 34.0:
            attributions.append(FeatureAttribution(
                feature="10m Sustained Wind Field",
                observed_value=f"{wind_kts:.1f} kts ({round(wind_kts * 1.852, 1)} km/h)",
                importance_weight=0.20,
                impact="ESCALATING",
                explanation="Gale-force sustained circulation confirmed across eye wall."
            ))
        else:
            attributions.append(FeatureAttribution(
                feature="10m Sustained Wind Field",
                observed_value=f"{wind_kts:.1f} kts",
                importance_weight=0.15,
                impact="NEUTRAL",
                explanation="Sub-gale surface winds typical of an early depression or tropical wave."
            ))

        # 3. Satellite CDO Overcast Symmetry & Cloud Top IR Temperature
        if cdo_symmetry >= 0.75:
            attributions.append(FeatureAttribution(
                feature="Satellite CDO Overcast Symmetry",
                observed_value=f"{cdo_symmetry:.2f}",
                importance_weight=0.18,
                impact="ESCALATING",
                explanation="High quadrant radial symmetry indicates mature vortex organization with minimal vertical wind shear disruption."
            ))
        else:
            attributions.append(FeatureAttribution(
                feature="Satellite CDO Overcast Symmetry",
                observed_value=f"{cdo_symmetry:.2f}",
                importance_weight=0.10,
                impact="NEUTRAL",
                explanation="Moderate cloud asymmetry indicates active environmental shear interaction."
            ))

        # 4. Sea Surface Temperature (SST Thermodynamic Potential)
        if sst_c >= 28.5:
            attributions.append(FeatureAttribution(
                feature="Sea Surface Temperature (SST)",
                observed_value=f"{sst_c:.1f}°C",
                importance_weight=0.14,
                impact="ESCALATING",
                explanation="Elevated ocean heat content exceeding 28.5°C threshold fuels continuous latent heat release."
            ))

        # 5. Rapid Intensification (RI) & Dynamic Trend
        if rapid_intensification:
            attributions.append(FeatureAttribution(
                feature="Rapid Intensification Signature",
                observed_value="ACTIVE (ΔV ≥ 30 kts / 24h)",
                importance_weight=0.24,
                impact="ESCALATING",
                explanation="Extreme rate of barometric drop satisfies physical criteria for explosive cyclogenesis."
            ))
        elif trend == "INTENSIFYING":
            attributions.append(FeatureAttribution(
                feature="Intensity Trend Vector",
                observed_value="INTENSIFYING",
                importance_weight=0.12,
                impact="ESCALATING",
                explanation="Positive differential wind rates project continued intensification over the 12-hour window."
            ))

        # Return sorted by importance weight descending
        return sorted(attributions, key=lambda a: a.importance_weight, reverse=True)
