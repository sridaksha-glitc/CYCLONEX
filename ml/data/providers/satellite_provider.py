from abc import ABC, abstractmethod
from typing import Optional, Any
from datetime import datetime
from PIL import Image
from ml.data.schemas.unified import SatelliteObservation

class BaseSatelliteProvider(ABC):
    """
    Abstract interface for satellite data ingestion.
    Decouples computer vision inference from specific physical satellite archives
    (e.g., INSAT-3D, INSAT-3DR, NOAA GOES, or local file archives).
    """

    @abstractmethod
    async def get_observation(
        self,
        timestamp: Optional[datetime] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> SatelliteObservation:
        """
        Retrieves a standardized satellite observation and metadata for the requested spatiotemporal coordinate.
        """
        pass

    @abstractmethod
    def load_image(self, observation: SatelliteObservation) -> Image.Image:
        """
        Loads the underlying image object (PIL Image) from path, URL, or buffer.
        """
        pass
