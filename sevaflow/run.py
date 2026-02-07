#!/usr/bin/env python3
"""
SEVAFLOW Unified Runner

Starts both the FastAPI backend and Telegram bot concurrently.
This is the main entry point for running the complete system.

Usage:
    python run.py              # Run both API and Bot
    python run.py --api-only   # Run only the API server
    python run.py --bot-only   # Run only the Telegram bot
"""

import asyncio
import sys
import subprocess
import uvicorn

from app.config import settings
from app import database


def print_banner():
    """Print the SEVAFLOW banner."""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   ███████╗███████╗██╗   ██╗ █████╗ ███████╗██╗      ██╗   ██╗║
║   ██╔════╝██╔════╝██║   ██║██╔══██╗██╔════╝██║     ██╔╝██║   ║
║   ███████╗█████╗  ██║   ██║███████║█████╗  ██║    ██║  ██║   ║
║   ╚════██║██╔══╝  ╚██╗ ██╔╝██╔══██║██╔══╝  ██║   ██║   ██║   ║
║   ███████║███████╗ ╚████╔╝ ██║  ██║██║     ██║████████╗██║   ║
║   ╚══════╝╚══════╝  ╚═══╝  ╚═╝  ╚═╝╚═╝     ╚═╝╚═══════╝╚═╝   ║
║                                                           ║
║   AI-Assisted Citizen Grievance Platform for Delhi        ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)


def run_api_server():
    """Run the FastAPI server (synchronous entry point)."""
    print(f"🚀 Starting SEVAFLOW...")
    print(f"   API Server: http://localhost:{settings.port}")
    print(f"   Admin Dashboard: http://localhost:{settings.port}/admin")
    print(f"   API Docs: http://localhost:{settings.port}/docs")
    print("")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level="info"
    )


async def run_telegram_bot():
    """Run the Telegram bot."""
    from app.telegram.bot import bot
    
    if not settings.telegram_bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not set in environment")
        print("   Create a bot via @BotFather and add the token to .env")
        return
    
    print("🤖 Starting Telegram bot...")
    application = bot.build_application()
    
    # Start polling
    await application.initialize()
    await application.start()
    await application.updater.start_polling(drop_pending_updates=True)
    
    print("✅ Telegram bot is running!")
    bot_info = await application.bot.get_me()
    print(f"   Bot: @{bot_info.username}")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        pass
    finally:
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


async def run_both():
    """Run both API server and Telegram bot."""
    import threading
    
    # Initialize database
    await database.init_db()
    
    print(f"🚀 Starting SEVAFLOW...")
    print(f"   API Server: http://localhost:{settings.port}")
    print(f"   Admin Dashboard: http://localhost:{settings.port}/admin")
    print(f"   API Docs: http://localhost:{settings.port}/docs")
    print("")
    
    # Start API server in a separate thread
    def start_api():
        uvicorn.run(
            "app.main:app",
            host=settings.host,
            port=settings.port,
            reload=False,
            log_level="info"
        )
    
    api_thread = threading.Thread(target=start_api, daemon=True)
    api_thread.start()
    
    # Run bot in main async loop
    await run_telegram_bot()


def main():
    """Main entry point."""
    print_banner()
    
    # Parse arguments
    api_only = "--api-only" in sys.argv
    bot_only = "--bot-only" in sys.argv
    
    if api_only:
        # Run only API server (synchronous)
        print("🌐 Running API server only...")
        # Initialize database synchronously
        asyncio.run(database.init_db())
        run_api_server()
    elif bot_only:
        # Run only Telegram bot
        print("📱 Running Telegram bot only...")
        asyncio.run(database.init_db())
        asyncio.run(run_telegram_bot())
    else:
        # Run both concurrently
        asyncio.run(run_both())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Shutting down SEVAFLOW...")
