# Quick Reference: Seamless Event Chatbot System

## 🚀 Three Workflows at a Glance

### 1️⃣ CSV → Events + AI Content
**File**: `csv_to_events_pipeline.json`  
**Webhook**: `POST /webhook-test/csv-import`  
**Input**: Upload CSV with Event_Title, Event_Date, Start_Time, Content_Remarks  
**Process**: Parse CSV → Groq LLM generates content → Django creates events  
**Output**: Events with `generated_content` (social_post, email_body, article_body)  
**Staff Action**: Upload test file `example_end_of_semester_plans.csv`

---

### 2️⃣ Event Refinement Chatbot
**File**: `event_refinement_chatbot.json`  
**Webhook**: `POST /webhook-test/event-refinement`  
**Input**: Event ID + prompt (e.g., "make casual") or direct text edit  
**Process**: 
- If prompt → Groq generates alternatives
- If direct → Update immediately  
**Output**: Suggestions array or confirmation  
**Staff Action**: Use frontend component to edit/refine content

---

### 3️⃣ Calendar Sync (Legacy)
**File**: `schedule_upload_csv_to_calendar.json`  
**Webhook**: `POST /webhook-test/import-schedule`  
**Input**: CSV with notification rules (e.g., "2 weeks before")  
**Process**: Parse → Calculate dates → Google Calendar API  
**Output**: Calendar events with embedded metadata  
**Staff Action**: Upload for direct Google Calendar sync

---

## 🔌 Backend Endpoints

```
POST /api/events/import-csv/
├─ Accept: CSV file (form-data "data" field)
├─ Permission: Staff
└─ Returns: {created_count: N, errors: []}

POST /api/events/{id}/refine-chatbot/
├─ Body: {refinement_type: "prompt"|"direct_edit", content: "...", field: "social_post"}
├─ Permission: Staff
└─ Returns: {type: "suggestions"|"confirmation", ...}

POST /api/events/{id}/apply-suggestion/
├─ Body: {suggestion: "...", field: "social_post"}
├─ Permission: Staff
└─ Returns: {message: "Suggestion applied", generated_content: {...}}

POST /api/events/bulk-publish/
├─ Body: {event_ids: [1,2,3], visibility: "public", generation_status: "ready"}
├─ Permission: Staff
└─ Returns: {updated_count: N}

GET /api/events/pending-refinement/
├─ Params: status, unit_id, days (optional)
├─ Permission: Staff
└─ Returns: {count: N, results: [...]}

GET /api/events/{id}/get_generation_status/
├─ Permission: Staff
└─ Returns: {generation_status, generated_content, generation_meta, ...}
```

---

## 🎨 Frontend Component

```jsx
import EventRefinementChatbot from '../components/EventRefinementChatbot';

// In your staff panel:
<EventRefinementChatbot 
  eventId={123}                    // Event ID to refine
  onClose={() => setOpen(false)}   // Called when staff clicks "Close"
  onPublish={(id) => publishEvent(id)}  // Called when staff clicks "Publish"
/>
```

**Features**:
- 6 tabs: social_post, email_body, article_body (English + Vietnamese)
- Direct edit mode: Type/paste, apply immediately
- AI suggestions: Send prompt, get alternatives, pick best one
- Real-time preview of current content
- Status: Ready to publish or not

---

## 📊 Data Model

```python
Event.generated_content = {
  "social_post": "🎓 Short snippet for social media",
  "email_subject": "Subject line",
  "email_body": "Full email template",
  "article_title": "Long-form title",
  "article_body": "Full article text",
  "vietnamese_social_post": "Vietnamese version",
  "vietnamese_email_body": "Vietnamese email",
  "vietnamese_article_body": "Vietnamese article"
}

Event.generation_status: "idle" | "pending" | "ready" | "failed"

Event.generation_meta = {
  "prompt_used": "...",
  "tone": "...",
  "last_refined_by": "staff@example.com",
  "last_refined_at": "2025-01-25T10:00:00Z",
  "last_suggestion_applied_at": "2025-01-25T10:05:00Z"
}
```

