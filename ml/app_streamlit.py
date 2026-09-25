import streamlit as st
import numpy as np
import pandas as pd
import json
import sys
import os

# Ensure backend app is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from app.services.ml_engine import ml_engine, IMD_CATEGORIES
from app.services.risk_engine import RiskEngine
from app.services.explainability import ExplainabilityService

st.set_page_config(
    page_title="CYCLONEX ML Debugger",
    page_icon="🌀",
    layout="wide"
)

st.title("🌀 CYCLONEX — Machine Learning & Fusion Debug Workbench")
st.caption("Internal diagnostic interface for evaluating Models A, B, C, Feature Fusion & Risk Heuristics.")

# Notice
st.info("⚠️ Non-operational research and debugging sandbox. Values and predictions are project-specific heuristics.")

# Sidebar Controls
st.sidebar.header("Meteorological & Satellite Inputs")
lat = st.sidebar.slider("Latitude (°N)", 5.0, 30.0, 15.2, 0.1)
lon = st.sidebar.slider("Longitude (°E)", 60.0, 95.0, 85.4, 0.1)
wind_speed_kts = st.sidebar.slider("Max Sustained Wind (knots)", 10.0, 160.0, 65.0, 1.0)
pressure_hpa = st.sidebar.slider("Central Pressure (hPa)", 900.0, 1015.0, 975.0, 1.0)
cdo_symmetry = st.sidebar.slider("CDO Cloud Symmetry (0 to 1)", 0.1, 1.0, 0.82, 0.01)
core_temp_k = st.sidebar.slider("IR Minimum Core Temp (Kelvin)", 190.0, 260.0, 212.0, 1.0)
sst_c = st.sidebar.slider("Sea Surface Temperature (°C)", 25.0, 32.0, 29.2, 0.1)
humidity_pct = st.sidebar.slider("Tropospheric Humidity (%)", 50.0, 100.0, 85.0, 1.0)

# Multi-Source Feature Extraction
image_features = {
    "cdo_symmetry": cdo_symmetry,
    "core_temp_k": core_temp_k,
    "spiral_curvature_score": min(1.0, cdo_symmetry * 1.1),
    "eye_feature_present": (wind_speed_kts >= 64 and cdo_symmetry > 0.75),
    "is_synthetic_proxy": True
}

# Model Inferences
detected, prob = ml_engine.detect_cyclone(image_features, wind_speed_kts, pressure_hpa)
class_name, class_abbr, class_conf, tier = ml_engine.classify_cyclone(
    wind_kts=wind_speed_kts,
    pressure_hpa=pressure_hpa,
    image_features=image_features,
    temperature_c=sst_c,
    humidity_pct=humidity_pct
)

pred_res = ml_engine.predict_short_term(
    current_lat=lat,
    current_lon=lon,
    wind_kts=wind_speed_kts,
    pressure_hpa=pressure_hpa,
    movement_speed_kmh=16.0,
    movement_direction_deg=345.0,
    sst=sst_c
)

risk_score, risk_level, breakdown = RiskEngine.calculate_risk(
    wind_speed_kts=wind_speed_kts,
    central_pressure_hpa=pressure_hpa,
    trend=pred_res["trend"],
    rapid_intensification=pred_res["rapid_intensification"],
    cdo_symmetry=cdo_symmetry,
    confidence=class_conf
)

explanations = ExplainabilityService.generate_explanations(
    wind_kts=wind_speed_kts,
    pressure_hpa=pressure_hpa,
    temperature_c=sst_c,
    humidity_pct=humidity_pct,
    cdo_symmetry=cdo_symmetry,
    core_temp_k=core_temp_k,
    trend=pred_res["trend"],
    rapid_intensification=pred_res["rapid_intensification"]
)

# UI Layout
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Model A: Detection", "DETECTED" if detected else "NO CYCLONE", f"{prob*100:.1f}% Probability")
with col2:
    st.metric("Model B: Classification", class_name, f"{class_abbr} ({class_conf*100:.0f}% Conf)")
with col3:
    st.metric("Model C: 12h Wind", f"{pred_res['horizons'][1]['predicted_wind_speed_kts']} kts", f"Trend: {pred_res['trend']}")
with col4:
    color = "red" if risk_level in ["HIGH", "EXTREME"] else ("orange" if risk_level == "MODERATE" else "green")
    st.metric("Prototype Risk Score", f"{risk_score} / 100", f"Tier: {risk_level}")

st.markdown("---")

col_left, col_right = st.columns(2)

with col_left:
    st.subheader("📊 6h / 12h / 24h Prediction Trajectory")
    h_df = pd.DataFrame(pred_res["horizons"])
    st.dataframe(h_df[["lead_time_hours", "predicted_wind_speed_kts", "predicted_pressure_hpa", "classification", "trend", "predicted_latitude", "predicted_longitude"]])
    
    st.line_chart(h_df.set_index("lead_time_hours")[["predicted_wind_speed_kts", "predicted_pressure_hpa"]])

with col_right:
    st.subheader("🧠 Explainable AI: Feature Contributions")
    exp_data = []
    for exp in explanations:
        exp_data.append({
            "Feature": exp.feature,
            "Value": str(exp.value),
            "Importance": exp.importance,
            "Impact": exp.impact,
            "Description": exp.description
        })
    st.dataframe(pd.DataFrame(exp_data))

st.subheader("🔬 Multi-Source Fusion Vector")
st.json({
    "atmospheric_features": {
        "surface_wind_kts": wind_speed_kts,
        "central_pressure_hpa": pressure_hpa,
        "sea_surface_temp_c": sst_c,
        "humidity_pct": humidity_pct
    },
    "satellite_vision_features": image_features,
    "risk_index_breakdown": breakdown
})
