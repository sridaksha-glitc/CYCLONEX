from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from app.models.schemas import CycloneListResponse, CycloneItem
from app.services.supabase_client import storage_service

router = APIRouter()

@router.get("/cyclones", response_model=CycloneListResponse)
def list_cyclones(status: Optional[str] = Query(None, description="Filter by status: ACTIVE, ARCHIVED")):
    """
    Retrieves active or archived tropical cyclones.
    """
    items = storage_service.get_cyclones(status=status)
    active_count = len([c for c in storage_service.get_cyclones() if c.get("status") == "ACTIVE"])
    
    return CycloneListResponse(
        total=len(items),
        active_count=active_count,
        cyclones=[CycloneItem(**item) for item in items]
    )

@router.get("/cyclones/{id}", response_model=CycloneItem)
def get_cyclone(id: str):
    """
    Retrieves detailed observation, track, and metrics for a specific cyclone.
    """
    item = storage_service.get_cyclone_by_id(id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Cyclone with ID or code '{id}' not found.")
    return CycloneItem(**item)
