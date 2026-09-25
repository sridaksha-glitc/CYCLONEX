import os
import json
import numpy as np
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from PIL import Image

from ml.data.schemas.unified import SatelliteObservation, DataMode
from ml.data.providers.satellite_provider import BaseSatelliteProvider

class LocalSatelliteAdapter(BaseSatelliteProvider):
    """
    Adapter for loading satellite imagery from local archives and curated datasets.
    Does NOT require a live network connection, preventing external blockers.
    """

    def __init__(self, archive_dir: Optional[str] = None):
        if not archive_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            archive_dir = os.path.join(base_dir, "samples", "satellite")
        self.archive_dir = archive_dir

    async def get_observation(
        self,
        timestamp: Optional[datetime] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> SatelliteObservation:
        """
        Loads matching satellite metadata and image path from the local archive.
        Matches by nearest coordinates or default sample.
        """
        sample_meta_files = [f for f in os.listdir(self.archive_dir) if f.endswith(".json")]
        if not sample_meta_files:
            raise FileNotFoundError(f"No satellite metadata samples located in {self.archive_dir}")

        chosen_meta = None
        min_dist = float("inf")

        for meta_file in sample_meta_files:
            meta_path = os.path.join(self.archive_dir, meta_file)
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            if latitude is not None and longitude is not None:
                s_lat = data.get("latitude", 0.0)
                s_lon = data.get("longitude", 0.0)
                dist = ((s_lat - latitude) ** 2 + (s_lon - longitude) ** 2) ** 0.5
                if dist < min_dist:
                    min_dist = dist
                    chosen_meta = data
                    chosen_meta["_base_name"] = meta_file.replace(".json", "")
            else:
                chosen_meta = data
                chosen_meta["_base_name"] = meta_file.replace(".json", "")
                break

        img_file_png = os.path.join(self.archive_dir, f"{chosen_meta['_base_name']}.png")
        if not os.path.exists(img_file_png):
            img_file_png = None

        obs_time = datetime.fromisoformat(chosen_meta["timestamp"].replace("Z", "+00:00"))

        return SatelliteObservation(
            timestamp=obs_time,
            latitude=chosen_meta.get("latitude"),
            longitude=chosen_meta.get("longitude"),
            source=chosen_meta.get("source", "INSAT-3D Archive"),
            data_mode=DataMode(chosen_meta.get("data_mode", "HISTORICAL")),
            image_path=img_file_png,
            channel=chosen_meta.get("channel", "IR-10.8um"),
            min_brightness_temp_k=chosen_meta.get("min_brightness_temp_k"),
            cdo_symmetry=chosen_meta.get("cdo_symmetry"),
            metadata=chosen_meta
        )

    def load_image(self, observation: SatelliteObservation) -> Image.Image:
        if not observation.image_path or not os.path.exists(observation.image_path):
            # Create a fallback placeholder image
            arr = np.full((128, 128), 128, dtype=np.uint8)
            return Image.fromarray(arr)
        return Image.open(observation.image_path).convert("L")

class DemoSatelliteAdapter(BaseSatelliteProvider):
    """
    Demonstration satellite provider producing synthetic IR tiles.
    Explicitly tags all outputs with data_mode = DEMO.
    """

    async def get_observation(
        self,
        timestamp: Optional[datetime] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None
    ) -> SatelliteObservation:
        t = timestamp or datetime.now(timezone.utc)
        lat = latitude if latitude is not None else 14.5
        lon = longitude if longitude is not None else 86.2

        return SatelliteObservation(
            timestamp=t,
            latitude=lat,
            longitude=lon,
            source="Procedural Synthetic Satellite Adapter",
            data_mode=DataMode.DEMO,
            image_path=None,
            channel="IR-10.8um",
            min_brightness_temp_k=218.5,
            cdo_symmetry=0.68,
            metadata={"simulation": True, "notice": "Procedural demo proxy"}
        )

    def load_image(self, observation: SatelliteObservation) -> Image.Image:
        # Generate synthetic vortex array
        y, x = np.ogrid[:128, :128]
        dist = np.sqrt((x - 64)**2 + (y - 64)**2)
        arr = np.clip(220 - (dist * 2.0) + np.sin(dist / 6.0) * 30, 20, 255).astype(np.uint8)
        return Image.fromarray(arr)
