"""
Telegram Bot for SEVAFLOW.

Provides a conversational interface for citizens to:
- Submit complaints in natural language
- Check complaint status
- Receive proactive updates

The interface prioritizes:
- Simplicity
- Familiar UX
- Minimal user effort
"""

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from app.config import settings
from app.models import ComplaintCreate
from app.services.ai_processor import process_complaint
from app.services.router import route_complaint
from app.services.notifier import notifier
from app import database

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class SevaFlowBot:
    """
    Telegram bot for citizen grievance submission and tracking.
    """
    
    def __init__(self):
        """Initialize the bot with handlers."""
        self.application = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command - welcome message."""
        user = update.effective_user
        welcome = f"""
🙏 <b>Namaste, {user.first_name}!</b>

Welcome to <b>SEVAFLOW</b> - Your AI-powered grievance assistant for Delhi.

<b>How can I help you today?</b>

📝 <b>To submit a complaint:</b>
Just describe your issue in your own words!

Example:
<i>"The streetlight near Laxmi Nagar metro gate has been off for 3 days"</i>

🔍 <b>To check status:</b>
/status SF-1001

📜 <b>To see all your complaints:</b>
/mycomplaints

❓ <b>For help:</b>
/help

Let's make Delhi better together! 🌟
"""
        await update.message.reply_text(welcome.strip(), parse_mode='HTML')
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = notifier.format_help_message()
        await update.message.reply_text(help_text, parse_mode='HTML')
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status <complaint_id> command."""
        # Extract complaint ID from command args
        if not context.args:
            await update.message.reply_text(
                "❓ Please provide your complaint Reference ID.\n\n"
                "Usage: /status SF-1001",
                parse_mode='HTML'
            )
            return
        
        complaint_id = context.args[0].upper()
        
        # Look up complaint
        complaint = await database.get_complaint_by_id(complaint_id)
        
        if not complaint:
            await update.message.reply_text(
                f"🔍 Complaint <code>{complaint_id}</code> not found.\n\n"
                "Please check the Reference ID and try again.",
                parse_mode='HTML'
            )
            return
        
        # Format and send status
        message = notifier.format_status_message(complaint)
        await update.message.reply_text(message, parse_mode='HTML')
    
    async def my_complaints_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /mycomplaints command."""
        user_id = update.effective_user.id
        
        complaints = await database.get_complaints_by_user(user_id)
        message = notifier.format_my_complaints_message(complaints)
        
        await update.message.reply_text(message, parse_mode='HTML')
    
    async def handle_complaint(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle free-form text messages as complaint submissions.
        This is the core flow:
        1. Receive text
        2. Process with AI
        3. Route to department
        4. Store in database
        5. Send confirmation
        """
        user = update.effective_user
        text = update.message.text.strip()
        
        # Ignore very short messages
        if len(text) < 15:
            await update.message.reply_text(
                "📝 Please describe your complaint in more detail.\n\n"
                "Include information like:\n"
                "• What the issue is\n"
                "• Where it's located\n"
                "• How long it's been a problem",
                parse_mode='HTML'
            )
            return
        
        # Send "processing" indicator
        processing_msg = await update.message.reply_text(
            "🔄 <i>Processing your complaint...</i>",
            parse_mode='HTML'
        )
        
        try:
            # Step 1: AI Processing
            ai_result = await process_complaint(text)
            logger.info(f"AI extracted: {ai_result.model_dump()}")
            
            # Step 2: Route to department
            department, sla_hours = route_complaint(ai_result)
            
            # Step 3: Generate complaint ID and store
            complaint_id = await database.get_next_complaint_id()
            
            complaint = await database.create_complaint(
                complaint_id=complaint_id,
                telegram_user_id=user.id,
                user_name=user.full_name,
                raw_text=text,
                issue_type=ai_result.issue_type,
                location=ai_result.location,
                department=department,
                priority=ai_result.priority.value,
                summary=ai_result.summary,
                estimated_hours=sla_hours
            )
            
            # Step 4: Format and send confirmation
            confirmation = notifier.format_registration_message(complaint)
            
            # Delete processing message and send confirmation
            await processing_msg.delete()
            await update.message.reply_text(confirmation, parse_mode='HTML')
            
            logger.info(f"Complaint {complaint_id} registered for user {user.id}")
            
        except Exception as e:
            logger.error(f"Error processing complaint: {e}")
            await processing_msg.edit_text(
                "❌ Sorry, there was an error processing your complaint.\n\n"
                "Please try again in a moment, or contact support if the issue persists.",
                parse_mode='HTML'
            )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors gracefully."""
        logger.error(f"Update {update} caused error {context.error}")
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ An unexpected error occurred. Please try again.",
                parse_mode='HTML'
            )
    
    def build_application(self) -> Application:
        """Build and configure the bot application."""
        # Create application
        self.application = Application.builder().token(settings.telegram_bot_token).build()
        
        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("mycomplaints", self.my_complaints_command))
        
        # Add message handler for complaints (handles all non-command text)
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_complaint)
        )
        
        # Add error handler
        self.application.add_error_handler(self.error_handler)
        
        return self.application
    
    async def send_notification(self, user_id: int, message: str):
        """Send a notification message to a user."""
        if self.application and self.application.bot:
            try:
                await self.application.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode='HTML'
                )
            except Exception as e:
                logger.error(f"Failed to send notification to {user_id}: {e}")


# Singleton bot instance
bot = SevaFlowBot()


def get_bot() -> SevaFlowBot:
    """Get the bot instance."""
    return bot
