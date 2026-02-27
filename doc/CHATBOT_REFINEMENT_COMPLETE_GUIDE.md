# Complete Event Management Workflow Integration Guide

## Overview

This guide documents the **complete end-to-end workflow** for the CMS event management system with n8n integration, supporting three distinct processes:

1. **CSV → Events Pipeline** — Staff uploads CSV → n8n processes → Django creates events
2. **Event Refinement Chatbot** — Staff refines auto-generated content via prompt or direct editing
3. **Calendar Integration** — Legacy calendar sync via Google Calendar

---

## 1. CSV to Events Pipeline

### Architecture

```
Staff Frontend
    ↓ (Upload CSV)
Django /api/events/import-csv/
    ↓ (Forward to n8n)
n8n: csv_to_events_pipeline.json
    ├─ Extract CSV rows
    ├─ Validate fields
    ├─ Generate content (Groq LLM)
    └─ Callback to Django
Django /api/events/batch-create-webhook/
    └─ Create events with generated_content
```

### CSV Format

Upload CSV with columns:
```
Event_Title | Event_Date | Location | Start_Time | Notify_Rule | Channels | Target_Audience | Dept_Filter | Content_Remarks | Assets_URL
```

Example:
```csv
Test Event,2025-11-26,demo,08:00,same day,Email,"students","all","Tone: professional; topic: test event for n8n email notification",https://drive.google.com/drive/...
```

### n8n Workflow: `csv_to_events_pipeline.json`

**Webhook Path**: `POST /webhook-test/csv-import`

**Flow**:
1. **CSV Upload Webhook** — Receives multipart form-data with file
2. **Extract CSV Rows** — Parses CSV headers and data
3. **Validate CSV Rows** — Checks required fields (Event_Title, Event_Date, Start_Time)
4. **Groq: Generate Content** — Calls Groq llama-3.3-70b-versatile to generate:
   - `social_post` — Facebook/TikTok snippet
   - `email_subject`, `email_body` — Email template
   - `article_title`, `article_body` — Long-form article
   - Vietnamese translations
5. **Parse Generated Content** — Extracts JSON from Groq response
6. **Django: Batch Create Events** — POSTs to `/api/events/batch-create-webhook/`
7. **Format Response** — Returns success/failure summary

### Backend Endpoint: POST `/api/events/batch-create-webhook/`

**Permission**: Staff only

**Payload**:
```json
{
  "events": [
    {
      "title": "Event Title",
      "description": "Description",
      "start": "2025-11-26T08:00:00Z",
      "end": "2025-11-26T09:00:00Z",
      "location": "Location",
      "visibility": "staff",
      "generated_content": {
        "social_post": "...",
        "email_body": "...",
        "article_body": "..."
      },
      "generation_status": "ready"
    }
  ]
}
```

**Response**:
```json
{
  "created_count": 3,
  "errors": [],
  "message": "3 events created successfully"
}
```

---

## 2. Event Refinement Chatbot

### Architecture

```
Staff Frontend (EventRefinementChatbot.jsx)
    ├─ View: Generated content preview
    ├─ Tab 1: Direct Edit (edit text inline)
    └─ Tab 2: AI Suggestions (prompt-based refinement)
            ↓
Django /api/events/{id}/refine-chatbot/
    ├─ If prompt: → n8n event_refinement_chatbot.json
    └─ If direct: → Update immediately
            ↓
n8n (if prompt mode)
    ├─ Validate request
    ├─ Split by type (prompt vs direct_edit)
    ├─ Groq: Generate alternatives
    └─ Return suggestions
            ↓
Frontend: Displays suggestions
Staff: Selects one
            ↓
Django /api/events/{id}/apply-suggestion/
    └─ Update generated_content + mark as pending
```

### Frontend Component: `EventRefinementChatbot.jsx`

**Props**:
- `eventId` — Event ID to refine
- `onClose` — Callback when done
- `onPublish` — Callback to publish event

**Features**:
- **Tab Navigation** — Switch between social_post, email_body, article_body (English & Vietnamese)
- **Direct Edit Mode** — Type/paste content directly into text field
- **AI Suggestions Mode** — Send natural language prompt (e.g., "make it casual" or "add emojis")
- **Suggestion Selection** — Browse AI-generated alternatives, apply with one click
- **Preview** — See current content in real-time

