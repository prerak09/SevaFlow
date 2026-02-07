"""
Pydantic models for SEVAFLOW.
Defines data structures for complaints, API requests/responses.
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel, Field


class PriorityLevel(str, Enum):
    """Complaint priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ComplaintStatus(str, Enum):
    """Complaint lifecycle statuses."""
    SUBMITTED = "submitted"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


# ============================================================
# AI Processing Models
# ============================================================

class AIExtractionResult(BaseModel):
    """
    Structured output from AI complaint processing.
    This is what the LLM returns after analyzing citizen input.
    """
    issue_type: str = Field(description="Category of the complaint")
    location: str = Field(description="Location/address mentioned in complaint")
    responsible_department: str = Field(description="Suggested department for handling")
    priority: PriorityLevel = Field(default=PriorityLevel.MEDIUM)
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    summary: str = Field(default="", description="Brief summary of the complaint")


# ============================================================
# Database Models
# ============================================================

class ComplaintBase(BaseModel):
    """Base complaint data."""
    raw_text: str = Field(description="Original complaint text from citizen")
    telegram_user_id: Optional[int] = None
    user_name: Optional[str] = None


class ComplaintCreate(ComplaintBase):
    """Data for creating a new complaint."""
    pass


class Complaint(ComplaintBase):
    """Full complaint record as stored in database."""
    id: int
    complaint_id: str = Field(description="Human-readable ID like SF-1001")
    issue_type: str
    location: str
    department: str
    priority: PriorityLevel
    status: ComplaintStatus = ComplaintStatus.SUBMITTED
    summary: str = ""
    estimated_resolution_hours: int = 48
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class StatusHistoryEntry(BaseModel):
    """Record of a status change."""
    id: int
    complaint_id: str
    old_status: ComplaintStatus
    new_status: ComplaintStatus
    changed_at: datetime
    notes: Optional[str] = None
    changed_by: Optional[str] = None


# ============================================================
# API Request/Response Models
# ============================================================

class ComplaintSubmitRequest(BaseModel):
    """Request body for submitting a new complaint via API."""
    text: str = Field(min_length=10, description="Complaint description")
    telegram_user_id: Optional[int] = None
    user_name: Optional[str] = None


class ComplaintResponse(BaseModel):
    """API response after complaint submission."""
    success: bool
    complaint_id: str
    message: str
    department: str
    priority: str
    estimated_resolution_hours: int


class StatusUpdateRequest(BaseModel):
    """Request body for updating complaint status."""
    new_status: ComplaintStatus
    notes: Optional[str] = None
    notify_citizen: bool = True


class ComplaintListResponse(BaseModel):
    """Paginated list of complaints."""
    total: int
    page: int
    per_page: int
    complaints: List[Complaint]


class DashboardStats(BaseModel):
    """Statistics for admin dashboard."""
    total_complaints: int
    pending: int
    in_progress: int
    resolved: int
    escalated: int
    by_department: dict
    by_priority: dict
    avg_resolution_hours: Optional[float]


# ============================================================
# Telegram Bot Models
# ============================================================

class TelegramUser(BaseModel):
    """Telegram user info."""
    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None


class BotMessage(BaseModel):
    """Formatted message for Telegram bot."""
    text: str
    parse_mode: str = "HTML"
