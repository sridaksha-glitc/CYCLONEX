import os
import io
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional
from email.utils import parsedate_to_datetime
import httpx
from PIL import Image

from app.config import settings
from ml.models.detector import CycloneDetector

logger = logging.getLogger("cyclonex.satellite")

class SatelliteService:
    """
    Live Satellite Data Provider for CYCLONEX (Phase 4).
    Acquires and ingests Near-Real-Time (NRT) satellite imagery and products from
    ISRO / MOSDAC / IMD INSAT-3D and INSAT-3DS satellites.

    Supports:
      1. Open NRT INSAT-3D/3DS Asian Sector Infrared (10.8 µm) feed.
      2. Authenticated MOSDAC API (when MOSDAC_USERNAME and MOSDAC_PASSWORD are set).
      3. Strict mode isolation: Never supplies DEMO assets in LIVE mode.
    """

    _last_fetch_time: Optional[datetime] = None
    _cached_result: Optional[Dict[str, Any]] = None
    _CACHE_TTL_SECONDS = 300  # 5 minutes cache to respect satellite update cycle (every 30m)

    @classmethod
    async def fetch_live_satellite(
        cls,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Fetches near-real-time satellite observation from MOSDAC / ISRO INSAT.
        Returns standardized metadata, acquisition timestamp, band, coverage, and extracted features.
        """
        now = datetime.now(timezone.utc)

        # Return cached live result if recent and valid
        if (
            not force_refresh
            and cls._cached_result is not None
            and cls._cached_result.get("available")
            and cls._last_fetch_time is not None
            and (now - cls._last_fetch_time).total_seconds() < cls._CACHE_TTL_SECONDS
        ):
            return cls._cached_result

        # Determine target NRT URL / MOSDAC endpoint
        nrt_url = settings.MOSDAC_NRT_URL or "https://mausam.imd.gov.in/Satellite/3Dasiasec_ir1.jpg"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CYCLONEX-LiveSatelliteEngine/1.0"
        }

        # If MOSDAC credentials are provided, configure HTTP Basic Auth
        auth = None
        if settings.MOSDAC_USERNAME and settings.MOSDAC_PASSWORD:
            auth = (settings.MOSDAC_USERNAME, settings.MOSDAC_PASSWORD)
            logger.info("Using authenticated MOSDAC credentials for satellite product ingestion.")

        try:
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                resp = await client.get(nrt_url, headers=headers, auth=auth)
                if resp.status_code != 200:
                    logger.warning(f"Live satellite provider returned HTTP {resp.status_code}")
                    return cls._create_unavailable_response(
                        f"MOSDAC / INSAT endpoint returned HTTP {resp.status_code}"
                    )

                content_type = resp.headers.get("Content-Type", "")
                if not ("image" in content_type or resp.content[:4] in [b"\xff\xd8\xff\xe0", b"\xff\xd8\xff\xe1", b"\x89PNG"]):
                    return cls._create_unavailable_response(
                        f"Invalid satellite content-type: {content_type}"
                    )

                # Parse acquisition timestamp from Last-Modified header
                acq_time_iso = now.isoformat()
                last_modified_str = resp.headers.get("Last-Modified")
                if last_modified_str:
                    try:
                        acq_dt = parsedate_to_datetime(last_modified_str)
                        if acq_dt.tzinfo is None:
                            acq_dt = acq_dt.replace(tzinfo=timezone.utc)
                        acq_time_iso = acq_dt.astimezone(timezone.utc).isoformat()
                    except Exception as date_err:
                        logger.warning(f"Could not parse Last-Modified header: {date_err}")

                # Process image in-memory
                img_bytes = resp.content
                image = Image.open(io.BytesIO(img_bytes)).convert("L")

                # Extract real computer vision features from the live NRT satellite tile
                features = CycloneDetector.extract_image_features(image)
                # Mark as authentic non-synthetic
                features["is_synthetic_proxy"] = False

                # Cache artifact locally
                cache_dir = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "data", "samples", "satellite")
                )
                os.makedirs(cache_dir, exist_ok=True)
                local_artifact_path = os.path.join(cache_dir, "live_insat_nrt.jpg")
                try:
                    with open(local_artifact_path, "wb") as f:
                        f.write(img_bytes)
                except Exception as save_err:
                    logger.warning(f"Could not persist local satellite cache: {save_err}")
                    local_artifact_path = None

                result = {
                    "available": True,
                    "status": "CONNECTED",
                    "source": "MOSDAC / ISRO INSAT NRT (TIR-1 10.8µm)",
                    "satellite_name": "INSAT-3D / INSAT-3DS",
                    "band": "TIR-1 Infrared (10.8 µm)",
                    "acquisition_timestamp": acq_time_iso,
                    "coverage": "North Indian Ocean Sector (10°S–40°N, 45°E–105°E)",
                    "image_url": nrt_url,
                    "local_path": local_artifact_path,
                    "min_brightness_temp_k": float(features.get("core_temp_k", 220.0)),
                    "cdo_symmetry": float(features.get("cdo_symmetry", 0.65)),
                    "image_features": features,
                    "notice": "Real-time geostationary meteorological radiometry",
                    "reason": None
                }

                cls._cached_result = result
                cls._last_fetch_time = now
                return result

        except Exception as e:
            logger.warning(f"Live satellite query failed: {e}")
            return cls._create_unavailable_response(str(e))

    @classmethod
    def _create_unavailable_response(cls, reason: str) -> Dict[str, Any]:
        """
        Creates an explicit, honest UNAVAILABLE status.
        Never falls back to static demo images in LIVE mode.
        """
        return {
            "available": False,
            "status": "UNAVAILABLE",
            "source": "MOSDAC INSAT NRT (Unavailable)",
            "satellite_name": "INSAT-3D / INSAT-3DS",
            "band": "TIR-1 Infrared (10.8 µm)",
            "acquisition_timestamp": None,
            "coverage": "North Indian Ocean Sector",
            "image_url": None,
            "local_path": None,
            "min_brightness_temp_k": None,
            "cdo_symmetry": None,
            "image_features": None,
            "notice": "Live satellite feed unreachable. Operating in weather-telemetry only mode.",
            "reason": reason
        }