**Usage**:
```jsx
<EventRefinementChatbot 
  eventId={123} 
  onClose={() => setOpen(false)}
  onPublish={(id) => handlePublish(id)}
/>
```

### Backend Endpoints

#### POST `/api/events/{id}/refine-chatbot/`

**Permission**: Staff only

**Payload (Direct Edit)**:
```json
{
  "refinement_type": "direct_edit",
  "content": "New content text",
  "field": "social_post"  // or "email_body", "article_body", "all"
}
```

**Response**:
```json
{
  "type": "confirmation",
  "event_id": 123,
  "message": "Content updated successfully",
  "updated_field": "social_post",
  "generated_content": { ... },
  "ready_to_publish": true
}
```

**Payload (Prompt-Based)**:
```json
{
  "refinement_type": "prompt",
  "content": "Make this more casual and add relevant emojis",
  "field": "social_post"
}
```

**Response**:
```json
{
  "type": "suggestions",
  "event_id": 123,
  "suggestions": [
    "🎓 Hey students! Check out our amazing...",
    "✨ Join us for an unforgettable experience..."
  ],
  "user_request": "Make this more casual and add relevant emojis",
  "field": "social_post",
  "message": "Suggestions generated. Select one to apply."
}
```

#### POST `/api/events/{id}/apply-suggestion/`

**Permission**: Staff only

**Payload**:
```json
{
  "suggestion": "The selected suggestion text",
  "field": "social_post"
}
```

**Response**:
```json
{
  "message": "Suggestion applied successfully",
  "field": "social_post",
  "suggestion": "...",
  "generated_content": { ... },
  "ready_to_publish": true
}
```

### n8n Workflow: `event_refinement_chatbot.json`

**Webhook Path**: `POST /webhook-test/event-refinement`

**Flow**:
1. **Refinement Webhook** — Receives refinement request
2. **Validate Refinement Request** — Checks event_id, refinement_type, content
3. **Split by Type** — Routes to prompt or direct_edit handler
4. **If Prompt**:
   - Groq: Generate alternatives
   - Parse suggestions
5. **If Direct Edit**:
   - Pass through content
6. **Merge Results** — Combine both paths
7. **Format Frontend Response** — Return suggestions or confirmation

---

## 3. Event Publication

### Backend Endpoint: POST `/api/events/bulk-publish/`

**Permission**: Staff only

**Payload**:
```json
{
  "event_ids": [1, 2, 3],
  "visibility": "public",
  "generation_status": "ready"
}
```

**Response**:
```json
{
  "message": "Updated 3 events",
  "updated_count": 3,
  "visibility": "public",
  "generation_status": "ready"
}
```

### Backend Endpoint: GET `/api/events/pending-refinement/`

**Permission**: Staff only

**Query Parameters**:
- `status` — Filter by generation_status (pending, idle)
- `unit_id` — Filter by unit
- `days` — Last N days

**Response**:
```json
{
  "count": 5,
  "results": [
    {
      "id": 123,
      "title": "Event Title",
      "generation_status": "pending",
      "generated_content": { ... },
      "created_at": "2025-01-25T10:00:00Z"
    }
  ]
}
```

---

## 4. Database Integration

### Event Model Fields

```python
class Event(models.Model):
    title = models.CharField(max_length=500)
    description = models.TextField()
    start = models.DateTimeField()
    end = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    visibility = models.CharField(choices=[
        ('public', 'Public'),
        ('unit', 'Unit Only'),
        ('staff', 'Staff Only')
    ])
    
    # Generation tracking
    generated_content = models.JSONField(default=dict, blank=True)
    # Structure: {
    #   "social_post": "...",
    #   "email_subject": "...",
    #   "email_body": "...",
    #   "article_title": "...",
    #   "article_body": "...",
    #   "vietnamese_social_post": "...",
    #   "vietnamese_email_body": "...",
    #   "vietnamese_article_body": "..."
    # }
    
    generation_status = models.CharField(choices=[
        ('idle', 'Not Generated'),
        ('pending', 'Pending'),
        ('ready', 'Ready'),
        ('failed', 'Failed')
    ])
    
    generation_meta = models.JSONField(default=dict, blank=True)
    # Structure: {
    #   "prompt_used": "...",
    #   "tone": "...",
    #   "last_refined_by": "user@example.com",
    #   "last_refined_at": "2025-01-25T10:00:00Z",
    #   "last_suggestion_applied_at": "2025-01-25T10:00:00Z"
    # }
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_generated_at = models.DateTimeField(null=True, blank=True)
```

