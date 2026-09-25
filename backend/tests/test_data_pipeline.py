import pytest
import os
import numpy as np
from datetime import datetime, timezone
from PIL import Image

from ml.data.schemas.unified import (
    DataMode,
    SatelliteObservation,
    WeatherObservation,
    HistoricalCycloneObservation,
    UnifiedObservation
)
from ml.data.adapters.satellite_adapter import LocalSatelliteAdapter, DemoSatelliteAdapter
from ml.data.adapters.weather_adapter import OpenWeatherAdapter, DemoWeatherAdapter
from ml.data.adapters.historical_adapter import IBTrACSAdapter, DemoHistoricalAdapter
from ml.data.adapters.unified_adapter import UnifiedDataAdapter
from ml.data.preprocessing import CycloneDataPreprocessor

# ------------------------------------------------------------------------------
# Satellite Adapter Tests
# ------------------------------------------------------------------------------
@pytest.mark.anyio
async def test_local_satellite_adapter():
    adapter = LocalSatelliteAdapter()
    obs = await adapter.get_observation(latitude=20.8, longitude=89.3)
    
    assert isinstance(obs, SatelliteObservation)
    assert obs.source.startswith("INSAT-3D")
    assert obs.data_mode == DataMode.HISTORICAL
    assert obs.channel == "IR-10.8um"
    assert obs.min_brightness_temp_k is not None
    assert obs.cdo_symmetry is not None
    assert obs.image_path is not None and os.path.exists(obs.image_path)

    # Test Image Loading
    img = adapter.load_image(obs)
    assert isinstance(img, Image.Image)
    assert img.size == (128, 128)

@pytest.mark.anyio
async def test_demo_satellite_adapter():
    adapter = DemoSatelliteAdapter()
    obs = await adapter.get_observation(latitude=14.0, longitude=85.0)

    assert obs.data_mode == DataMode.DEMO
    assert obs.source.startswith("Procedural")
    img = adapter.load_image(obs)
    assert isinstance(img, Image.Image)
    assert img.size == (128, 128)

# ------------------------------------------------------------------------------
# Weather Adapter Tests
# ------------------------------------------------------------------------------
@pytest.mark.anyio
async def test_openweather_adapter_without_key():
    adapter = OpenWeatherAdapter(api_key="")
    with pytest.raises(ValueError, match="OPENWEATHER_API_KEY is not configured"):
        await adapter.get_observation(latitude=13.0, longitude=80.0)

@pytest.mark.anyio
async def test_demo_weather_adapter():
    adapter = DemoWeatherAdapter()
    obs = await adapter.get_observation(latitude=15.0, longitude=88.0)

    assert isinstance(obs, WeatherObservation)
    assert obs.data_mode == DataMode.DEMO
    assert obs.temperature_c >= 25.0
    assert 900.0 <= obs.pressure_hpa <= 1020.0
    assert obs.wind_speed_kts > 0.0
    assert obs.wind_speed_kmh == round(obs.wind_speed_kts * 1.852, 1)

# ------------------------------------------------------------------------------
# Historical Adapter Tests (IBTrACS)
# ------------------------------------------------------------------------------
def test_ibtracs_adapter_list_and_track():
    adapter = IBTrACSAdapter()
    storms = adapter.list_cyclones()
    assert len(storms) >= 4

    storm_names = [s["name"] for s in storms]
    assert "REMAL" in storm_names
    assert "BIPARJOY" in storm_names

    # Retrieve Remal track
    track = adapter.get_cyclone_track("REMAL")
    assert len(track) >= 5
    first_pt = track[0]
    last_pt = track[-1]

    assert first_pt.cyclone_name == "REMAL"
    assert first_pt.data_mode == DataMode.HISTORICAL
    assert first_pt.wind_kts > 0
    assert first_pt.pressure_hpa > 900

    # Test inter-point movement calculation
    assert track[1].movement_speed_kmh is not None
    assert track[1].movement_direction_deg is not None

def test_demo_historical_adapter():
    adapter = DemoHistoricalAdapter()
    storms = adapter.list_cyclones()
    assert len(storms) >= 1
    track = adapter.get_cyclone_track("DEMO-INVEST-91B")
    assert len(track) >= 1
    assert track[0].data_mode == DataMode.DEMO

# ------------------------------------------------------------------------------
# Unified Data Adapter Tests
# ------------------------------------------------------------------------------
@pytest.mark.anyio
async def test_unified_data_adapter_fusion():
    sat_adapter = LocalSatelliteAdapter()
    weather_adapter = DemoWeatherAdapter()
    hist_adapter = IBTrACSAdapter()

    sat_obs = await sat_adapter.get_observation(latitude=21.0, longitude=89.0)
    weather_obs = await weather_adapter.get_observation(latitude=21.0, longitude=89.0)
    remal_track = hist_adapter.get_cyclone_track("REMAL")
    hist_obs = remal_track[0]

    unified = UnifiedDataAdapter.fuse(
        weather=weather_obs,
        satellite=sat_obs,
        historical=hist_obs
    )

    assert isinstance(unified, UnifiedObservation)
    assert unified.latitude == 21.0
    assert unified.longitude == 89.0
    assert unified.cyclone_name == "REMAL"
    assert unified.temperature is not None
    assert unified.pressure is not None
    assert unified.wind_speed_kts is not None
    assert unified.image_features is not None
    # Because weather is DEMO, overall mode must be DEMO (never masquerade demo as historical/live)
    assert unified.data_mode == DataMode.DEMO

