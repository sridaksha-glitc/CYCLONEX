from fastapi import APIRouter
from typing import Dict, Any
from pydantic import BaseModel, Field

router = APIRouter()

class IngestObservationRequest(BaseModel):
    latitude: float
    longitude: float
    source: str = Field(default="In-situ Weather Sensor")
    temperature_c: float
    humidity_pct: float
    pressure_hpa: float
    wind_speed_kts: float
    wind_direction_deg: float = 180.0
    cyclone_code: str = "INVEST-AUTO"

@router.post("/ingest")
def ingest_observation(req: IngestObservationRequest):
    """
    Ingests multi-source sensor observations into the CYCLONEX telemetry pool.
    """
    return {
        "status": "INGESTED",
        "observation_id": f"obs-{req.cyclone_code}-{int(req.pressure_hpa)}",
        "data_mode": "DEMO",
        "received_payload": req.model_dump()
    }
