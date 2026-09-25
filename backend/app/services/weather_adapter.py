import logging
from typing import Dict, Any, Optional
import httpx
from app.config import settings

logger = logging.getLogger("cyclonex.weather")

class WeatherAdapter:
    """
    Multi-source meteorological data adapter.
    Fetches real-time observations from OpenWeather if an API key is available,
    or falls back cleanly to deterministic meteorological climate models.
    """

    @classmethod
    async def fetch_weather(
        cls, 
        latitude: float, 
        longitude: float, 
        force_live: bool = False
    ) -> Dict[str, Any]:
        api_key = settings.OPENWEATHER_API_KEY.strip()
        
        # 1. Attempt live OpenWeather API if key is present
        if api_key and (force_live or settings.DATA_MODE in ["LIVE", "HYBRID"]):
            try:
                url = f"https://api.openweathermap.org/data/2.5/weather"
                params = {
                    "lat": latitude,
                    "lon": longitude,
                    "appid": api_key,
                    "units": "metric"
                }
                async with httpx.AsyncClient(timeout=4.0) as client:
                    resp = await client.get(url, params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        main = data.get("main", {})
                        wind = data.get("wind", {})
                        
                        wind_ms = float(wind.get("speed", 0.0))
                        wind_kmh = round(wind_ms * 3.6, 1)
                        wind_kts = round(wind_ms * 1.94384, 1)
                        
                        return {
                            "temperature_c": float(main.get("temp", 28.0)),
                            "humidity_pct": float(main.get("humidity", 80.0)),
                            "pressure_hpa": float(main.get("pressure", 1008.0)),
                            "wind_speed_kmh": wind_kmh,
                            "wind_speed_kts": wind_kts,
                            "wind_direction_deg": float(wind.get("deg", 180.0)),
                            "data_mode": "LIVE",
                            "source": "OpenWeather API (Live)"
                        }
                    else:
                        logger.warning(f"OpenWeather returned {resp.status_code}. Falling back to demo adapter.")
            except Exception as e:
                logger.warning(f"Failed to query OpenWeather API: {e}. Falling back to demo adapter.")

        # 2. Deterministic Meteorological Climatology / Demo Fallback
        # Calculates realistic tropical ocean background pressure & winds
        return cls._generate_deterministic_demo(latitude, longitude)

    @classmethod
    def _generate_deterministic_demo(cls, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Generates realistic tropical maritime atmosphere values based on coordinates
        (e.g., North Indian Ocean Bay of Bengal / Arabian Sea cyclogenesis basins).
        """
        # North Indian Ocean basin coordinates roughly 5N-25N, 60E-95E
        is_bay_of_bengal = (80.0 <= longitude <= 95.0) and (5.0 <= latitude <= 24.0)
        is_arabian_sea = (60.0 <= longitude < 80.0) and (5.0 <= latitude <= 25.0)

        # Baseline tropical marine characteristics
        base_temp = 29.2 if (is_bay_of_bengal or is_arabian_sea) else 27.5
        base_humidity = 82.0 if is_bay_of_bengal else 76.0
        
        # Modest cyclonic depression characteristics if in active cyclone breeding zone
        base_pressure = 998.0 if is_bay_of_bengal else 1006.0
        base_wind_kts = 35.0 if is_bay_of_bengal else 18.0
        base_wind_kmh = round(base_wind_kts * 1.852, 1)

        return {
            "temperature_c": base_temp,
            "humidity_pct": base_humidity,
            "pressure_hpa": base_pressure,
            "wind_speed_kmh": base_wind_kmh,
            "wind_speed_kts": base_wind_kts,
            "wind_direction_deg": 210.0,
            "data_mode": "DEMO",
            "source": "Meteorological Climatology Model (DEMO ADAPTER)"
        }
