# CYCLONEX n8n Automated Alerting Engine

This directory contains the n8n automation workflow definition for CYCLONEX.

## Setup Instructions

1. **Start n8n**:
   ```bash
   npx n8n
   # or with docker:
   # docker run -it --rm --name n8n -p 5678:5678 -v ~/.n8n:/home/node/.n8n n8nio/n8n
   ```

2. **Import Workflow**:
   * Open `http://localhost:5678`
   * Click **Workflows** -> **Import from File**
   * Select `cyclonex_alert_workflow.json`
   * Click **Save** and toggle the workflow to **Active**

3. **Backend Integration**:
   * The CYCLONEX FastAPI backend sends a POST payload to:
     `POST http://localhost:5678/webhook/cyclonex-alert`
   * Whenever `POST /api/v1/alerts` is called or an analysis results in a risk score exceeding threshold ($PRI \ge 60$), the alert service pushes the structured incident to this webhook.

4. **Payload Schema**:
   ```json
   {
     "cyclone_name": "Cyclone Remal",
     "classification": "Severe Cyclonic Storm",
     "severity": "WARNING",
     "risk_score": 78,
     "risk_level": "HIGH",
     "wind_speed_kts": 60,
     "pressure_hpa": 978,
     "latitude": 21.4,
     "longitude": 89.2
   }
   ```
