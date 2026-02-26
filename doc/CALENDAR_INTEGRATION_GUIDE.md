# Calendar Integration Verification & Setup Guide

## Current State: `schedule_upload_csv_to_calendar.json`

The existing n8n workflow in `/n8n_backups/schedule_upload_csv_to_calendar.json` is configured to:

1. **Receive CSV via Webhook** — `POST /webhook-test/import-schedule`
2. **Parse CSV Columns**: Event_Title, Event_Date, Start_Time, Notify_Rule, Location, Channels, Target_Audience, Dept_Filter, Content_Remarks, Assets_URL
3. **Calculate Notification Dates** — Converts rules like "2 weeks before" → trigger date
4. **Create Google Calendar Events** — Posts to Google Calendar API

**Current Status**: ✅ Active and ready to use

---

## Three Workflows: Role Clarity

### Workflow 1: CSV → Django Events (NEW)
**File**: `csv_to_events_pipeline.json`
**Purpose**: Process CSV → Generate content (Groq) → Create Django Event records
**Webhook**: `POST /webhook-test/csv-import`
**Output**: Events in PostgreSQL with `generated_content`
**Staff Role**: Convenors & Staff
**Use Case**: "I want to bulk-create calendar events with AI-generated marketing content"

---

### Workflow 2: Event Refinement Chatbot (NEW)
**File**: `event_refinement_chatbot.json`
**Purpose**: Staff refines auto-generated content via prompt or direct editing
**Webhook**: `POST /webhook-test/event-refinement` 
**Input**: Event ID + prompt or edited text
**Output**: Suggestions (if prompt) or confirmation (if direct edit)
**Staff Role**: Staff only
**Use Case**: "I want to adjust the social post or email before publishing"

---

### Workflow 3: Calendar Integration (EXISTING)
**File**: `schedule_upload_csv_to_calendar.json`
**Purpose**: Legacy Google Calendar sync with notification scheduling
**Webhook**: `POST /webhook-test/import-schedule`
**Supported Columns**: Event_Title, Event_Date, Start_Time, Notify_Rule, Location, Channels, Target_Audience, Dept_Filter, Content_Remarks, Assets_URL
**Output**: Google Calendar events with embedded metadata
**Staff Role**: Academic personnel
**Use Case**: "I want to sync a schedule directly to Google Calendar with notification rules"

---

## Workflow Selection Matrix

| Need | Use Workflow | Why |
|------|--------------|-----|
| Upload CSV → Create events with AI marketing content | csv_to_events_pipeline | Generates social_post, email_body, article_body automatically |
| Need to edit generated content before publishing | event_refinement_chatbot | Provides UI for prompt-based or direct editing |
| Sync schedule to Google Calendar | schedule_upload_csv_to_calendar | Google Calendar API integration with notify rules |
| Bulk-approve events | Event bulk-publish endpoint | Django endpoint, not n8n |

---

## CSV Upload Specifications

### For Django Event Creation (Workflow 1)

**Source File**: `example_end_of_semester_plans.csv`

**Required Columns**:
- `Event_Title` — Name of event
- `Event_Date` — Date (YYYY-MM-DD or MM/DD/YYYY)
- `Start_Time` — Time (HH:MM format)

**Optional Columns**:
- `Location` — Event location
- `Notify_Rule` — Notification timing (e.g., "2 weeks before")
- `Channels` — Communication channels
- `Target_Audience` — Who this is for (students, parents, etc.)
- `Dept_Filter` — Department filter
- `Content_Remarks` — Additional context for LLM generation
- `Assets_URL` — Drive link to assets

**Example**:
```csv
Event_Title,Event_Date,Location,Start_Time,Notify_Rule,Channels,Target_Audience,Dept_Filter,Content_Remarks,Assets_URL
Tuition Fee Deadline,2025-12-12,"Academic Department at Swinburne Danang",07:00,1 week before,Email,"Parents, students",all,Tone: professional; topic: payment deadline,https://drive.google.com/...
Unit Enrolment,2025-12-12,"Academic Department at Swinburne Danang",08:00,2 week before,Email,students,all,Tone: professional; emphasize deadline,
```

**Upload Method**:
```bash
curl -X POST http://localhost:8000/api/events/import-csv/ \
  -H "Authorization: Bearer <staff_token>" \
  -F "data=@example_end_of_semester_plans.csv"
```

**Response**:
```json
{
  "message": "CSV parsed (dev mode): 4 events",
  "events": [
    {
      "Event_Title": "Tuition Fee Deadline",
      "Event_Date": "2025-12-12",
      ...
    }
  ]
}
```

---

## Setup Instructions

### Step 1: Verify n8n is Running

```bash
# Check Docker
docker ps | grep n8n

# Access UI
http://localhost:5678
```

### Step 2: Import Workflows

In n8n UI:

1. Click "New" → "Import workflow"
2. Upload `n8n_backups/csv_to_events_pipeline.json`
3. Click "Import"
4. Verify webhook path shows: `POST /webhook-test/csv-import`
5. Click the webhook node → "Test webhook"

Repeat for other workflows:
- `event_refinement_chatbot.json` (webhook: `/webhook-test/event-refinement`)
- Verify `schedule_upload_csv_to_calendar.json` is still active (webhook: `/webhook-test/import-schedule`)

### Step 3: Configure Groq Credentials

1. In n8n: Settings → Credentials
2. Click "New credential type: Groq account"
3. Add your Groq API key
4. Save

