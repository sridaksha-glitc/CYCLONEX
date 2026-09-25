from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime
from ml.data.schemas.unified import WeatherObservation

class BaseWeatherProvider(ABC):
    """
    Abstract interface for meteorological atmospheric data.
    Decouples feature fusion from concrete weather APIs (OpenWeather, ERA5 reanalysis, IMD buoys).
    """

    @abstractmethod
    async def get_observation(
        self,
        latitude: float,
        longitude: float,
        timestamp: Optional[datetime] = None
    ) -> WeatherObservation:
        """
        Retrieves normalized surface weather telemetry for given spatial coordinates.
        """
        pass
