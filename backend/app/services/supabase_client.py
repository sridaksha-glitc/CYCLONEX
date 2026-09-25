import logging
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import httpx
from app.config import settings

logger = logging.getLogger("cyclonex.storage")

# Benchmark Initial In-Memory / Local Seed Data
BENCHMARK_CYCLONES = [
    {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567801",
        "code": "BOB-01-2024",
        "name": "Cyclone Remal",
        "basin": "Bay of Bengal",
        "status": "ACTIVE",
        "classification": "Severe Cyclonic Storm",
        "current_lat": 21.4,
        "current_lon": 89.2,
        "max_sustained_wind_kts": 60.0,
        "central_pressure_hpa": 978.0,
        "movement_speed_kmh": 16.0,
        "movement_direction_deg": 355.0,
        "risk_level": "HIGH",
        "risk_score": 78,
        "data_mode": "HISTORICAL",
        "started_at": "2024-05-24T12:00:00Z",
        "last_updated_at": "2024-05-26T18:00:00Z"
    },
    {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567802",
        "code": "ARB-02-2023",
        "name": "Cyclone Biparjoy",
        "basin": "Arabian Sea",
        "status": "ARCHIVED",
        "classification": "Extremely Severe Cyclonic Storm",
        "current_lat": 22.8,
        "current_lon": 68.1,
        "max_sustained_wind_kts": 90.0,
        "central_pressure_hpa": 954.0,
        "movement_speed_kmh": 12.0,
        "movement_direction_deg": 45.0,
        "risk_level": "EXTREME",
        "risk_score": 92,
        "data_mode": "HISTORICAL",
        "started_at": "2023-06-06T06:00:00Z",
        "last_updated_at": "2023-06-15T15:00:00Z"
    },
    {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567803",
        "code": "BOB-06-2023",
        "name": "Cyclone Michaung",
        "basin": "Bay of Bengal",
        "status": "ARCHIVED",
        "classification": "Severe Cyclonic Storm",
        "current_lat": 15.2,
        "current_lon": 80.5,
        "max_sustained_wind_kts": 55.0,
        "central_pressure_hpa": 986.0,
        "movement_speed_kmh": 14.0,
        "movement_direction_deg": 350.0,
        "risk_level": "HIGH",
        "risk_score": 72,
        "data_mode": "HISTORICAL",
        "started_at": "2023-12-01T00:00:00Z",
        "last_updated_at": "2023-12-05T12:00:00Z"
    },
    {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567804",
        "code": "INVEST-91B",
        "name": "Invest 91B (Early Stage)",
        "basin": "Bay of Bengal",
        "status": "ACTIVE",
        "classification": "Deep Depression",
        "current_lat": 12.8,
        "current_lon": 85.4,
        "max_sustained_wind_kts": 30.0,
        "central_pressure_hpa": 998.0,
        "movement_speed_kmh": 18.0,
        "movement_direction_deg": 315.0,
        "risk_level": "MODERATE",
        "risk_score": 46,
        "data_mode": "DEMO",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "last_updated_at": datetime.now(timezone.utc).isoformat()
    }
]

BENCHMARK_ALERTS = [
    {
        "id": "alt-001",
        "cyclone_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567801",
        "cyclone_name": "Cyclone Remal",
        "title": "Landfall Trajectory Alert: Cyclone Remal",
        "message": "Cyclone Remal sustained winds 60 kts. Landfall anticipated near coastal Bengal/Bangladesh delta within 14 hours. High storm surge expected.",
        "severity": "WARNING",
        "risk_score": 78,
        "risk_level": "HIGH",
        "n8n_dispatched": True,
        "channels": ["webhook", "dashboard", "sms"],
        "dispatched_at": datetime.now(timezone.utc).isoformat()
    }
]

