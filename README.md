# SEVAFLOW Technical Documentation

> Detailed technical reference for developers and contributors.

---

## Table of Contents

- [System Components](#system-components)
- [Configuration Reference](#configuration-reference)
- [Database Schema](#database-schema)
- [AI Processor Details](#ai-processor-details)
- [Routing Engine](#routing-engine)
- [API Reference](#api-reference)
- [Telegram Bot](#telegram-bot)
- [Admin Dashboard](#admin-dashboard)
- [Development Guide](#development-guide)

---

## System Components

### Overview

SEVAFLOW consists of four main components that work together:

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend API** | FastAPI | REST endpoints, admin dashboard serving |
| **Telegram Bot** | python-telegram-bot | Citizen interface |
| **AI Processor** | Google Gemini | Complaint classification |
| **Database** | SQLite + aiosqlite | Persistent storage |

### Component Interaction Flow

```
Citizen Message → Telegram Bot → AI Processor → Router → Database
                                                  ↓
                                            Admin Dashboard
                                                  ↓
                                         Status Update → Notifier → Citizen
```

---

## Configuration Reference

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `TELEGRAM_BOT_TOKEN` | ✅ | — | Bot token from @BotFather |
| `GEMINI_API_KEY` | ✅ | — | Google Gemini API key |
| `ADMIN_SECRET` | ✅ | — | Secret for admin endpoints |
| `HOST` | ❌ | `0.0.0.0` | Server bind address |
| `PORT` | ❌ | `8000` | Server port |
| `DATABASE_URL` | ❌ | `sqlite:///./sevaflow.db` | Database path |

### Department Configuration

Departments are configured in `app/config.py`. Each department has:

```python
{
    "id": "mcd_electrical",
    "name": "MCD Electrical",
    "keywords": ["streetlight", "lamp", "electricity", "power"],
    "sla_hours": 48,
    "contact": "mcd-electrical@delhi.gov.in"
}
```

---

## Database Schema

### complaints table

| Column | Type | Description |
|--------|------|-------------|
| `id` | TEXT | Primary key (SF-XXXX format) |
| `telegram_user_id` | INTEGER | Citizen's Telegram ID |
| `raw_text` | TEXT | Original complaint text |
| `issue_type` | TEXT | AI-classified issue type |
| `location` | TEXT | Extracted location |
| `department_id` | TEXT | Assigned department |
| `priority` | TEXT | low/medium/high/urgent |
| `status` | TEXT | pending/acknowledged/in_progress/resolved/closed |
| `confidence` | REAL | AI confidence score (0-1) |
| `summary` | TEXT | AI-generated summary |
| `created_at` | TIMESTAMP | Submission time |
| `updated_at` | TIMESTAMP | Last update time |

### status_history table

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER | Primary key |
| `complaint_id` | TEXT | Foreign key to complaints |
| `old_status` | TEXT | Previous status |
| `new_status` | TEXT | New status |
| `changed_at` | TIMESTAMP | Change timestamp |
| `changed_by` | TEXT | Who made the change |

---

## AI Processor Details

### Location

`app/services/ai_processor.py`

### Functionality

The AI processor uses Google Gemini to extract structured information from unstructured complaint text.

### Prompt Design Principles

1. **Low Temperature (0.1)** — Ensures consistent, deterministic outputs
2. **JSON-Only Output** — Structured response format
3. **Constrained Options** — Department list is explicitly provided
4. **Delhi-Specific** — Trained on local government structure

### Output Schema

```json
{
  "issue_type": "string",
  "location": "string | null",
  "responsible_department": "string",
  "priority": "low | medium | high | urgent",
  "confidence": 0.0-1.0,
  "summary": "string"
}
```

### Fallback Behavior

If AI processing fails:
1. Keyword matching is used to identify department
2. Priority defaults to "medium"
3. Location extraction is skipped
4. Complaint is marked with `confidence: 0.0`

---

## Routing Engine

### Location

`app/services/router.py`

### Routing Rules

The router uses a deterministic, rule-based approach:

1. **Priority Override** — Emergency keywords trigger high priority regardless of AI output
2. **Department Matching** — Maps AI department suggestion to configured departments
3. **SLA Assignment** — Based on department + priority
4. **Fallback** — Unknown departments route to "General Services"

### Priority Keywords

| Priority | Trigger Words |
|----------|--------------|
| `urgent` | emergency, danger, life-threatening, fire |
| `high` | flooding, collapse, accident, burst |
| `medium` | broken, not working, damaged |
| `low` | suggestion, improvement, feedback |

---

## API Reference

### Complaints Endpoints

#### POST `/api/complaints`

Submit a new complaint.

**Request:**
```json
{
  "telegram_user_id": 123456789,
  "text": "Streetlight broken at Nehru Place"
}
```

**Response:**
```json
{
  "id": "SF-1234",
  "status": "pending",
  "department": "MCD Electrical",
  "created_at": "2024-01-15T10:30:00Z"
}
```

#### GET `/api/complaints`

List complaints with pagination.

**Query Parameters:**
- `skip` (int, default: 0)
- `limit` (int, default: 20)
- `status` (string, optional)
- `department` (string, optional)

#### GET `/api/complaints/{id}`

Get complaint details by ID.

#### GET `/api/complaints/{id}/history`

Get status change history for a complaint.

### Admin Endpoints

All admin endpoints require `X-Admin-Secret` header.

#### GET `/api/admin/stats`

Dashboard statistics.

**Response:**
```json
{
  "total_complaints": 150,
  "pending": 45,
  "resolved": 80,
  "avg_resolution_hours": 36.5,
  "by_department": {...},
  "by_priority": {...}
}
```

#### PATCH `/api/admin/complaints/{id}/status`

Update complaint status.

**Request:**
```json
{
  "status": "in_progress",
  "note": "Team dispatched"
}
```

---

## Telegram Bot

### Location

`app/telegram/bot.py`

### Commands

| Command | Handler | Description |
|---------|---------|-------------|
| `/start` | `start_handler` | Welcome message |
| `/help` | `help_handler` | Show commands |
| `/status <id>` | `status_handler` | Check complaint status |
| `/cancel` | `cancel_handler` | Cancel conversation |

### Conversation Flow

```
User: Hi
Bot: Welcome! Describe your complaint in detail.

User: The streetlight at my colony gate is not working
Bot: Processing your complaint...
Bot: ✅ Complaint registered!
     Reference: SF-1234
     Department: MCD Electrical
     Priority: Medium
     Expected response: within 48 hours
```

### Message Handling

Non-command messages are treated as complaints and processed through:
1. AI classification
2. Department routing
3. Database storage
4. Confirmation message

---

## Admin Dashboard

### Location

`admin/` directory

### Access

Navigate to `http://localhost:8000/admin`

### Features

- **Overview Stats** — Total, pending, resolved complaints
- **Complaint List** — Filterable, sortable table
- **Detail View** — Full complaint info with history
- **Status Update** — Change status with notes
- **Notification** — Trigger citizen notification

### Authentication

Enter the `ADMIN_SECRET` when prompted.

---

## Development Guide

### Running in Development

```bash
# With auto-reload (API only)
uvicorn app.main:app --reload --port 8000

# Bot separately
python run.py --bot-only
```

### Adding a New Department

1. Edit `app/config.py`
2. Add department to `DEPARTMENTS` list:

```python
{
    "id": "new_dept",
    "name": "New Department",
    "keywords": ["keyword1", "keyword2"],
    "sla_hours": 72,
    "contact": "new-dept@delhi.gov.in"
}
```

3. Restart the application

### Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=app
```

### Database Reset

```bash
# Delete database file to reset
rm sevaflow.db

# Database will be recreated on next startup
python run.py
```

---

## Troubleshooting

### Bot not responding

1. Check `TELEGRAM_BOT_TOKEN` in `.env`
2. Verify bot is not blocked by Telegram
3. Check console for error messages

### AI classification failing

1. Verify `GEMINI_API_KEY` is valid
2. Check Google Cloud quotas
3. System will fallback to keyword matching

### Admin dashboard not loading

1. Ensure `/admin` directory exists
2. Check `index.html` is present
3. Verify CORS settings if accessing from different origin

---

*For more information, see the main [README.md](../README.md)*
