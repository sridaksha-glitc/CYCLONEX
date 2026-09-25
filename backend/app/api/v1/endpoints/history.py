from fastapi import APIRouter
from typing import List, Dict, Any

router = APIRouter()

# Authoritative IBTrACS historical cyclones for North Indian Ocean validation
HISTORICAL_STORMS = [
    {
        "name": "Cyclone Remal",
        "year": 2024,
        "basin": "Bay of Bengal",
        "max_category": "Severe Cyclonic Storm",
        "peak_wind_kts": 60,
        "min_pressure_hpa": 978,
        "landfall_area": "West Bengal & Bangladesh coast",
        "impact": "1.5m surge, heavy rainfall, high wind destruction",
        "data_source": "IBTrACS / IMD RSMC New Delhi"
    },
    {
        "name": "Cyclone Michaung",
        "year": 2023,
        "basin": "Bay of Bengal",
        "max_category": "Severe Cyclonic Storm",
        "peak_wind_kts": 55,
        "min_pressure_hpa": 986,
        "landfall_area": "Bapatla, Andhra Pradesh",
        "impact": "Catastrophic urban flooding in Chennai and coastal AP",
        "data_source": "IBTrACS / IMD RSMC New Delhi"
    },
    {
        "name": "Cyclone Biparjoy",
        "year": 2023,
        "basin": "Arabian Sea",
        "max_category": "Extremely Severe Cyclonic Storm",
        "peak_wind_kts": 90,
        "min_pressure_hpa": 954,
        "landfall_area": "Naliya, Gujarat",
        "impact": "Extensive coastal infrastructure damage, gale winds",
        "data_source": "IBTrACS / IMD RSMC New Delhi"
    },
    {
        "name": "Cyclone Tauktae",
        "year": 2021,
        "basin": "Arabian Sea",
        "max_category": "Extremely Severe Cyclonic Storm",
        "peak_wind_kts": 100,
        "min_pressure_hpa": 950,
        "landfall_area": "Saurashtra, Gujarat",
        "impact": "Severe maritime surge, offshore rig evacuations",
        "data_source": "IBTrACS / IMD RSMC New Delhi"
    },
    {
        "name": "Cyclone Amphan",
        "year": 2020,
        "basin": "Bay of Bengal",
        "max_category": "Super Cyclonic Storm",
        "peak_wind_kts": 130,
        "min_pressure_hpa": 920,
        "landfall_area": "Sundarbans delta",
        "impact": "Record-breaking $13B damage, severe tidal inundation",
        "data_source": "IBTrACS / IMD RSMC New Delhi"
    }
]

@router.get("/history")
def get_historical_analogs():
    """
    Returns curated authoritative historical cyclone benchmarks from IBTrACS.
    """
    return {
        "dataset": "NOAA IBTrACS v04r00 / IMD RSMC Archives",
        "total_records": len(HISTORICAL_STORMS),
        "data_mode": "HISTORICAL",
        "storms": HISTORICAL_STORMS
    }
