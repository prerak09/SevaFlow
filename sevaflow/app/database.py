"""
Database layer for SEVAFLOW.
Uses SQLite with aiosqlite for async operations.
"""

import aiosqlite
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import json

from app.models import (
    Complaint, ComplaintStatus, PriorityLevel,
    StatusHistoryEntry, DashboardStats
)

# Database file path
DB_PATH = Path(__file__).resolve().parent.parent / "sevaflow.db"


async def init_db():
    """Initialize database with required tables."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Enable foreign keys
        await db.execute("PRAGMA foreign_keys = ON")
        
        # Complaints table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                complaint_id TEXT UNIQUE NOT NULL,
                telegram_user_id INTEGER,
                user_name TEXT,
                raw_text TEXT NOT NULL,
                issue_type TEXT NOT NULL,
                location TEXT NOT NULL,
                department TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'medium',
                status TEXT NOT NULL DEFAULT 'submitted',
                summary TEXT DEFAULT '',
                estimated_resolution_hours INTEGER DEFAULT 48,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Status history table for audit trail
        await db.execute("""
            CREATE TABLE IF NOT EXISTS status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                complaint_id TEXT NOT NULL,
                old_status TEXT NOT NULL,
                new_status TEXT NOT NULL,
                changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                changed_by TEXT,
                FOREIGN KEY (complaint_id) REFERENCES complaints(complaint_id)
            )
        """)
        
        # Create indexes for common queries
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_complaints_status ON complaints(status)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_complaints_department ON complaints(department)
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_complaints_telegram_user ON complaints(telegram_user_id)
        """)
        
        await db.commit()
        print("✅ Database initialized successfully")


async def get_next_complaint_id() -> str:
    """Generate next sequential complaint ID (SF-XXXX format)."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT MAX(id) FROM complaints")
        row = await cursor.fetchone()
        next_id = (row[0] or 0) + 1
        return f"SF-{next_id:04d}"


async def create_complaint(
    complaint_id: str,
    telegram_user_id: Optional[int],
    user_name: Optional[str],
    raw_text: str,
    issue_type: str,
    location: str,
    department: str,
    priority: str,
    summary: str,
    estimated_hours: int
) -> Complaint:
    """Create a new complaint record."""
    async with aiosqlite.connect(DB_PATH) as db:
        now = datetime.now()
        
        await db.execute("""
            INSERT INTO complaints (
                complaint_id, telegram_user_id, user_name, raw_text,
                issue_type, location, department, priority, status,
                summary, estimated_resolution_hours, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            complaint_id, telegram_user_id, user_name, raw_text,
            issue_type, location, department, priority, "submitted",
            summary, estimated_hours, now, now
        ))
        
        # Also create initial status history entry
        await db.execute("""
            INSERT INTO status_history (complaint_id, old_status, new_status, notes)
            VALUES (?, ?, ?, ?)
        """, (complaint_id, "new", "submitted", "Complaint registered"))
        
        await db.commit()
        
        # Fetch and return the created complaint
        return await get_complaint_by_id(complaint_id)


async def get_complaint_by_id(complaint_id: str) -> Optional[Complaint]:
    """Get a single complaint by its ID."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM complaints WHERE complaint_id = ?",
            (complaint_id,)
        )
        row = await cursor.fetchone()
        
        if row:
            return _row_to_complaint(dict(row))
        return None


async def get_complaints_by_user(telegram_user_id: int) -> List[Complaint]:
    """Get all complaints from a specific Telegram user."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM complaints WHERE telegram_user_id = ? ORDER BY created_at DESC",
            (telegram_user_id,)
        )
        rows = await cursor.fetchall()
        return [_row_to_complaint(dict(row)) for row in rows]


