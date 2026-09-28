import logging
import urllib.parse
from typing import Dict, Any, Optional
import httpx
from app.config import settings

logger = logging.getLogger("cyclonex.weather")


def _sanitize_secret(text: str, secret: Optional[str]) -> str:
    """Scrub sensitive API key from strings, error messages, and URLs to prevent credential leaks."""
    if not text or not secret:
        return text
    clean_secret = secret.strip()
    if clean_secret and clean_secret in text:
        text = text.replace(clean_secret, "[REDACTED]")
    try:
        encoded = urllib.parse.quote(clean_secret)
        if encoded and encoded in text:
            text = text.replace(encoded, "[REDACTED]")
    except Exception:
        pass
    return text


class SensitiveDataFilter(logging.Filter):
    """Logging filter ensuring API secrets are never emitted to logs or console by any logger."""
    def __init__(self, secret: Optional[str] = None):
        super().__init__()
        self.secret = secret

    def filter(self, record: logging.LogRecord) -> bool:
        sec = (self.secret or getattr(settings, "OPENWEATHER_API_KEY", "")).strip()
        if sec and len(sec) >= 4:
            if isinstance(record.msg, str) and sec in record.msg:
                record.msg = record.msg.replace(sec, "[REDACTED]")
            if record.args:
                if isinstance(record.args, dict):
                    record.args = {
                        k: (v.replace(sec, "[REDACTED]") if isinstance(v, str) and sec in v else v)
                        for k, v in record.args.items()
                    }
                elif isinstance(record.args, tuple):
                    record.args = tuple(
                        (a.replace(sec, "[REDACTED]") if isinstance(a, str) and sec in a else a)
                        for a in record.args
                    )
        return True


# Attach secret scrubbing filter to root logger
_filter = SensitiveDataFilter()
logging.getLogger().addFilter(_filter)
# Suppress httpx internal request logs which might include query strings
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


class WeatherAdapter:
    """
    Multi-source meteorological data adapter.
    Fetches real-time observations from OpenWeather if an API key is configured,
    or returns OPENWEATHER_NOT_CONFIGURED status while preserving cyclone telemetry.
    Never exposes or logs the raw API key.
    """

    @classmethod
    async def fetch_weather(
        cls, 
        latitude: float, 
        longitude: float, 
        force_live: bool = False,
        data_mode: str = "DEMO"
    ) -> Dict[str, Any]:
        api_key = settings.OPENWEATHER_API_KEY.strip()
        is_live = (data_mode == "LIVE") or force_live
        
        # 1. LIVE MODE:
        if is_live:
            if not api_key:
                # Key is missing: do NOT use fake weather data, return clear unconfigured status
                return {
                    "temperature_c": None,
                    "humidity_pct": None,
                    "pressure_hpa": None,
                    "wind_speed_kmh": None,
                    "wind_speed_kts": None,
                    "wind_direction_deg": None,
                    "cloud_pct": None,
                    "observed_at": None,
                    "city": None,
                    "coordinates": {"latitude": latitude, "longitude": longitude},
                    "data_mode": "LIVE",
                    "source": "OpenWeather Current Weather (Unconfigured)",
                    "status": "OPENWEATHER_NOT_CONFIGURED"
                }

            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": api_key,
                "units": "metric"
            }
            try:
                async with httpx.AsyncClient(timeout=6.0) as client:
                    resp = await client.get(url, params=params)
                    if resp.status_code == 401:
                        raise ValueError("OPENWEATHER_SOURCE_ERROR: Invalid OpenWeather API key (401 Unauthorized).")
                    elif resp.status_code != 200:
                        raise ValueError(f"OPENWEATHER_SOURCE_ERROR: OpenWeather API returned HTTP {resp.status_code}.")
                    
                    data = resp.json()
                    main = data.get("main", {})
                    wind = data.get("wind", {})
                    clouds = data.get("clouds", {})
                    
                    wind_ms = float(wind.get("speed", 0.0))
                    wind_kmh = round(wind_ms * 3.6, 1)
                    wind_kts = round(wind_ms * 1.94384, 1)

                    from datetime import datetime, timezone
                    dt = data.get("dt")
                    obs_time = (
                        datetime.fromtimestamp(dt, tz=timezone.utc).isoformat()
                        if dt else datetime.now(timezone.utc).isoformat()
                    )
                    
                    return {
                        "temperature_c": float(main.get("temp", 28.0)),
                        "humidity_pct": float(main.get("humidity", 80.0)),
                        "pressure_hpa": float(main.get("pressure", 1008.0)),
                        "wind_speed_kmh": wind_kmh,
                        "wind_speed_kts": wind_kts,
                        "wind_direction_deg": float(wind.get("deg", 180.0)),
                        "cloud_pct": float(clouds.get("all", 0.0)),
                        "observed_at": obs_time,
                        "city": data.get("name"),
                        "coordinates": {"latitude": latitude, "longitude": longitude},
                        "data_mode": "LIVE",
                        "source": "OpenWeather Current Weather (Live Telemetry)",
                        "status": "CONNECTED"
                    }
            except Exception as e:
                raw_err = str(e)
                clean_err = _sanitize_secret(raw_err, api_key)
                logger.error(f"Live OpenWeather fetch failed: {clean_err}")
                if "OPENWEATHER_SOURCE_ERROR" in raw_err:
                    raise ValueError(clean_err)
                raise ValueError(f"OPENWEATHER_SOURCE_ERROR: Could not connect to OpenWeather: {clean_err}")

        # 2. Deterministic Meteorological Climatology / Demo Fallback for non-live modes
        return cls._generate_deterministic_demo(latitude, longitude)

    @classmethod
    def _generate_deterministic_demo(cls, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Generates realistic tropical maritime atmosphere values based on coordinates
        (e.g., North Indian Ocean Bay of Bengal / Arabian Sea cyclogenesis basins).
        """
        is_bay_of_bengal = (80.0 <= longitude <= 95.0) and (5.0 <= latitude <= 24.0)
        is_arabian_sea = (60.0 <= longitude < 80.0) and (5.0 <= latitude <= 25.0)

        base_temp = 29.2 if (is_bay_of_bengal or is_arabian_sea) else 27.5
        base_humidity = 82.0 if is_bay_of_bengal else 76.0
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
