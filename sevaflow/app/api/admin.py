"""
Admin API endpoints for SEVAFLOW.

Provides REST API for administrative operations:
- Dashboard statistics
- Status updates
- Citizen notifications
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional

from app.config import settings
from app.models import StatusUpdateRequest, DashboardStats
from app.services.notifier import notifier
from app.telegram.bot import get_bot
from app import database

router = APIRouter(prefix="/api/admin", tags=["Admin"])


async def verify_admin(x_admin_secret: str = Header(None)):
    """Simple admin authentication via header."""
    if x_admin_secret != settings.admin_secret:
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    return True


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(authorized: bool = Depends(verify_admin)):
    """Get aggregated statistics for the admin dashboard."""
    return await database.get_dashboard_stats()


@router.patch("/complaints/{complaint_id}/status")
async def update_complaint_status(
    complaint_id: str,
    request: StatusUpdateRequest,
    authorized: bool = Depends(verify_admin)
):
    """
    Update the status of a complaint.
    
    Optionally triggers a notification to the citizen.
    """
    # Get current complaint
    complaint = await database.get_complaint_by_id(complaint_id.upper())
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    old_status = complaint.status.value
    new_status = request.new_status.value
    
    # Update status
    updated = await database.update_complaint_status(
        complaint_id=complaint_id.upper(),
        new_status=new_status,
        notes=request.notes,
        changed_by="Admin"
    )
    
    # Send notification if requested and user has Telegram ID
    if request.notify_citizen and updated.telegram_user_id:
        notification = notifier.format_status_update_notification(
            updated,
            old_status,
            new_status,
            request.notes
        )
        
        bot = get_bot()
        await bot.send_notification(updated.telegram_user_id, notification)
    
    return {
        "success": True,
        "complaint_id": complaint_id.upper(),
        "old_status": old_status,
        "new_status": new_status,
        "notified": request.notify_citizen and updated.telegram_user_id is not None
    }


@router.get("/departments")
async def get_departments(authorized: bool = Depends(verify_admin)):
    """Get list of all departments and their SLAs."""
    from app.services.router import get_all_departments, get_department_info
    
    departments = []
    for name in get_all_departments():
        info = get_department_info(name)
        departments.append({
            "name": name,
            "sla_hours": info["sla_hours"],
            "contact": info.get("contact", "N/A")
        })
    
    return {"departments": departments}


@router.post("/notify/{complaint_id}")
async def send_custom_notification(
    complaint_id: str,
    message: str,
    authorized: bool = Depends(verify_admin)
):
    """Send a custom notification to a citizen about their complaint."""
    complaint = await database.get_complaint_by_id(complaint_id.upper())
    
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    if not complaint.telegram_user_id:
        raise HTTPException(status_code=400, detail="No Telegram user linked to this complaint")
    
    formatted_message = f"""
📢 <b>Message from SEVAFLOW</b>

Regarding complaint <code>{complaint_id.upper()}</code>:

{message}

<i>- Administrative Team</i>
"""
    
    bot = get_bot()
    await bot.send_notification(complaint.telegram_user_id, formatted_message.strip())
    
    return {"success": True, "message": "Notification sent"}