### Step 4: Test CSV Import

```bash
# Using test file
curl -X POST http://localhost:8000/api/events/import-csv/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -F "data=@test-n8n-input/example_end_of_semester_plans.csv"
```

**Expected**:
- n8n processes CSV
- Groq generates content for each row
- Django creates 4 events
- Response: `{created_count: 4, errors: []}`

### Step 5: Verify Events in Database

```bash
curl -X GET http://localhost:8000/api/events/pending-refinement/ \
  -H "Authorization: Bearer <staff_token>"
```

**Expected**:
```json
{
  "count": 4,
  "results": [
    {
      "id": 101,
      "title": "Tuition Fee Deadline",
      "generation_status": "pending",
      "generated_content": {
        "social_post": "🎓 Reminder: Tuition fee due Dec 12...",
        "email_body": "Dear students and parents,\n\nThis is a reminder...",
        "article_body": "Tuition Fee Payment Deadline...",
        ...
      }
    }
  ]
}
```

### Step 6: Refine & Publish

Using frontend component or API:

```bash
# Direct edit
curl -X POST http://localhost:8000/api/events/101/refine-chatbot/ \
  -H "Authorization: Bearer <staff_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "refinement_type": "direct_edit",
    "content": "🎓 Quick reminder: Tuition due Dec 12! Pay now to avoid holds.",
    "field": "social_post"
  }'

# Get suggestions
curl -X POST http://localhost:8000/api/events/101/refine-chatbot/ \
  -H "Authorization: Bearer <staff_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "refinement_type": "prompt",
    "content": "Make this more urgent and add a link to payment portal",
    "field": "social_post"
  }'

# Publish
curl -X POST http://localhost:8000/api/events/bulk-publish/ \
  -H "Authorization: Bearer <staff_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "event_ids": [101, 102, 103, 104],
    "visibility": "public",
    "generation_status": "ready"
  }'
```

---

## Google Calendar Integration (Optional)

If you also want to sync to Google Calendar:

### Prerequisites

1. **Google Cloud Project** with Calendar API enabled
2. **OAuth 2.0 credentials** for n8n (service account or personal)
3. **Calendar ID** (usually email@example.com)

### Setup in n8n

1. Open `schedule_upload_csv_to_calendar.json` workflow
2. Find "Create an event" node (Google Calendar)
3. Click Credentials → "Add new credential type: Google Calendar"
4. Authenticate with Google account
5. Select target calendar
6. Save

### Test Google Calendar Sync

```bash
# Post to /webhook-test/import-schedule
curl -X POST http://localhost:5678/webhook-test/import-schedule \
  -H "Content-Type: multipart/form-data" \
  -F "data=@test-n8n-input/example_end_of_semester_plans.csv"
```

**Expected**:
- n8n processes CSV
- Calculates notification dates from `Notify_Rule`
- Creates events in your Google Calendar

---

## Troubleshooting

### CSV Import Returns 503

```
Symptom: "n8n webhook not configured"
```

**Fix**:
1. Check n8n service: `docker ps | grep n8n`
2. Check Django setting: `N8N_IMPORT_WEBHOOK = 'http://cos40005_n8n:5678/webhook-test/csv-import'`
3. Verify n8n webhook is enabled (workflow active)

### No Events Created After Import

```
Symptom: "created_count": 0
```

**Debug**:
1. Check n8n logs: `docker logs cos40005_n8n`
2. Check Groq API: Is API key valid? Is model available?
3. Check Django logs: `docker logs cos40005_backend`
4. Verify CSV format: Required columns present?

### Groq Returns Empty Suggestions

```
Symptom: "suggestions": []
```

**Fix**:
1. Check n8n Groq credentials configuration
2. Check Groq API rate limits
3. Verify prompt is being sent correctly
4. Try with shorter prompt

### Events Not Appearing in Refinement UI

```
Symptom: GET /api/events/pending-refinement/ returns empty
```

**Debug**:
1. Check database: `psql -c "SELECT id, title, generation_status FROM core_event;"`
2. Verify events were actually created during import
3. Check generation_status is "pending": `SELECT id, generation_status FROM core_event WHERE id = 101;`

---

## Summary

### Three Independent Workflows

| Workflow | Input | Process | Output | Django Table |
|----------|-------|---------|--------|---------------|
| **csv_to_events_pipeline** | CSV file | Parse → Groq generate → Django create | Event records | core_event |
| **event_refinement_chatbot** | Event ID + prompt/edit | Groq refine or direct update | Suggestions or confirmation | core_event (updated) |
| **schedule_upload_csv_to_calendar** | CSV file | Parse → Calculate dates → GCal sync | Calendar events | External: Google Calendar |

### Integration Points

```
Staff                  Django                     n8n
────────────────────────────────────────────────────────
  Upload CSV  →  /api/events/import-csv/  →  csv_to_events_pipeline
                                              (Groq LLM)
                                                  ↓
                                  /api/events/batch-create-webhook/
  See pending  ←  /api/events/pending-refinement/  ←  DB
  
  Click refine →  /api/events/{id}/refine-chatbot/ → event_refinement_chatbot
                                                      (Groq LLM)
                                                          ↓
                                        Frontend displays suggestions
  
  Select        →  /api/events/{id}/apply-suggestion/
  suggestion        (Direct DB update)
  
  Publish      →  /api/events/bulk-publish/
```

---

**Status**: All three workflows ready for use
**Last Updated**: 2025-01-25
