from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ml.data.schemas.unified import HistoricalCycloneObservation

class BaseHistoricalProvider(ABC):
    """
    Abstract interface for authoritative historical cyclone archives (e.g. NOAA IBTrACS, IMD RSMC).
    """

    @abstractmethod
    def get_cyclone_track(self, cyclone_id: str) -> List[HistoricalCycloneObservation]:
        """
        Retrieves full temporal chronological track points for a designated storm.
        """
        pass

    @abstractmethod
    def list_cyclones(
        self, 
        basin: Optional[str] = None, 
        min_wind_kts: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Lists available historical storm systems matching criteria.
        """
        pass