# ------------------------------------------------------------------------------
# Preprocessing Pipeline Tests
# ------------------------------------------------------------------------------
def test_preprocessing_imputation_physics():
    # 1. Missing pressure -> Atkinson-Holliday wind deduction
    obs_no_pres = UnifiedObservation(
        timestamp=datetime.now(timezone.utc),
        latitude=15.0,
        longitude=85.0,
        source="Test Sensor",
        data_mode=DataMode.DEMO,
        wind_speed_kts=60.0
    )
    cleaned = CycloneDataPreprocessor.impute_missing_values(obs_no_pres)
    assert cleaned.pressure is not None
    assert 960.0 <= cleaned.pressure <= 995.0 # Physical pressure deficit for 60 kts

    # 2. Missing wind -> pressure deduction
    obs_no_wind = UnifiedObservation(
        timestamp=datetime.now(timezone.utc),
        latitude=15.0,
        longitude=85.0,
        source="Test Sensor",
        data_mode=DataMode.DEMO,
        pressure=980.0
    )
    cleaned_wind = CycloneDataPreprocessor.impute_missing_values(obs_no_wind)
    assert cleaned_wind.wind_speed_kts is not None
    assert 50.0 <= cleaned_wind.wind_speed_kts <= 75.0

def test_preprocessing_normalization():
    raw_feats = {
        "wind_kts": 80.0,
        "pressure_hpa": 965.0,
        "sst_c": 29.5,
        "humidity_pct": 85.0,
        "cdo_symmetry": 0.82
    }
    norm = CycloneDataPreprocessor.normalize_features(raw_feats)
    for key, val in norm.items():
        assert 0.0 <= val <= 1.0

def test_feature_vector_extraction():
    obs = UnifiedObservation(
        timestamp=datetime.now(timezone.utc),
        latitude=15.0,
        longitude=85.0,
        source="Test Sensor",
        data_mode=DataMode.DEMO,
        temperature=29.0,
        humidity=82.0,
        pressure=985.0,
        wind_speed_kts=55.0,
        image_features={"cdo_symmetry": 0.75, "min_brightness_temp_k": 210.0}
    )
    vec = CycloneDataPreprocessor.extract_feature_vector(obs)
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (6,)
    assert vec[0] == 55.0 # wind_kts
    assert vec[1] == pytest.approx(1013.25 - 985.0, 0.1) # p_def

def test_timestamp_seasonality_processing():
    # Cyclone in May (Pre-monsoon peak)
    dt_may = datetime(2024, 5, 25, 12, 0, 0, tzinfo=timezone.utc)
    res_may = CycloneDataPreprocessor.process_timestamp(dt_may)
    assert res_may["is_cyclone_season"] is True
    assert -1.0 <= res_may["sin_day_of_year"] <= 1.0

    # Low activity month (e.g. February)
    dt_feb = datetime(2024, 2, 10, 12, 0, 0, tzinfo=timezone.utc)
    res_feb = CycloneDataPreprocessor.process_timestamp(dt_feb)
    assert res_feb["is_cyclone_season"] is False

def test_sequence_construction_with_deltas():
    # Construct 3 sequential 6-hour track points for a deepening storm
    t0 = datetime(2024, 5, 24, 0, 0, 0, tzinfo=timezone.utc)
    t1 = datetime(2024, 5, 24, 6, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2024, 5, 24, 12, 0, 0, tzinfo=timezone.utc)

    obs_list = [
        UnifiedObservation(
            timestamp=t0, latitude=18.0, longitude=89.0, source="IBTrACS",
            data_mode=DataMode.HISTORICAL, wind_speed_kts=35.0, pressure=995.0
        ),
        UnifiedObservation(
            timestamp=t1, latitude=18.6, longitude=89.1, source="IBTrACS",
            data_mode=DataMode.HISTORICAL, wind_speed_kts=45.0, pressure=990.0
        ),
        UnifiedObservation(
            timestamp=t2, latitude=19.3, longitude=89.2, source="IBTrACS",
            data_mode=DataMode.HISTORICAL, wind_speed_kts=55.0, pressure=982.0
        )
    ]

    seq = CycloneDataPreprocessor.construct_temporal_sequence(obs_list)
    assert len(seq) == 3
    
    # Check step 1 (6h point)
    step1 = seq[1]
    assert step1["delta_wind_6h"] == 10.0 # +10 kts in 6h
    assert step1["delta_pressure_6h"] == -5.0 # -5 hPa in 6h (deepening)
    assert step1["forward_speed_kmh"] > 0
    assert 0.0 <= step1["forward_direction_deg"] <= 45.0 # Heading North-North-East

    # Check step 2 (12h point)
    step2 = seq[2]
    assert step2["delta_wind_6h"] == 10.0
    assert step2["delta_pressure_6h"] == -8.0
