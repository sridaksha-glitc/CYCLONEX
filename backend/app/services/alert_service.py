import logging
from typing import Dict, Any
import httpx
from app.config import settings
from app.services.supabase_client import storage_service

logger = logging.getLogger("cyclonex.alerts")

class AlertService:
    """
    Automated Alert Dispatch Engine.
    Dispatches critical alerts to configured n8n webhook workflows and stores alerts.
    """

    @classmethod
    async def dispatch_alert(cls, alert_payload: Dict[str, Any]) -> Dict[str, Any]:
        webhook_url = settings.N8N_WEBHOOK_URL.strip()
        n8n_dispatched = False

        if webhook_url:
            try:
                async with httpx.AsyncClient(timeout=3.0) as client:
                    resp = await client.post(webhook_url, json={"body": alert_payload})
                    if resp.status_code in [200, 201, 202]:
                        n8n_dispatched = True
                        logger.info(f"Successfully dispatched alert to n8n webhook {webhook_url}")
                    else:
                        logger.warning(f"n8n webhook returned status code: {resp.status_code}")
            except Exception as e:
                logger.warning(f"Could not reach n8n webhook ({e}). Alert logged locally.")

        alert_record = {
            "cyclone_id": alert_payload.get("cyclone_id"),
            "cyclone_name": alert_payload.get("cyclone_name", "Unassigned"),
            "title": f"{alert_payload.get('severity', 'WARNING')}: {alert_payload.get('cyclone_name', 'Cyclone Alert')}",
            "message": alert_payload.get("message") or (
                f"{alert_payload.get('classification')} detected. Risk index: {alert_payload.get('risk_score')}/100. "
                f"Winds: {alert_payload.get('wind_speed_kts')} kts, Pressure: {alert_payload.get('pressure_hpa')} hPa."
            ),
            "severity": alert_payload.get("severity", "WARNING"),
            "risk_score": alert_payload.get("risk_score", 60),
            "risk_level": alert_payload.get("risk_level", "HIGH"),
            "status": "SENT" if n8n_dispatched else "LOGGED_LOCALLY",
            "n8n_dispatched": n8n_dispatched,
            "channels": ["n8n_webhook", "dashboard"] if n8n_dispatched else ["dashboard_local"]
        }

        saved = storage_service.record_alert(alert_record)
        return saved

alert_service = AlertService()
