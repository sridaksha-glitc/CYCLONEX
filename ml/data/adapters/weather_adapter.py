import os
import httpx
from datetime import datetime, timezone
from typing import Optional

from ml.data.schemas.unified import WeatherObservation, DataMode
from ml.data.providers.weather_provider import BaseWeatherProvider

class OpenWeatherAdapter(BaseWeatherProvider):
    """
    OpenWeather API provider.
    Ingests live meteorological surface observations and normalizes all units to scientific standards.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY", "").strip()

    async def get_observation(
        self,
        latitude: float,
        longitude: float,
        timestamp: Optional[datetime] = None
    ) -> WeatherObservation:
        if not self.api_key:
            raise ValueError(
                "OPENWEATHER_API_KEY is not configured. "
                "Use DemoWeatherAdapter for offline execution or configure OPENWEATHER_API_KEY."
            )

        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": self.api_key,
            "units": "metric"
        }

        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        main = data.get("main", {})
        wind = data.get("wind", {})

        # Conversions
        wind_ms = float(wind.get("speed", 0.0))
        wind_kts = round(wind_ms * 1.94384, 1)
        wind_kmh = round(wind_ms * 3.6, 1)

        obs_time = datetime.fromtimestamp(data.get("dt", datetime.now().timestamp()), tz=timezone.utc)

        return WeatherObservation(
            timestamp=obs_time,
            latitude=latitude,
            longitude=longitude,
            temperature_c=float(main.get("temp", 28.0)),
            humidity_pct=float(main.get("humidity", 80.0)),
            pressure_hpa=float(main.get("pressure", 1010.0)),
            wind_speed_kts=wind_kts,
            wind_speed_kmh=wind_kmh,
            wind_direction_deg=float(wind.get("deg", 180.0)),
            source="OpenWeather API (Live)",
            data_mode=DataMode.LIVE,
            metadata={
                "city": data.get("name"),
                "weather_main": data.get("weather", [{}])[0].get("main"),
                "weather_desc": data.get("weather", [{}])[0].get("description")
            }
        )

class DemoWeatherAdapter(BaseWeatherProvider):
    """
    Deterministic meteorological climatology fallback adapter.
    Explicitly tags all outputs as DEMO data.
    """

    async def get_observation(
        self,
        latitude: float,
        longitude: float,
        timestamp: Optional[datetime] = None
    ) -> WeatherObservation:
        t = timestamp or datetime.now(timezone.utc)

        # North Indian Ocean basin coordinates roughly 5N-25N, 60E-95E
        is_bay_of_bengal = (80.0 <= longitude <= 95.0) and (5.0 <= latitude <= 24.0)
        is_arabian_sea = (60.0 <= longitude < 80.0) and (5.0 <= latitude <= 25.0)

        # Baseline physical characteristics
        base_temp = 29.2 if (is_bay_of_bengal or is_arabian_sea) else 27.5
        base_humidity = 82.0 if is_bay_of_bengal else 76.0
        base_pressure = 998.0 if is_bay_of_bengal else 1006.0
        base_wind_kts = 35.0 if is_bay_of_bengal else 18.0
        base_wind_kmh = round(base_wind_kts * 1.852, 1)

        return WeatherObservation(
            timestamp=t,
            latitude=latitude,
            longitude=longitude,
            temperature_c=base_temp,
            humidity_pct=base_humidity,
            pressure_hpa=base_pressure,
            wind_speed_kts=base_wind_kts,
            wind_speed_kmh=base_wind_kmh,
            wind_direction_deg=210.0,
            source="Meteorological Climatology Model (DEMO ADAPTER)",
            data_mode=DataMode.DEMO,
            metadata={"simulation": True, "notice": "Climatological baseline proxy"}
        )
