import os
import json
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter()

@router.get("/validation/scientific-benchmark")
def get_scientific_benchmark() -> Dict[str, Any]:
    """
    Read-only scientific validation benchmark results.
    Presents the Leave-One-Cyclone-Out (LOCO) wind-excluded benchmark alongside
    the calibrated baseline benchmark for transparent research comparison.
    """
    # __file__ is in backend/app/api/v1/endpoints/ -> 5 levels up to repo root
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
    results_path = os.path.join(base_dir, "ml", "validation", "scientific_benchmark_results.json")
    audit_path = os.path.join(base_dir, "ml", "validation", "feature_audit.json")

    if not os.path.exists(results_path):
        raise HTTPException(status_code=404, detail="Scientific benchmark results artifact not found")

    try:
        with open(results_path, "r", encoding="utf-8") as f:
            benchmark_data = json.load(f)
            
        feature_audit = None
        if os.path.exists(audit_path):
            with open(audit_path, "r", encoding="utf-8") as f:
                feature_audit = json.load(f)

        return {
            "scientific_benchmark": benchmark_data,
            "feature_audit": feature_audit
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read scientific benchmark: {str(e)}")