---

## 5. Configuration

### Django Settings (`config/settings/dev.py`)

```python
# n8n webhooks
N8N_IMPORT_WEBHOOK = 'http://cos40005_n8n:5678/webhook-test/csv-import'
N8N_REFINE_WEBHOOK = 'http://cos40005_n8n:5678/webhook-test/event-refinement'

# Optional authentication
N8N_API_KEY = None
N8N_WEBHOOK_SECRET = None  # Set to require X-N8N-SECRET header
```

### Docker Compose (`docker-compose-dev.yaml`)

```yaml
services:
  n8n:
    image: n8n:latest
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=false
      - N8N_HOST=localhost
    volumes:
      - n8n_data:/home/node/.n8n
    networks:
      - cos40005-network

  db:
    # ... PostgreSQL configuration

  backend:
    # ... Django configuration
    depends_on:
      - n8n
```

---

## 6. Testing the Workflows

### Test CSV Upload

```bash
# Upload CSV file
curl -X POST http://localhost:8000/api/events/import-csv/ \
  -H "Authorization: Bearer <staff_token>" \
  -F "data=@example_end_of_semester_plans.csv"

# Expected response: Event created count + status
```

### Test Chatbot Refinement

```bash
# Get pending events
curl http://localhost:8000/api/events/pending-refinement/ \
  -H "Authorization: Bearer <staff_token>"

# Send prompt-based refinement
curl -X POST http://localhost:8000/api/events/123/refine-chatbot/ \
  -H "Authorization: Bearer <staff_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "refinement_type": "prompt",
    "content": "Make this more casual and add emojis",
    "field": "social_post"
  }'

# Send direct edit
curl -X POST http://localhost:8000/api/events/123/refine-chatbot/ \
  -H "Authorization: Bearer <staff_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "refinement_type": "direct_edit",
    "content": "New content text here",
    "field": "social_post"
  }'
```

### Test Bulk Publish

```bash
curl -X POST http://localhost:8000/api/events/bulk-publish/ \
  -H "Authorization: Bearer <staff_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "event_ids": [1, 2, 3],
    "visibility": "public",
    "generation_status": "ready"
  }'
```

---

## 7. Deployment Checklist

- [ ] n8n workflows imported (`csv_to_events_pipeline.json`, `event_refinement_chatbot.json`)
- [ ] Groq API credentials configured in n8n (model: `llama-3.3-70b-versatile`)
- [ ] Webhook paths set in n8n (POST `/webhook-test/csv-import`, `/webhook-test/event-refinement`)
- [ ] Django settings updated with n8n webhook URLs
- [ ] Frontend component `EventRefinementChatbot.jsx` installed
- [ ] Staff roles have permissions for `/api/events/batch-create-webhook/`, `/api/events/refine-chatbot/`, `/api/events/apply-suggestion/`
- [ ] Docker volumes preserved for n8n workflow persistence
- [ ] Test end-to-end CSV upload → refinement → publish flow

---

## 8. Troubleshooting

### CSV upload returns 503
- Check: n8n service is running (`docker ps | grep n8n`)
- Check: `N8N_IMPORT_WEBHOOK` in settings points to correct URL
- Check: n8n workflow `csv_to_events_pipeline.json` is active and webhook is enabled

### Refine-chatbot returns empty suggestions
- Check: Groq API key configured in n8n
- Check: n8n workflow `event_refinement_chatbot.json` is active
- Check: Request contains valid `event_id` and `refinement_type`

### Events not appearing after CSV upload
- Check: Django logs for batch-create errors
- Check: Groq LLM response format (should be valid JSON)
- Check: Database permissions for event creation

