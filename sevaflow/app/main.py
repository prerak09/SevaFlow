"""
SEVAFLOW - Main FastAPI Application

This is the entry point for the backend server that provides:
- REST API for complaints management
- Admin dashboard serving
- Static file serving for the web UI

The Telegram bot runs concurrently with the web server.
"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app import database
from app.api.complaints import router as complaints_router
from app.api.admin import router as admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    print("🚀 Starting SEVAFLOW...")
    await database.init_db()
    print("✅ Database initialized")
    
    yield
    
    # Shutdown
    print("👋 Shutting down SEVAFLOW...")


# Create FastAPI application
app = FastAPI(
    title="SEVAFLOW",
    description="""
    AI-Assisted Citizen Grievance Platform for Delhi
    
    A GovTech solution that provides:
    - Conversational complaint submission via Telegram
    - AI-powered complaint classification
    - Transparent tracking and status updates
    - Administrative dashboard for officials
    
    **Note:** This is a prototype/MVP for demonstration purposes.
    It does not integrate with actual government systems.
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for admin dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(complaints_router)
app.include_router(admin_router)

# Serve admin dashboard static files
ADMIN_DIR = Path(__file__).resolve().parent.parent / "admin"
if ADMIN_DIR.exists():
    app.mount("/admin/static", StaticFiles(directory=ADMIN_DIR), name="admin_static")


@app.get("/")
async def root():
    """Root endpoint with system info."""
    return {
        "name": "SEVAFLOW",
        "version": "1.0.0",
        "description": "AI-Assisted Citizen Grievance Platform for Delhi",
        "status": "operational",
        "endpoints": {
            "api_docs": "/docs",
            "admin_dashboard": "/admin",
            "complaints": "/api/complaints"
        }
    }


@app.get("/admin")
@app.get("/admin/")
async def admin_dashboard():
    """Serve the admin dashboard."""
    admin_file = ADMIN_DIR / "index.html"
    if admin_file.exists():
        return FileResponse(admin_file)
    return {"error": "Admin dashboard not found", "path": str(admin_file)}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "sevaflow-backend"}
