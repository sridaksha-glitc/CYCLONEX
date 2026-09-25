from fastapi import APIRouter
from typing import List
from app.models.schemas import AlertRequest, AlertResponse
from app.services.alert_service import alert_service
from app.services.supabase_client import storage_service

router = APIRouter()

@router.post("/alerts", response_model=AlertResponse)
async def trigger_manual_alert(req: AlertRequest):
    """
    Triggers an automated alert and dispatches it to configured channels (including n8n).
    """
    res = await alert_service.dispatch_alert(req.model_dump())
    return AlertResponse(
        id=res["id"],
        status="DISPATCHED",
        severity=res["severity"],
        title=res["title"],
        message=res["message"],
        risk_score=res["risk_score"],
        n8n_dispatched=res["n8n_dispatched"],
        channels=res["channels"],
        dispatched_at=res["dispatched_at"]
    )

@router.get("/alerts")
def list_alerts():
    """
    Lists recent dispatched cyclone advisories and emergency alerts.
    """
    alerts = storage_service.get_alerts()
    return {"total": len(alerts), "alerts": alerts}
