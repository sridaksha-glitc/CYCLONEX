import os
import sys

# Automatically ensure backend directory and repository root are on sys.path
# This enables seamless execution on Vercel, Docker, local, and CI environments without manual PYTHONPATH setup
_current_dir = os.path.dirname(os.path.abspath(__file__))  # backend/app
_backend_dir = os.path.abspath(os.path.join(_current_dir, ".."))  # backend
_repo_root = os.path.abspath(os.path.join(_backend_dir, ".."))  # repository root

for _path in [_backend_dir, _repo_root]:
    if _path not in sys.path:
        sys.path.insert(0, _path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone

try:
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
        ingest,
        validation
    )
except ImportError:
    from backend.app.config import settings
    from backend.app.api.v1.endpoints import (
        health,
        analyze,
        detect,
        classify,
        predict,
        cyclones,
        history,
        alerts,
        ingest,
        validation
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
app.include_router(validation.router, prefix=api_v1_prefix, tags=["Scientific Validation"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
