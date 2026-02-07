"""
Notification Service for SEVAFLOW.

Handles citizen notifications via Telegram when complaint status changes.
Generates human-readable, non-technical messages.
"""

from typing import Optional
from app.models import Complaint, ComplaintStatus


class NotificationService:
    """
    Generates and manages citizen notifications.
    Messages are designed to be:
    - Human-readable
    - Non-technical  
    - Transparent about process
    """
    
    def __init__(self, bot=None):
        """Initialize with optional Telegram bot reference."""
        self.bot = bot
    
    def set_bot(self, bot):
        """Set the Telegram bot instance for sending messages."""
        self.bot = bot
    
    def format_registration_message(self, complaint: Complaint) -> str:
        """
        Format the confirmation message when a complaint is first registered.
        
        Args:
            complaint: The newly created complaint
            
        Returns:
            Formatted message string with emojis and clear info
        """
        priority_emoji = {
            "low": "🟢",
            "medium": "🟡", 
            "high": "🔴"
        }
        
        message = f"""
✅ <b>Complaint Registered Successfully!</b>

📋 <b>Issue:</b> {complaint.issue_type}
📍 <b>Location:</b> {complaint.location}
🏢 <b>Department:</b> {complaint.department}
{priority_emoji.get(complaint.priority.value, "🟡")} <b>Priority:</b> {complaint.priority.value.capitalize()}

🆔 <b>Reference ID:</b> <code>{complaint.complaint_id}</code>
⏱️ <b>Expected Resolution:</b> {complaint.estimated_resolution_hours} hours

Save your Reference ID to check status anytime!
Type /status {complaint.complaint_id} to track progress.

Thank you for helping improve Delhi! 🙏
"""
        return message.strip()
    
    def format_status_message(self, complaint: Complaint) -> str:
        """
        Format a status check response message.
        
        Args:
            complaint: The complaint to report status on
            
        Returns:
            Formatted status message
        """
        status_emoji = {
            "submitted": "📝",
            "assigned": "👤",
            "in_progress": "🔄",
            "resolved": "✅",
            "escalated": "⚠️",
            "closed": "📁"
        }
        
        status_text = {
            "submitted": "Your complaint has been received and is awaiting assignment.",
            "assigned": "Your complaint has been assigned to the concerned department.",
            "in_progress": "The department is actively working on your complaint.",
            "resolved": "Your complaint has been resolved!",
            "escalated": "Your complaint has been escalated for priority attention.",
            "closed": "This complaint has been closed."
        }
        
        emoji = status_emoji.get(complaint.status.value, "📋")
        description = status_text.get(complaint.status.value, "Status unknown")
        
        message = f"""
{emoji} <b>Complaint Status</b>

🆔 <b>Reference:</b> <code>{complaint.complaint_id}</code>
📋 <b>Issue:</b> {complaint.issue_type}
🏢 <b>Department:</b> {complaint.department}
📍 <b>Location:</b> {complaint.location}

<b>Current Status:</b> {complaint.status.value.replace('_', ' ').title()}
{description}

<i>Last updated: {complaint.updated_at.strftime('%d %b %Y, %I:%M %p')}</i>
"""
        return message.strip()
    
    def format_status_update_notification(
        self,
        complaint: Complaint,
        old_status: str,
        new_status: str,
        notes: Optional[str] = None
    ) -> str:
        """
        Format a proactive notification when status changes.
        
        Args:
            complaint: The updated complaint
            old_status: Previous status
            new_status: New status
            notes: Optional notes from the department
            
        Returns:
            Formatted notification message
        """
        status_messages = {
            "assigned": "Your complaint has been assigned to the {department} team. They will begin work soon.",
            "in_progress": "Good news! Work has begun on your complaint. The {department} team is on it.",
            "resolved": "🎉 Your complaint has been resolved! Thank you for your patience.",
            "escalated": "Your complaint has been escalated for priority handling due to its urgency.",
            "closed": "This complaint has been closed. If you're not satisfied, please submit a new complaint."
        }
        
        base_message = status_messages.get(
            new_status, 
            f"Your complaint status has changed from {old_status} to {new_status}."
        ).format(department=complaint.department)
        
        message = f"""
🔔 <b>Status Update</b>

🆔 <b>Reference:</b> <code>{complaint.complaint_id}</code>
📋 <b>Issue:</b> {complaint.issue_type}

{base_message}
"""
        
        if notes:
            message += f"\n💬 <b>Note from department:</b>\n<i>{notes}</i>\n"
        
        message += f"\n<i>Updated: {complaint.updated_at.strftime('%d %b %Y, %I:%M %p')}</i>"
        
        return message.strip()
    
    def format_help_message(self) -> str:
        """Format the help/instructions message."""
        return """
🙏 <b>Welcome to SEVAFLOW</b>
<i>Your AI-powered grievance assistant for Delhi</i>

<b>How to use:</b>

📝 <b>Submit a complaint:</b>
Just type your complaint in plain language!
Example: "The streetlight near Laxmi Nagar metro gate has been off for 3 days"

🔍 <b>Check status:</b>
/status SF-1001
(Replace with your Reference ID)

📜 <b>View your complaints:</b>
/mycomplaints

❓ <b>Get help:</b>
/help

<b>Tips for faster resolution:</b>
• Include specific location details
• Mention how long the problem has existed
• Describe the issue clearly

We're here to help make Delhi better! 🌟
"""

    def format_my_complaints_message(self, complaints: list) -> str:
        """Format a list of user's complaints."""
        if not complaints:
            return "📋 You haven't submitted any complaints yet.\n\nTo submit a complaint, just describe your issue in plain language!"
        
        message = f"📋 <b>Your Complaints</b> ({len(complaints)} total)\n\n"
        
        for c in complaints[:10]:  # Show last 10
            status_emoji = {
                "submitted": "📝", "assigned": "👤", "in_progress": "🔄",
                "resolved": "✅", "escalated": "⚠️", "closed": "📁"
            }
            emoji = status_emoji.get(c.status.value, "📋")
            
            message += f"{emoji} <code>{c.complaint_id}</code> - {c.issue_type[:30]}...\n"
            message += f"   Status: {c.status.value.replace('_', ' ').title()}\n\n"
        
        if len(complaints) > 10:
            message += f"<i>Showing 10 of {len(complaints)} complaints</i>"
        
        return message


# Singleton instance
notifier = NotificationService()