class SupabaseStorageService:
    """
    Dual-mode persistence engine.
    Uses Supabase REST API if configured, otherwise falls back to local in-memory
    pre-seeded benchmark store for 100% offline hackathon reliability.
    """

    def __init__(self):
        self.supabase_url = settings.SUPABASE_URL.strip().rstrip("/")
        self.supabase_key = settings.SUPABASE_KEY.strip()
        self.is_connected_to_cloud = bool(self.supabase_url and self.supabase_key and not self.supabase_url.startswith("https://your-project"))
        
        # Local Fallback Store
        self._cyclones: Dict[str, Dict[str, Any]] = {c["id"]: dict(c) for c in BENCHMARK_CYCLONES}
        self._alerts: List[Dict[str, Any]] = list(BENCHMARK_ALERTS)
        self._model_runs: List[Dict[str, Any]] = []
        self._weather_observations: List[Dict[str, Any]] = []
        self._predictions: List[Dict[str, Any]] = []

    def get_cyclones(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        cyclones_list = list(self._cyclones.values())
        if status:
            cyclones_list = [c for c in cyclones_list if c.get("status", "").upper() == status.upper()]
        return cyclones_list

    def get_cyclone_by_id(self, cyclone_id: str) -> Optional[Dict[str, Any]]:
        # Match by ID or Code
        for c in self._cyclones.values():
            if c["id"] == cyclone_id or c.get("code") == cyclone_id:
                return dict(c)
        return None

    def upsert_cyclone(self, cyclone_data: Dict[str, Any]) -> Dict[str, Any]:
        cid = cyclone_data.get("id") or str(uuid.uuid4())
        cyclone_data["id"] = cid
        cyclone_data["last_updated_at"] = datetime.now(timezone.utc).isoformat()
        self._cyclones[cid] = cyclone_data

        if self.is_connected_to_cloud:
            try:
                headers = {
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json",
                    "Prefer": "resolution=merge-duplicates"
                }
                httpx.post(f"{self.supabase_url}/rest/v1/cyclones", json=cyclone_data, headers=headers, timeout=2.0)
            except Exception as e:
                logger.warning(f"Could not persist cyclone to remote Supabase ({e}). Persisted locally.")

        return cyclone_data

    def record_weather_observation(self, obs_data: Dict[str, Any]) -> Dict[str, Any]:
        oid = obs_data.get("id") or str(uuid.uuid4())
        obs_data["id"] = oid
        obs_data["created_at"] = datetime.now(timezone.utc).isoformat()
        self._weather_observations.insert(0, obs_data)

        if self.is_connected_to_cloud:
            try:
                headers = {
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json"
                }
                httpx.post(f"{self.supabase_url}/rest/v1/weather_observations", json=obs_data, headers=headers, timeout=2.0)
            except Exception as e:
                logger.warning(f"Could not persist weather observation to remote Supabase ({e}). Persisted locally.")

        return obs_data

    def record_prediction(self, pred_data: Dict[str, Any]) -> Dict[str, Any]:
        pid = pred_data.get("id") or str(uuid.uuid4())
        pred_data["id"] = pid
        pred_data["created_at"] = datetime.now(timezone.utc).isoformat()
        self._predictions.insert(0, pred_data)

        if self.is_connected_to_cloud:
            try:
                headers = {
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json"
                }
                httpx.post(f"{self.supabase_url}/rest/v1/predictions", json=pred_data, headers=headers, timeout=2.0)
            except Exception as e:
                logger.warning(f"Could not persist prediction to remote Supabase ({e}). Persisted locally.")

        return pred_data

    def record_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        aid = alert_data.get("id") or f"alt-{uuid.uuid4().hex[:8]}"
        alert_data["id"] = aid
        alert_data["dispatched_at"] = datetime.now(timezone.utc).isoformat()
        self._alerts.insert(0, alert_data)

        if self.is_connected_to_cloud:
            try:
                headers = {
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json"
                }
                httpx.post(f"{self.supabase_url}/rest/v1/alerts", json=alert_data, headers=headers, timeout=2.0)
            except Exception as e:
                logger.warning(f"Could not persist alert to remote Supabase ({e}). Persisted locally.")

        return alert_data

    def get_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._alerts[:limit]

    def get_weather_observations(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._weather_observations[:limit]

    def get_predictions(self, cyclone_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        if cyclone_id:
            return [p for p in self._predictions if p.get("cyclone_id") == cyclone_id][:limit]
        return self._predictions[:limit]

    def log_model_run(self, model_name: str, inputs: Dict[str, Any], outputs: Dict[str, Any], explanation: Optional[Any] = None) -> None:
        run_record = {
            "id": str(uuid.uuid4()),
            "model_name": model_name,
            "inputs": inputs,
            "outputs": outputs,
            "explanation": explanation,
            "executed_at": datetime.now(timezone.utc).isoformat()
        }
        self._model_runs.append(run_record)

        if self.is_connected_to_cloud:
            try:
                headers = {
                    "apikey": self.supabase_key,
                    "Authorization": f"Bearer {self.supabase_key}",
                    "Content-Type": "application/json"
                }
                httpx.post(f"{self.supabase_url}/rest/v1/model_runs", json=run_record, headers=headers, timeout=2.0)
            except Exception as e:
                logger.warning(f"Could not persist model run to remote Supabase ({e}). Persisted locally.")

storage_service = SupabaseStorageService()

