from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class DataMode(str, Enum):
    LIVE = "LIVE"
    HISTORICAL = "HISTORICAL"
    DEMO = "DEMO"

class SatelliteObservation(BaseModel):
    """
    Standardized schema for satellite infrared, visible, or microwave imagery observations.
    """
    timestamp: datetime
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    source: str = Field(..., description="e.g. INSAT-3D, INSAT-3DR, GOES-16, LocalArchive, Synthetic")
    data_mode: DataMode = Field(..., description="LIVE | HISTORICAL | DEMO")
    image_path: Optional[str] = None
    channel: str = Field(default="IR-10.8um", description="IR-10.8um | VIS-0.65um | WaterVapor")
    min_brightness_temp_k: Optional[float] = Field(None, description="Cloud top minimum core temperature in Kelvin")
    cdo_symmetry: Optional[float] = Field(None, ge=0.0, le=1.0, description="Central Dense Overcast symmetry metric")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WeatherObservation(BaseModel):
    """
    Standardized schema for in-situ, buoy, surface meteorological observations.
    """
    timestamp: datetime
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    temperature_c: float = Field(..., description="Air / Sea-surface temperature in Celsius")
    humidity_pct: float = Field(..., ge=0.0, le=100.0, description="Relative humidity %")
    pressure_hpa: float = Field(..., description="Atmospheric barometric pressure in hPa")
    wind_speed_kts: float = Field(..., ge=0.0, description="10m sustained wind speed in knots")
    wind_speed_kmh: float = Field(..., ge=0.0, description="10m sustained wind speed in km/h")
    wind_direction_deg: float = Field(..., ge=0.0, le=360.0, description="Wind heading 0-360 degrees")
    source: str = Field(..., description="e.g. OpenWeather Live, Global Buoy Network, DemoAdapter")
    data_mode: DataMode = Field(..., description="LIVE | HISTORICAL | DEMO")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class HistoricalCycloneObservation(BaseModel):
    """
    Standardized schema for authoritative historical cyclone observations (e.g. NOAA IBTrACS).
    """
    cyclone_id: str = Field(..., description="Storm Identifier, e.g. 2024146N18089 or BOB-01-2024")
    cyclone_name: str = Field(..., description="Official storm name, e.g. REMAL, BIPARJOY")
    timestamp: datetime
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    wind_kts: float = Field(..., ge=0.0, description="Maximum sustained wind speed in knots")
    wind_kmh: float = Field(..., ge=0.0, description="Maximum sustained wind speed in km/h")
    pressure_hpa: float = Field(..., description="Central minimum pressure in hPa")
    movement_speed_kmh: Optional[float] = Field(None, description="Forward speed in km/h")
    movement_direction_deg: Optional[float] = Field(None, description="Forward movement heading 0-360")
    classification: Optional[str] = Field(None, description="IMD / WMO category label")
    basin: str = Field(default="North Indian Ocean")
    source: str = Field(default="NOAA IBTrACS v04r00")
    data_mode: DataMode = Field(default=DataMode.HISTORICAL)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class UnifiedObservation(BaseModel):
    """
    Unified multi-source observation fusing satellite, weather, and historical records.
    Core internal schema for the CYCLONEX ML feature extraction and inference pipeline.
    """
    timestamp: datetime
    latitude: float
    longitude: float
    source: str
    data_mode: DataMode
    image_path: Optional[str] = None
    image_features: Optional[Dict[str, float]] = None
    temperature: Optional[float] = None       # in Celsius
    humidity: Optional[float] = None          # %
    pressure: Optional[float] = None          # in hPa
    wind_speed: Optional[float] = None        # in km/h
    wind_speed_kts: Optional[float] = None    # in knots
    wind_direction: Optional[float] = None    # degrees
    cyclone_id: Optional[str] = None
    cyclone_name: Optional[str] = None
    classification: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
