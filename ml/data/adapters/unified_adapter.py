from datetime import datetime, timezone
from typing import Optional, Dict, Any

from ml.data.schemas.unified import (
    UnifiedObservation, 
    SatelliteObservation, 
    WeatherObservation, 
    HistoricalCycloneObservation, 
    DataMode
)

class UnifiedDataAdapter:
    """
    Fuses heterogeneous observations (satellite, weather, historical) into a single
    normalized UnifiedObservation entity for the ML pipeline.
    """

    @classmethod
    def fuse(
        cls,
        weather: Optional[WeatherObservation] = None,
        satellite: Optional[SatelliteObservation] = None,
        historical: Optional[HistoricalCycloneObservation] = None,
        default_lat: float = 15.0,
        default_lon: float = 85.0
    ) -> UnifiedObservation:
        # Determine temporal anchor
        timestamp = (
            (weather and weather.timestamp) or
            (satellite and satellite.timestamp) or
            (historical and historical.timestamp) or
            datetime.now(timezone.utc)
        )

        # Spatial coordinates priority: Weather -> Historical -> Satellite -> default
        lat = default_lat
        lon = default_lon
        if weather:
            lat, lon = weather.latitude, weather.longitude
        elif historical:
            lat, lon = historical.latitude, historical.longitude
        elif satellite and satellite.latitude is not None and satellite.longitude is not None:
            lat, lon = satellite.latitude, satellite.longitude

        # Atmospheric variables
        temp = weather.temperature_c if weather else 28.5
        humidity = weather.humidity_pct if weather else 80.0
        pressure = (weather and weather.pressure_hpa) or (historical and historical.pressure_hpa) or 1004.0
        
        wind_kts = (weather and weather.wind_speed_kts) or (historical and historical.wind_kts) or 25.0
        wind_kmh = (weather and weather.wind_speed_kmh) or (historical and historical.wind_kmh) or round(wind_kts * 1.852, 1)
        wind_deg = (weather and weather.wind_direction_deg) or (historical and historical.movement_direction_deg) or 180.0

        # Cyclone identity
        cid = historical.cyclone_id if historical else None
        cname = historical.cyclone_name if historical else None
        classification = historical.classification if historical else None

        # Satellite features
        img_path = satellite.image_path if satellite else None
        img_features = None
        if satellite:
            img_features = {
                "cdo_symmetry": satellite.cdo_symmetry or 0.65,
                "min_brightness_temp_k": satellite.min_brightness_temp_k or 220.0
            }

        # Data mode determination (strict rule: never label DEMO as LIVE)
        modes = []
        if weather: modes.append(weather.data_mode)
        if satellite: modes.append(satellite.data_mode)
        if historical: modes.append(historical.data_mode)

        if DataMode.DEMO in modes or not modes:
            overall_mode = DataMode.DEMO
        elif all(m == DataMode.HISTORICAL for m in modes):
            overall_mode = DataMode.HISTORICAL
        elif any(m == DataMode.LIVE for m in modes):
            overall_mode = DataMode.LIVE
        else:
            overall_mode = DataMode.DEMO

        sources = []
        if weather: sources.append(weather.source)
        if satellite: sources.append(satellite.source)
        if historical: sources.append(historical.source)
        source_summary = " + ".join(sources) if sources else "Unified Fusion Engine"

        return UnifiedObservation(
            timestamp=timestamp,
            latitude=lat,
            longitude=lon,
            source=source_summary,
            data_mode=overall_mode,
            image_path=img_path,
            image_features=img_features,
            temperature=temp,
            humidity=humidity,
            pressure=pressure,
            wind_speed=wind_kmh,
            wind_speed_kts=wind_kts,
            wind_direction=wind_deg,
            cyclone_id=cid,
            cyclone_name=cname,
            classification=classification,
            metadata={"fused_sources_count": len(sources)}
        )
