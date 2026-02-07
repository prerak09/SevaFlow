# SEVAFLOW Documentation

**AI-Assisted Citizen Grievance Platform for Delhi**

A GovTech solution for the Public Safety & Governance Challenge that simplifies grievance intake, improves transparency, and reduces cognitive load on citizens.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [System Architecture](#system-architecture)
4. [Configuration](#configuration)
5. [Usage Guide](#usage-guide)
6. [AI Usage & Responsible Design](#ai-usage--responsible-design)
7. [API Reference](#api-reference)
8. [Demo Scenarios](#demo-scenarios)

---

## Overview

### What is SEVAFLOW?

SEVAFLOW re-architectures the civic grievance experience as a **conversation, not a form**. Instead of navigating complex government portals and filling structured forms, citizens can simply describe their problem in natural language via Telegram.

### Key Features

| Feature | Description |
|---------|-------------|
| 🗣️ **Conversational Interface** | Submit complaints via Telegram in plain language |
| 🤖 **AI Classification** | Automatic categorization and department routing |
| 📍 **Location Extraction** | Automatically identifies complaint location |
| 🏢 **Rule-based Routing** | Transparent, deterministic department assignment |
| 📊 **Admin Dashboard** | Web interface for officials to manage complaints |
| 🔔 **Proactive Updates** | Citizens notified of status changes via Telegram |

### Important Disclaimer

> ⚠️ **This is a prototype/MVP** for demonstration purposes. It does not integrate with actual government systems and should not claim official access to any government portals.

---

## Quick Start

### Prerequisites

- Python 3.10+
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- Google Gemini API Key (from [Google AI Studio](https://makersuite.google.com/app/apikey))

### Installation

```bash
# Clone/Navigate to project directory
cd sevaflow

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your tokens
```

### Configuration

Edit `.env` file:

```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
GEMINI_API_KEY=your_gemini_key_here
ADMIN_SECRET=your_admin_password
```

### Run the System

```bash
# Run both API and Telegram bot
python run.py

# Or run separately:
python run.py --api-only    # Only API server (port 8000)
python run.py --bot-only    # Only Telegram bot
```

### Access Points

| Service | URL |
|---------|-----|
| API Documentation | http://localhost:8000/docs |
| Admin Dashboard | http://localhost:8000/admin |
| Health Check | http://localhost:8000/health |

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         SEVAFLOW                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────────────────────────────┐     │
│  │  Telegram   │    │         Backend Services           │     │
│  │    Bot      │◄──►│  ┌─────────────────────────────┐   │     │
│  └─────────────┘    │  │      FastAPI Server         │   │     │
│                     │  └─────────────────────────────┘   │     │
│  ┌─────────────┐    │              │                     │     │
│  │   Admin     │◄──►│  ┌───────────┴───────────┐         │     │
│  │  Dashboard  │    │  │                       │         │     │
│  └─────────────┘    │  ▼                       ▼         │     │
│                     │ ┌───────────┐    ┌─────────────┐   │     │
│                     │ │    AI     │    │   Router    │   │     │
│                     │ │ Processor │    │  (Rules)    │   │     │
│                     │ └───────────┘    └─────────────┘   │     │
│                     │        │                │          │     │
│                     │        └────────┬───────┘          │     │
│                     │                 ▼                  │     │
│                     │        ┌─────────────┐             │     │
│                     │        │   SQLite    │             │     │
│                     │        │   Database  │             │     │
│                     │        └─────────────┘             │     │
│                     └─────────────────────────────────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Component Overview

| Component | File | Purpose |
|-----------|------|---------|
| Config | `app/config.py` | Settings, department mappings |
| Models | `app/models.py` | Data structures (Pydantic) |
| Database | `app/database.py` | SQLite operations |
| AI Processor | `app/services/ai_processor.py` | LLM-based classification |
| Router | `app/services/router.py` | Rule-based department routing |
| Notifier | `app/services/notifier.py` | Message formatting |
| Telegram Bot | `app/telegram/bot.py` | Citizen interface |
| API | `app/api/*.py` | REST endpoints |
| Dashboard | `admin/` | Web admin interface |

---

## AI Usage & Responsible Design

### Philosophy

> **AI assists decision-making; it does not autonomously act.**

SEVAFLOW uses AI responsibly:

1. **Classification Only**: AI extracts information from complaints—it does NOT make decisions about resolution or departmental actions.

2. **Deterministic Routing**: After AI classification, rule-based logic assigns departments. This ensures predictability and auditability.

3. **Fallback Logic**: If AI fails, rule-based keyword matching ensures the system continues to work.

4. **Transparency**: All AI outputs include confidence scores. Low-confidence classifications can be flagged for human review.

### AI Classification Output

```json
{
  "issue_type": "Streetlight outage",
  "location": "Laxmi Nagar Metro Gate",
  "responsible_department": "MCD Electrical",
  "priority": "medium",
  "confidence": 0.85,
  "summary": "Citizen reports non-functional streetlight near metro station"
}
```

### Prompt Design

The AI prompt is:
- **Deterministic**: Low temperature (0.1) for consistent outputs
- **Constrained**: Must output valid JSON only
- **Transparent**: Department options are explicitly listed
- **Delhi-specific**: Trained on local department structure

---

## API Reference

### Public Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | System info |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | API documentation |

### Complaints API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/complaints` | Submit new complaint |
| `GET` | `/api/complaints` | List complaints (paginated) |
| `GET` | `/api/complaints/{id}` | Get complaint details |
| `GET` | `/api/complaints/{id}/history` | Get status history |

### Admin API (requires `X-Admin-Secret` header)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/admin/stats` | Dashboard statistics |
| `GET` | `/api/admin/departments` | List departments |
| `PATCH` | `/api/admin/complaints/{id}/status` | Update status |
| `POST` | `/api/admin/notify/{id}` | Send notification |

---

## Demo Scenarios

### Scenario 1: Streetlight Complaint

**Citizen sends to bot:**
> "The streetlight outside my house at 45 Nehru Nagar has been off for a week. Very dark and unsafe at night."

**Expected behavior:**
1. AI extracts: Issue=Streetlight, Location=45 Nehru Nagar, Priority=Medium
2. Router assigns: MCD Electrical, SLA=48 hours
3. Citizen receives confirmation with Reference ID

### Scenario 2: Urgent Water Issue

**Citizen sends:**
> "Emergency! Water pipe burst near Connaught Place, water flooding the street for hours."

**Expected behavior:**
1. AI detects: High priority (emergency keyword)
2. Assigned to: Delhi Jal Board, SLA=36 hours (reduced for urgency)
3. Immediate notification with acknowledgement

### Scenario 3: Status Check

**Citizen sends:**
> "/status SF-1023"

**Expected behavior:**
- Shows current status, department, and last update time

---

## Project Structure

```
sevaflow/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration & departments
│   ├── database.py          # SQLite operations
│   ├── models.py            # Pydantic models
│   ├── api/
│   │   ├── complaints.py    # Complaints endpoints
│   │   └── admin.py         # Admin endpoints
│   ├── services/
│   │   ├── ai_processor.py  # Gemini LLM integration
│   │   ├── router.py        # Department routing
│   │   └── notifier.py      # Notification formatting
│   └── telegram/
│       └── bot.py           # Telegram bot handlers
├── admin/
│   ├── index.html           # Dashboard UI
│   ├── style.css            # Styles
│   └── app.js               # Dashboard logic
├── docs/
│   └── README.md            # This file
├── requirements.txt
├── .env.example
└── run.py                   # Application runner
```

---

## License

This project is a prototype for educational and demonstration purposes.

---

## Contact

For questions about this prototype, please refer to the project maintainers.
