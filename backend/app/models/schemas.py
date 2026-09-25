from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# --- Explanations & Feature Importance ---
class FeatureExplanation(BaseModel):
    feature: str = Field(..., description="Name of the meteorological or satellite feature")
    value: Any = Field(..., description="Observed or extracted value")
    importance: float = Field(..., description="Relative importance weight (0.0 to 1.0)")
    impact: str = Field(..., description="ESCALATING, MITIGATING, or NEUTRAL")
    description: str = Field(..., description="Human-interpretable explanation of the contribution")

class RiskFactor(BaseModel):
    factor: str
    score: float
    max_score: float
    metric: str

class RiskAssessment(BaseModel):
    risk_score: int
    risk_level: str
    contributing_factors: List[RiskFactor] = []
    label: str = "CYCLONEX PROTOTYPE RISK INDEX"
    disclaimer: str = (
        "NOT AN OFFICIAL METEOROLOGICAL WARNING. The CYCLONEX Prototype Risk Index is a "
        "decision-support heuristic engineered exclusively for research and simulation drills. "
        "It does NOT replace official warning bulletins from IMD, WMO, or RSMC."
    )

class ForecastHorizon(BaseModel):
    lead_time_hours: int
    predicted_wind_speed_kts: float
    predicted_wind_speed_kmh: float
    predicted_pressure_hpa: float
    predicted_latitude: float
    predicted_longitude: float
    classification: str
    trend: str
    confidence: float

# Backwards compatibility alias
MultiHorizonPrediction = ForecastHorizon

# --- Primary Analysis Schema ---
class AnalyzeRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees (-90 to +90)")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees (-180 to +180)")
    temperature: Optional[float] = Field(None, description="Sea surface / air temperature in Celsius")
    humidity: Optional[float] = Field(None, ge=0.0, le=100.0, description="Relative humidity percentage (0-100)")
    pressure: Optional[float] = Field(None, ge=850.0, le=1050.0, description="Atmospheric pressure in hPa")
    wind_speed: Optional[float] = Field(None, ge=0.0, description="Sustained wind speed in km/h")
    wind_speed_kts: Optional[float] = Field(None, ge=0.0, description="Sustained wind speed in knots")
    wind_direction: Optional[float] = Field(None, ge=0.0, le=360.0, description="Wind heading in degrees (0-360)")
    satellite_image: Optional[str] = Field(None, description="Base64-encoded satellite image or image URL")
    satellite_image_path: Optional[str] = Field(None, description="Local path to satellite image file")
    cyclone_id: Optional[str] = Field(None, description="Associated cyclone UUID or identifier")
    cyclone_name: Optional[str] = Field(None, description="Optional label or disturbance identifier")
    data_mode: str = Field("DEMO", description="Data mode: LIVE, HISTORICAL, or DEMO")
    force_live_weather: bool = Field(False, description="Attempt live OpenWeather lookup for provided lat/lon")

class AnalyzeResponse(BaseModel):
    cyclone_detected: bool
    cyclone_probability: float
    classification: str
    classification_confidence: float
    classification_tier: int = 0
    predicted_wind_speed: float  # In km/h for backwards compatibility
    predicted_wind_speed_kts: float
    predicted_pressure_hpa: float
    trend: str                  # INTENSIFYING | STEADY | WEAKENING
    rapid_intensification: bool = False
    multi_horizon_forecast: List[ForecastHorizon] = []
    multi_horizon_predictions: List[ForecastHorizon] = []  # Alias
    risk: RiskAssessment
    risk_score: int             # 0 to 100
    risk_level: str             # LOW | MODERATE | HIGH | EXTREME
    explanation: List[FeatureExplanation]
    model_version: str = "v1.0-production"
    data_mode: str = "DEMO"     # LIVE | DEMO | HISTORICAL
    sources: List[str] = []
    data_sources: List[str] = [] # Alias
    timestamp: str
    disclaimer: str = (
        "NOT AN OFFICIAL METEOROLOGICAL WARNING. The CYCLONEX Prototype Risk Index is a "
        "decision-support heuristic engineered exclusively for research and simulation drills."
    )


# --- Sub-model Schemas ---
class DetectRequest(BaseModel):
    latitude: float
    longitude: float
    satellite_image: Optional[str] = None
    infrared_brightness_temp_k: Optional[float] = None
    cdo_symmetry: Optional[float] = None

class DetectResponse(BaseModel):
    cyclone_detected: bool
    cyclone_probability: float
    cdo_symmetry_score: float
    core_temp_k: float
    data_mode: str
    model_version: str

class ClassifyRequest(BaseModel):
    wind_speed_kts: float
    central_pressure_hpa: float
    cdo_symmetry: Optional[float] = None
    cloud_top_temp_k: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class ClassifyResponse(BaseModel):
    classification: str
    abbreviation: str
    classification_confidence: float
    wind_speed_kts: float
    central_pressure_hpa: float
    imd_category_tier: int
    data_mode: str
    model_version: str

class PredictRequest(BaseModel):
    latitude: float
    longitude: float
    wind_speed_kts: float
    pressure_hpa: float
    movement_speed_kmh: Optional[float] = 15.0
    movement_direction_deg: Optional[float] = 340.0
    delta_pressure_6h: Optional[float] = 0.0
    delta_wind_6h: Optional[float] = 0.0
    lead_time_hours: Optional[int] = 12

class PredictResponse(BaseModel):
    lead_time_hours: int
    predicted_wind_speed_kts: float
    predicted_wind_speed_kmh: float
    predicted_pressure_hpa: float
    predicted_latitude: float
    predicted_longitude: float
    trend: str
    confidence_score: float
    rapid_intensification_flag: bool
    data_mode: str
    model_version: str

# --- Cyclone Entities ---
class CycloneItem(BaseModel):
    id: str
    code: str
    name: str
    basin: str
    status: str
    classification: str
    current_lat: float
    current_lon: float
    max_sustained_wind_kts: float
    central_pressure_hpa: float
    movement_speed_kmh: float
    movement_direction_deg: float
    risk_level: str
    risk_score: int
    data_mode: str
    started_at: str
    last_updated_at: str

class CycloneListResponse(BaseModel):
    total: int
    active_count: int
    cyclones: List[CycloneItem]

# --- Alerts ---
class AlertRequest(BaseModel):
    cyclone_id: Optional[str] = None
    cyclone_name: str
    classification: str
    severity: str  # ADVISORY | WATCH | WARNING | EMERGENCY
    risk_score: int
    risk_level: str
    wind_speed_kts: float
    pressure_hpa: float
    latitude: float
    longitude: float
    message: Optional[str] = None

class AlertResponse(BaseModel):
    id: str
    status: str
    severity: str
    title: str
    message: str
    risk_score: int
    n8n_dispatched: bool
    channels: List[str]
    dispatched_at: str

# --- Health Check ---
class SubsystemHealth(BaseModel):
    status: str
    details: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    data_mode: str
    subsystems: Dict[str, SubsystemHealth]
