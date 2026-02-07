"""
Complaints API endpoints for SEVAFLOW.

Provides REST API for:
- Submitting complaints programmatically
- Retrieving complaint details
- Admin operations
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.models import (
    ComplaintSubmitRequest,
    ComplaintResponse,
    ComplaintListResponse,
    Complaint
)
from app.services.ai_processor import process_complaint
from app.services.router import route_complaint
from app import database

router = APIRouter(prefix="/api/complaints", tags=["Complaints"])


@router.post("/", response_model=ComplaintResponse)
async def submit_complaint(request: ComplaintSubmitRequest):
    """
    Submit a new complaint via API.
    
    This endpoint allows programmatic complaint submission,
    useful for integrations or testing.
    """
    # Process with AI
    ai_result = await process_complaint(request.text)
    
    # Route to department
    department, sla_hours = route_complaint(ai_result)
    
    # Generate ID and create
    complaint_id = await database.get_next_complaint_id()
    
    complaint = await database.create_complaint(
        complaint_id=complaint_id,
        telegram_user_id=request.telegram_user_id,
        user_name=request.user_name,
        raw_text=request.text,
        issue_type=ai_result.issue_type,
        location=ai_result.location,
        department=department,
        priority=ai_result.priority.value,
        summary=ai_result.summary,
        estimated_hours=sla_hours
    )
    
    return ComplaintResponse(
        success=True,
        complaint_id=complaint.complaint_id,
        message="Complaint registered successfully",
        department=complaint.department,
        priority=complaint.priority.value,
        estimated_resolution_hours=sla_hours
    )


@router.get("/", response_model=ComplaintListResponse)
async def list_complaints(
    status: Optional[str] = Query(None, description="Filter by status"),
    department: Optional[str] = Query(None, description="Filter by department"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    List all complaints with optional filters.
    Intended for admin dashboard use.
    """
    complaints, total = await database.get_all_complaints(
        status=status,
        department=department,
        priority=priority,
        page=page,
        per_page=per_page
    )
    
    return ComplaintListResponse(
        total=total,
        page=page,
        per_page=per_page,
        complaints=complaints
    )


@router.get("/{complaint_id}", response_model=Complaint)
async def get_complaint(complaint_id: str):
    """Get details of a specific complaint."""
    complaint = await database.get_complaint_by_id(complaint_id.upper())
    
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    return complaint


@router.get("/{complaint_id}/history")
async def get_complaint_history(complaint_id: str):
    """Get status change history for a complaint."""
    complaint = await database.get_complaint_by_id(complaint_id.upper())
    
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    history = await database.get_status_history(complaint_id.upper())
    
    return {
        "complaint_id": complaint_id.upper(),
        "current_status": complaint.status.value,
        "history": [
            {
                "old_status": h.old_status.value,
                "new_status": h.new_status.value,
                "changed_at": h.changed_at.isoformat(),
                "notes": h.notes,
                "changed_by": h.changed_by
            }
            for h in history
        ]
    }
