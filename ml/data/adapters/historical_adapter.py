import os
import math
import csv
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from ml.data.schemas.unified import HistoricalCycloneObservation, DataMode
from ml.data.providers.historical_provider import BaseHistoricalProvider

# Authoritative IMD classification standard mapper
def map_wind_to_imd_class(wind_kts: float) -> str:
    if wind_kts < 17:
        return "Low Pressure Area"
    elif wind_kts <= 27:
        return "Depression"
    elif wind_kts <= 33:
        return "Deep Depression"
    elif wind_kts <= 47:
        return "Cyclonic Storm"
    elif wind_kts <= 63:
        return "Severe Cyclonic Storm"
    elif wind_kts <= 89:
        return "Very Severe Cyclonic Storm"
    elif wind_kts <= 119:
        return "Extremely Severe Cyclonic Storm"
    else:
        return "Super Cyclonic Storm"

class IBTrACSAdapter(BaseHistoricalProvider):
    """
    Adapter for authoritative NOAA IBTrACS tropical cyclone track data.
    Parses IBTrACS CSV datasets, maps IMD classification tiers, and computes
    inter-point movement speed and headings.
    """

    def __init__(self, csv_path: Optional[str] = None):
        if not csv_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            csv_path = os.path.join(base_dir, "samples", "historical", "ibtracs_nio_subset.csv")
        self.csv_path = csv_path
        self._records: List[Dict[str, Any]] = []
        self._load_records()

    def _load_records(self):
        if not os.path.exists(self.csv_path):
            return

        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self._records.append(row)

    def list_cyclones(
        self,
        basin: Optional[str] = None,
        min_wind_kts: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        unique_storms: Dict[str, Dict[str, Any]] = {}

        for r in self._records:
            sid = r.get("SID", "")
            name = r.get("NAME", "UNNAMED")
            b = r.get("BASIN", "NI")
            season = r.get("SEASON", "")
            
            try:
                wind = float(r.get("WMO_WIND", 0.0) or 0.0)
            except ValueError:
                wind = 0.0

            if min_wind_kts is not None and wind < min_wind_kts:
                continue

            if sid not in unique_storms:
                unique_storms[sid] = {
                    "cyclone_id": sid,
                    "name": name,
                    "season": season,
                    "basin": "North Indian Ocean" if b == "NI" else b,
                    "peak_wind_kts": wind,
                    "record_count": 0
                }
            else:
                if wind > unique_storms[sid]["peak_wind_kts"]:
                    unique_storms[sid]["peak_wind_kts"] = wind
            
            unique_storms[sid]["record_count"] += 1

        return list(unique_storms.values())

    def get_cyclone_track(self, cyclone_id: str) -> List[HistoricalCycloneObservation]:
        # Filter matching rows by SID or Storm Name
        matches = [
            r for r in self._records 
            if r.get("SID", "").upper() == cyclone_id.upper() or r.get("NAME", "").upper() == cyclone_id.upper()
        ]

        if not matches:
            return []

        # Sort chronologically by ISO_TIME
        matches.sort(key=lambda x: x.get("ISO_TIME", ""))

        observations: List[HistoricalCycloneObservation] = []

        for idx, row in enumerate(matches):
            try:
                w_kts = float(row.get("WMO_WIND") or 35.0)
            except ValueError:
                w_kts = 35.0
            
            try:
                p_hpa = float(row.get("WMO_PRES") or 995.0)
            except ValueError:
                p_hpa = 995.0

            lat = float(row.get("LAT", 0.0))
            lon = float(row.get("LON", 0.0))
            w_kmh = round(w_kts * 1.852, 1)

            # Movement velocity calculation between consecutive track points
            move_speed_kmh: Optional[float] = None
            move_dir_deg: Optional[float] = None

            if idx > 0:
                prev_row = matches[idx - 1]
                p_lat = float(prev_row.get("LAT", lat))
                p_lon = float(prev_row.get("LON", lon))

                t_curr = datetime.fromisoformat(row.get("ISO_TIME", ""))
                t_prev = datetime.fromisoformat(prev_row.get("ISO_TIME", ""))
                dt_hours = max(0.5, (t_curr - t_prev).total_seconds() / 3600.0)

                # Great-circle approximate displacement (km)
                dy = (lat - p_lat) * 111.0
                dx = (lon - p_lon) * 111.0 * math.cos(math.radians((lat + p_lat) / 2.0))
                dist_km = math.sqrt(dx**2 + dy**2)

                move_speed_kmh = round(dist_km / dt_hours, 1)
                deg = math.degrees(math.atan2(dx, dy))
                move_dir_deg = round((deg + 360.0) % 360.0, 1)
            else:
                move_speed_kmh = 15.0
                move_dir_deg = 345.0

            classification = map_wind_to_imd_class(w_kts)
            obs_time = datetime.fromisoformat(row.get("ISO_TIME", "")).replace(tzinfo=timezone.utc)

            observations.append(HistoricalCycloneObservation(
                cyclone_id=row.get("SID", cyclone_id),
                cyclone_name=row.get("NAME", "CYCLONE"),
                timestamp=obs_time,
                latitude=lat,
                longitude=lon,
                wind_kts=w_kts,
                wind_kmh=w_kmh,
                pressure_hpa=p_hpa,
                movement_speed_kmh=move_speed_kmh,
                movement_direction_deg=move_dir_deg,
                classification=classification,
                basin="North Indian Ocean",
                source="NOAA IBTrACS v04r00",
                data_mode=DataMode.HISTORICAL,
                metadata=dict(row)
            ))

        return observations

class DemoHistoricalAdapter(BaseHistoricalProvider):
    """
    Simulated historical track generator for testing and demonstration.
    Explicitly tags all outputs as DEMO data.
    """

    def list_cyclones(self, basin: Optional[str] = None, min_wind_kts: Optional[float] = None) -> List[Dict[str, Any]]:
        return [{
            "cyclone_id": "DEMO-INVEST-91B",
            "name": "Invest 91B (Simulated)",
            "season": "2024",
            "basin": "Bay of Bengal",
            "peak_wind_kts": 35.0,
            "record_count": 3
        }]

    def get_cyclone_track(self, cyclone_id: str) -> List[HistoricalCycloneObservation]:
        now = datetime.now(timezone.utc)
        return [
            HistoricalCycloneObservation(
                cyclone_id="DEMO-INVEST-91B",
                cyclone_name="Invest 91B",
                timestamp=now,
                latitude=12.8,
                longitude=85.4,
                wind_kts=30.0,
                wind_kmh=55.6,
                pressure_hpa=998.0,
                movement_speed_kmh=18.0,
                movement_direction_deg=315.0,
                classification="Deep Depression",
                basin="Bay of Bengal",
                source="Demonstration Historical Generator",
                data_mode=DataMode.DEMO,
                metadata={"simulation": True}
            )
        ]
