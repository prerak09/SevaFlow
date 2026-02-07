# SEVAFLOW Demo Flow Guide

This guide outlines the demonstration scenarios for showcasing SEVAFLOW to evaluators, government officials, and stakeholders.

---

## Pre-Demo Setup

### 1. Environment Preparation

```bash
cd sevaflow
source venv/bin/activate
python run.py
```

### 2. Browser Tabs to Open

1. **Admin Dashboard**: http://localhost:8000/admin
2. **API Docs**: http://localhost:8000/docs (optional, for technical audience)

### 3. Telegram Setup

- Have your phone ready with Telegram open
- Navigate to your SEVAFLOW bot

---

## Demo Script (10-15 minutes)

### Part 1: The Problem (2 min)

> *"Current civic grievance systems require citizens to navigate complex forms, identify the correct department, and often visit multiple portals. SEVAFLOW changes this by treating grievance as a conversation."*

### Part 2: Citizen Experience (5 min)

#### Demo 2.1: Submit a Complaint

1. Open Telegram bot
2. Send: `/start`
3. Show the welcome message

4. Type a natural complaint:
   ```
   The streetlight near Laxmi Nagar Metro Station Gate 2 
   has been off for 3 days. It's very dark and unsafe.
   ```

5. **Point out:**
   - No forms filled
   - No department selection required
   - Immediate acknowledgement
   - Clear reference ID provided

#### Demo 2.2: Check Status

1. Copy the reference ID (e.g., SF-0001)
2. Send: `/status SF-0001`
3. Show the status display

#### Demo 2.3: View All Complaints

1. Send: `/mycomplaints`
2. Show the list of submitted complaints

### Part 3: Admin Experience (4 min)

1. **Switch to Admin Dashboard** (browser)

2. **Dashboard Overview:**
   - Show statistics cards
   - Point out the recent complaints

3. **View All Complaints:**
   - Click "All Complaints" in sidebar
   - Show filtering capabilities (status, department, priority)

4. **Update Status:**
   - Click "Update" on a complaint
   - Change status to "In Progress"
   - Check "Notify citizen"
   - Submit

5. **Show Notification in Telegram:**
   - Switch back to Telegram
   - Show the proactive notification received

### Part 4: Technical Highlights (3 min)

1. **AI Classification:**
   - Explain that AI extracts issue type, location, priority
   - Show that routing is rule-based (transparent, auditable)

2. **System Architecture:**
   - Open API docs briefly
   - Show modular design

3. **Responsible AI:**
   - AI assists; humans decide
   - All outputs validated
   - Fallback logic ensures reliability

---

## Sample Complaints for Demo

### Streetlight Issue
```
The streetlight near Laxmi Nagar Metro Gate 2 has been off for 3 days.
It's very dark and unsafe for pedestrians at night.
```

### Water Problem
```
There's a major water leakage from the main pipe on MG Road near
Siri Fort. Water has been flowing onto the street since morning.
```

### Garbage Issue
```
Garbage has not been collected from Block B, Vasant Kunj for 4 days.
The bins are overflowing and causing a bad smell.
```

### Pothole
```
There's a dangerous pothole on the main road near Dwarka Sector 21 
metro station. Already caused 2 accidents this week.
```

### Emergency (High Priority)
```
URGENT: Exposed electrical wire hanging low on the street near 
Janakpuri East metro. Someone might get electrocuted!
```

---

## Key Messages for Stakeholders

### For Government Officials
- "Reduces citizen friction dramatically"
- "Transparent, auditable routing logic"
- "Can integrate with existing systems via API"

### For Technical Evaluators
- "Modular, extensible architecture"
- "Responsible AI with fallback mechanisms"
- "Production-ready code quality"

### For Policy Stakeholders
- "AI assists, doesn't replace human judgment"
- "Rule-based decisions are policy-compatible"
- "Privacy-conscious design"

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Bot not responding | Check `TELEGRAM_BOT_TOKEN` in `.env` |
| AI not working | Check `GEMINI_API_KEY`; fallback will still work |
| Dashboard empty | Database may be empty; submit a complaint first |
| Admin API 401 | Check `ADMIN_SECRET` matches between `.env` and `app.js` |

---

## Post-Demo Q&A Preparation

### "How does it scale?"
> "The architecture separates concerns—bot, API, and database can scale independently. SQLite works for MVP; production would use PostgreSQL."

### "What about vernacular languages?"
> "The LLM can process Hindi and Hinglish. Production would add explicit multi-language support."

### "Is it secure?"
> "Yes—admin operations require authentication, and citizen data is only linked to Telegram IDs, not personal information."

### "Integration with existing systems?"
> "SEVAFLOW is designed as middleware. The REST API can push to existing government systems when APIs are available."
