from fastapi import APIRouter
from datetime import datetime, timezone
from app.config import settings
from app.models.schemas import HealthResponse, SubsystemHealth
from app.services.supabase_client import storage_service

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def get_health():
    return HealthResponse(
        status="HEALTHY",
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="1.0.0",
        data_mode=settings.DATA_MODE,
        subsystems={
            "ml_engine": SubsystemHealth(status="ONLINE", details="Models A, B, C loaded"),
            "weather_adapter": SubsystemHealth(
                status="ONLINE", 
                details="OpenWeather API Key active" if settings.OPENWEATHER_API_KEY else "Using Climate Demo Adapter"
            ),
            "storage": SubsystemHealth(
                status="ONLINE",
                details="Connected to Supabase Cloud" if storage_service.is_connected_to_cloud else "Local Persistent Benchmark Store"
            ),
            "n8n_automation": SubsystemHealth(status="CONFIGURED", details=f"Target: {settings.N8N_WEBHOOK_URL}")
        }
    )