async def get_all_complaints(
    status: Optional[str] = None,
    department: Optional[str] = None,
    priority: Optional[str] = None,
    page: int = 1,
    per_page: int = 50
) -> tuple[List[Complaint], int]:
    """Get paginated list of complaints with optional filters."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        
        # Build query with filters
        query = "SELECT * FROM complaints WHERE 1=1"
        count_query = "SELECT COUNT(*) FROM complaints WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            count_query += " AND status = ?"
            params.append(status)
        if department:
            query += " AND department = ?"
            count_query += " AND department = ?"
            params.append(department)
        if priority:
            query += " AND priority = ?"
            count_query += " AND priority = ?"
            params.append(priority)
        
        # Get total count
        cursor = await db.execute(count_query, params)
        total = (await cursor.fetchone())[0]
        
        # Add pagination
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        
        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()
        
        complaints = [_row_to_complaint(dict(row)) for row in rows]
        return complaints, total


async def update_complaint_status(
    complaint_id: str,
    new_status: str,
    notes: Optional[str] = None,
    changed_by: Optional[str] = None
) -> Optional[Complaint]:
    """Update the status of a complaint."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Get current status
        cursor = await db.execute(
            "SELECT status FROM complaints WHERE complaint_id = ?",
            (complaint_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        
        old_status = row[0]
        now = datetime.now()
        
        # Update complaint
        await db.execute("""
            UPDATE complaints SET status = ?, updated_at = ? WHERE complaint_id = ?
        """, (new_status, now, complaint_id))
        
        # Add to history
        await db.execute("""
            INSERT INTO status_history (complaint_id, old_status, new_status, notes, changed_by)
            VALUES (?, ?, ?, ?, ?)
        """, (complaint_id, old_status, new_status, notes, changed_by))
        
        await db.commit()
        
        return await get_complaint_by_id(complaint_id)


async def get_status_history(complaint_id: str) -> List[StatusHistoryEntry]:
    """Get status change history for a complaint."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT * FROM status_history WHERE complaint_id = ? ORDER BY changed_at ASC
        """, (complaint_id,))
        rows = await cursor.fetchall()
        
        return [
            StatusHistoryEntry(
                id=row["id"],
                complaint_id=row["complaint_id"],
                old_status=ComplaintStatus(row["old_status"]) if row["old_status"] != "new" else ComplaintStatus.SUBMITTED,
                new_status=ComplaintStatus(row["new_status"]),
                changed_at=datetime.fromisoformat(row["changed_at"]) if isinstance(row["changed_at"], str) else row["changed_at"],
                notes=row["notes"],
                changed_by=row["changed_by"]
            )
            for row in rows
        ]


async def get_dashboard_stats() -> DashboardStats:
    """Get aggregated statistics for admin dashboard."""
    async with aiosqlite.connect(DB_PATH) as db:
        # Total complaints
        cursor = await db.execute("SELECT COUNT(*) FROM complaints")
        total = (await cursor.fetchone())[0]
        
        # By status
        cursor = await db.execute("""
            SELECT status, COUNT(*) FROM complaints GROUP BY status
        """)
        status_counts = dict(await cursor.fetchall())
        
        # By department
        cursor = await db.execute("""
            SELECT department, COUNT(*) FROM complaints GROUP BY department
        """)
        by_department = dict(await cursor.fetchall())
        
        # By priority
        cursor = await db.execute("""
            SELECT priority, COUNT(*) FROM complaints GROUP BY priority
        """)
        by_priority = dict(await cursor.fetchall())
        
        return DashboardStats(
            total_complaints=total,
            pending=status_counts.get("submitted", 0) + status_counts.get("assigned", 0),
            in_progress=status_counts.get("in_progress", 0),
            resolved=status_counts.get("resolved", 0) + status_counts.get("closed", 0),
            escalated=status_counts.get("escalated", 0),
            by_department=by_department,
            by_priority=by_priority,
            avg_resolution_hours=None  # Could calculate from resolved complaints
        )


def _row_to_complaint(row: dict) -> Complaint:
    """Convert database row to Complaint model."""
    return Complaint(
        id=row["id"],
        complaint_id=row["complaint_id"],
        telegram_user_id=row["telegram_user_id"],
        user_name=row["user_name"],
        raw_text=row["raw_text"],
        issue_type=row["issue_type"],
        location=row["location"],
        department=row["department"],
        priority=PriorityLevel(row["priority"]),
        status=ComplaintStatus(row["status"]),
        summary=row["summary"] or "",
        estimated_resolution_hours=row["estimated_resolution_hours"],
        created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
        updated_at=datetime.fromisoformat(row["updated_at"]) if isinstance(row["updated_at"], str) else row["updated_at"]
    )
