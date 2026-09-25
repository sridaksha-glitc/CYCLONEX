from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

from app.config import settings
from app.api.v1.endpoints import (
    health,
    analyze,
    detect,
    classify,
    predict,
    cyclones,
    history,
    alerts,
    ingest
)

app = FastAPI(
    title="CYCLONEX Tropical Cyclone Intelligence Platform",
    description="Multi-Source AI/ML Tropical Cyclone Identification, Classification, Prediction & Early Risk Assessment API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root health endpoint
@app.get("/health", tags=["System"])
def root_health():
    return {
        "status": "HEALTHY",
        "service": "CYCLONEX API",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "data_mode": settings.DATA_MODE
    }

# Mount API v1 Routers
api_v1_prefix = "/api/v1"
app.include_router(health.router, prefix=api_v1_prefix, tags=["System Health"])
app.include_router(analyze.router, prefix=api_v1_prefix, tags=["Multi-Source AI Analysis"])
app.include_router(detect.router, prefix=api_v1_prefix, tags=["Model A: Detection"])
app.include_router(classify.router, prefix=api_v1_prefix, tags=["Model B: Classification"])
app.include_router(predict.router, prefix=api_v1_prefix, tags=["Model C: Prediction"])
app.include_router(cyclones.router, prefix=api_v1_prefix, tags=["Cyclone Monitoring"])
app.include_router(history.router, prefix=api_v1_prefix, tags=["Historical Climatology"])
app.include_router(alerts.router, prefix=api_v1_prefix, tags=["Automated Alerting"])
app.include_router(ingest.router, prefix=api_v1_prefix, tags=["Observation Ingest"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