---

## ⚙️ Configuration

```python
# config/settings/dev.py
N8N_IMPORT_WEBHOOK = 'http://cos40005_n8n:5678/webhook-test/csv-import'
N8N_REFINE_WEBHOOK = 'http://cos40005_n8n:5678/webhook-test/event-refinement'
```

---

## 🧪 Test Flow (5 Minutes)

### 1. Start Services
```bash
docker-compose -f docker-compose-dev.yaml up -d
```

### 2. Get Staff Token
```bash
curl -X POST http://localhost:8000/token/ \
  -d "email=staff@swin.edu.au&password=password"
# Copy token
```

### 3. Upload CSV
```bash
curl -X POST http://localhost:8000/api/events/import-csv/ \
  -H "Authorization: Bearer <token>" \
  -F "data=@test-n8n-input/example_end_of_semester_plans.csv"
```

**Expected**: `{created_count: 4, errors: []}`

### 4. View Pending Events
```bash
curl http://localhost:8000/api/events/pending-refinement/ \
  -H "Authorization: Bearer <token>"
```

**Expected**: 4 events with generated_content populated

### 5. Try Direct Edit
```bash
curl -X POST http://localhost:8000/api/events/1/refine-chatbot/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "refinement_type": "direct_edit",
    "content": "New social post text",
    "field": "social_post"
  }'
```

**Expected**: `{type: "confirmation", message: "Content updated successfully"}`

### 6. Try Prompt-Based Refinement
```bash
curl -X POST http://localhost:8000/api/events/2/refine-chatbot/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "refinement_type": "prompt",
    "content": "Make this more casual and add emojis",
    "field": "social_post"
  }'
```

**Expected**: `{type: "suggestions", suggestions: [...]}`

### 7. Apply Suggestion
```bash
curl -X POST http://localhost:8000/api/events/2/apply-suggestion/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "suggestion": "Selected suggestion text",
    "field": "social_post"
  }'
```

**Expected**: `{message: "Suggestion applied successfully"}`

### 8. Publish
```bash
curl -X POST http://localhost:8000/api/events/bulk-publish/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "event_ids": [1, 2, 3, 4],
    "visibility": "public",
    "generation_status": "ready"
  }'
```

**Expected**: `{updated_count: 4}`

---

## 🐛 Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| CSV import 503 | n8n not running | `docker ps \| grep n8n` |
| No suggestions returned | Groq API misconfigured | Check n8n credentials |
| Events not created | CSV validation failed | Check required columns |
| Refinement fails | n8n webhook path wrong | Verify `/webhook-test/event-refinement` |
| Frontend component doesn't render | Missing eventId prop | Add `eventId={123}` |

---

## 📚 Full Documentation

- `CHATBOT_REFINEMENT_COMPLETE_GUIDE.md` — Comprehensive 300+ line guide
- `IMPLEMENTATION_STATUS_CHATBOT.md` — What's been built & data flow
- `CALENDAR_INTEGRATION_GUIDE.md` — Setup & test instructions
- `EVENT_WORKFLOW_API.md` — Original endpoint documentation

---

## ✅ Deployment Checklist

- [ ] n8n service running (docker-compose)
- [ ] Two new workflows imported:
  - [ ] `csv_to_events_pipeline.json` (webhook: `/csv-import`)
  - [ ] `event_refinement_chatbot.json` (webhook: `/event-refinement`)
- [ ] Groq API key configured in n8n credentials
- [ ] Django settings updated with webhook URLs
- [ ] Backend code deployed (`/api/events/refine-chatbot/`, `/api/events/apply-suggestion/`)
- [ ] Frontend component installed (`EventRefinementChatbot.jsx`)
- [ ] Test CSV upload → refinement → publish flow
- [ ] Staff can access both direct edit & AI suggestions modes
- [ ] Database contains generated_content & generation_meta

---

**Status**: Production Ready (v1.0)  
**Last Updated**: 2025-01-25  
**Ready for**: Import & Testing