### Frontend chatbot not responding
- Check: Browser console for API errors
- Check: JWT token is valid (staff role)
- Check: Event exists in database

---

## 9. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────┐         ┌──────────────────────────────┐   │
│  │  Upload CSV Page    │         │ EventRefinementChatbot.jsx   │   │
│  │  (import-csv)       │ ─────┬──│  - Direct edit / AI prompts  │   │
│  └─────────────────────┘      │  │  - Tabbed content preview    │   │
│                               │  │  - Apply suggestions         │   │
│                               │  └──────────────────────────────┘   │
│                               │                                      │
└───────────────────────────────┼──────────────────────────────────────┘
                                │
                                ↓ (Bearer token JWT)
┌─────────────────────────────────────────────────────────────────────┐
│                     Django Backend (DRF)                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────────────┐  ┌──────────────────────┐                │
│  │ import-csv           │  │ refine-chatbot       │                │
│  │ (POST)               │  │ (POST)               │                │
│  └──────────┬───────────┘  └──────────┬───────────┘                │
│             │                         │                             │
│             ├─ Validate CSV           ├─ Validate request           │
│             └─ Forward to n8n         └─ Forward to n8n (if prompt) │
│                                                                      │
│  ┌──────────────────────┐  ┌──────────────────────┐                │
│  │ batch-create-webhook │  │ apply-suggestion     │                │
│  │ (POST)               │  │ (POST)               │                │
│  └──────────┬───────────┘  └──────────┬───────────┘                │
│             │                         │                             │
│             ├─ Create events          └─ Update generated_content   │
│             ├─ Set generation_status    Save to database            │
│             └─ Save to PostgreSQL                                    │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ PostgreSQL Event Model                                     │    │
│  │ ├─ id, title, start, end, location, visibility            │    │
│  │ ├─ generated_content (JSONB)                              │    │
│  │ ├─ generation_status (idle/pending/ready/failed)          │    │
│  │ ├─ generation_meta (JSON with refinement history)         │    │
│  │ └─ created_by, created_at, updated_at                     │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
└──────────────────────────────┬───────────────────────────────────────┘
                               │
                               ↓ (Webhook callback)
┌─────────────────────────────────────────────────────────────────────┐
│                       n8n Workflows                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────┐                                 │
│  │ csv_to_events_pipeline         │                                 │
│  ├────────────────────────────────┤                                 │
│  │ 1. Webhook: POST /csv-import   │                                 │
│  │ 2. Extract CSV rows            │                                 │
│  │ 3. Validate fields             │                                 │
│  │ 4. Groq: Generate content      │◄────┐                           │
│  │ 5. POST /batch-create-webhook/ │      │                          │
│  └────────────────────────────────┘      │                          │
│                                           │                          │
│  ┌────────────────────────────────┐      │ Groq API                 │
│  │ event_refinement_chatbot       │      │ (llama-3.3-70b)          │
│  ├────────────────────────────────┤      │                          │
│  │ 1. Webhook: POST /event-refine │      │                          │
│  │ 2. Validate request            │      │                          │
│  │ 3. If prompt: Groq generate    │◄─────┤                          │
│  │ 4. Return suggestions          │      │                          │
│  └────────────────────────────────┘      │                          │
│                                           │                          │
│  ┌────────────────────────────────┐      │                          │
│  │ swincms_main (optional)        │      │                          │
│  ├────────────────────────────────┤      │                          │
│  │ 1. Schedule Trigger (daily)    │      │                          │
│  │ 2. AI Agent (custom prompts)   │      │                          │
│  │ 3. Groq: Generate posts        │◄─────┘                          │
│  └────────────────────────────────┘                                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 10. Next Steps

1. **Import n8n Workflows** — In n8n UI, import JSON files from `/n8n_backups/`
2. **Configure Groq** — Add Groq API key to n8n credentials (llama-3.3-70b-versatile)
3. **Test CSV Upload** — Use `example_end_of_semester_plans.csv` from `/test-n8n-input/`
4. **Deploy Frontend** — Install `EventRefinementChatbot.jsx` in staff management pages
5. **Staff Training** — Teach staff to upload CSV → refine content → publish

---

**Last Updated**: 2025-01-25
**Status**: Production Ready (v1.0)
