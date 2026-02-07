"""
Configuration management for SEVAFLOW.
Loads settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Telegram
    telegram_bot_token: str = ""
    
    # Google Gemini
    gemini_api_key: str = ""
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str = "sqlite:///./sevaflow.db"
    
    # Admin
    admin_secret: str = "sevaflow_admin_2024"
    
    # Paths
    base_dir: Path = Path(__file__).resolve().parent.parent
    
    class Config:
        env_file = ".env"
        extra = "ignore"


# Singleton settings instance
settings = Settings()


# Department configuration with SLAs
DEPARTMENTS = {
    "MCD Electrical": {
        "keywords": ["streetlight", "light", "electricity", "power", "electrical", "lamp", "bulb"],
        "sla_hours": 48,
        "contact": "mcd-electrical@example.gov.in"
    },
    "Delhi Jal Board": {
        "keywords": ["water", "sewage", "drainage", "pipe", "leakage", "supply", "tanker"],
        "sla_hours": 72,
        "contact": "djb@example.gov.in"
    },
    "PWD": {
        "keywords": ["road", "pothole", "pavement", "footpath", "bridge", "flyover", "construction"],
        "sla_hours": 96,
        "contact": "pwd@example.gov.in"
    },
    "MCD Sanitation": {
        "keywords": ["garbage", "trash", "waste", "cleaning", "sanitation", "dustbin", "sweeper"],
        "sla_hours": 24,
        "contact": "mcd-sanitation@example.gov.in"
    },
    "Traffic Police": {
        "keywords": ["traffic", "signal", "parking", "challan", "jam", "violation", "zebra"],
        "sla_hours": 24,
        "contact": "traffic-police@example.gov.in"
    },
    "Delhi Police": {
        "keywords": ["crime", "theft", "robbery", "safety", "police", "emergency", "harassment"],
        "sla_hours": 12,
        "contact": "delhi-police@example.gov.in"
    },
    "BSES/TPDDL": {
        "keywords": ["meter", "bill", "voltage", "transformer", "outage", "fluctuation"],
        "sla_hours": 48,
        "contact": "power-discom@example.gov.in"
    },
    "DDA": {
        "keywords": ["park", "garden", "encroachment", "land", "colony", "development"],
        "sla_hours": 120,
        "contact": "dda@example.gov.in"
    },
    "General Helpdesk": {
        "keywords": [],  # Fallback department
        "sla_hours": 72,
        "contact": "helpdesk@example.gov.in"
    }
}


# Priority mapping based on keywords
PRIORITY_KEYWORDS = {
    "high": ["urgent", "emergency", "dangerous", "hazard", "safety", "crime", "accident", "fire"],
    "medium": ["broken", "not working", "issue", "problem", "complaint"],
    "low": ["request", "suggestion", "feedback", "improvement"]
}


# Status lifecycle
COMPLAINT_STATUSES = [
    "submitted",
    "assigned",
    "in_progress",
    "resolved",
    "escalated",
    "closed"
]
