# Implementation Summary: Seamless Chatbot Event Management

## What's Been Built

### ✅ Backend Implementation

**New API Endpoints** (in `src/backend/core/views_api.py`):

1. **POST `/api/events/{id}/refine-chatbot/`**
   - Supports both prompt-based and direct editing
   - Routes to n8n for prompt suggestions
   - Directly updates database for direct edits
   - Returns suggestions or confirmation

2. **POST `/api/events/{id}/apply-suggestion/`**
   - Staff selects one of n8n-generated suggestions
   - Updates `generated_content` field
   - Marks event as `pending` ready for publish

3. **Existing Endpoints** (already working):
   - `POST /api/events/batch-create-webhook/` — n8n callback for CSV import
   - `GET /api/events/pending-refinement/` — List events awaiting refinement
   - `POST /api/events/bulk-publish/` — Publish multiple events

### ✅ Frontend Implementation

**New React Component** (`src/frontend/src/components/EventRefinementChatbot.jsx`):

```jsx
<EventRefinementChatbot 
  eventId={123} 
  onClose={handleClose}
  onPublish={handlePublish}
/>
```

**Features**:
- Tab navigation for 6 content fields (English social, email, article + Vietnamese variants)
- **Direct Edit Mode** — Type/paste content, apply immediately
- **AI Suggestions Mode** — Send natural language prompt, Groq generates alternatives
- **Suggestion Browser** — Select and apply suggestions with one click
- Real-time preview of current content
- Status indicator (ready to publish or not)

### ✅ n8n Workflows Created

**1. `csv_to_events_pipeline.json`** (in `/n8n_backups/`)
   - Webhook: `POST /webhook-test/csv-import`
   - Parses CSV → Validates → Generates content (Groq) → Calls Django
   - Creates events with `generated_content` pre-populated

**2. `event_refinement_chatbot.json`** (in `/n8n_backups/`)
   - Webhook: `POST /webhook-test/event-refinement`
   - Receives refinement request (prompt or direct edit)
   - If prompt: Calls Groq to generate alternatives
   - Returns suggestions to frontend

### ✅ Database Integration

**Event Model Fields** (already exist, now utilized):
- `generated_content` (JSONB) — Stores social_post, email_body, article_body, etc.
- `generation_status` — Tracks state: idle → pending → ready → published
- `generation_meta` (JSONB) — Stores refinement history (who refined, when, what was changed)

### ✅ Configuration

**Django Settings** (`config/settings/dev.py`):
```python
N8N_IMPORT_WEBHOOK = 'http://cos40005_n8n:5678/webhook-test/csv-import'
N8N_REFINE_WEBHOOK = 'http://cos40005_n8n:5678/webhook-test/event-refinement'
```

---

## Complete User Journey

### Scenario 1: CSV Upload → Automatic Generation

```
1. Staff uploads example_end_of_semester_plans.csv
   ↓
2. Django /api/events/import-csv/ receives file
   ↓
3. Forwards to n8n webhook /csv-import
   ↓
4. n8n pipeline:
   - Parses CSV rows (Event_Title, Event_Date, etc.)
   - Validates required fields
   - Calls Groq LLM for each event
   - Gets back: social_post, email_subject, article_body, Vietnamese variants
   ↓
5. n8n POSTs back to Django /api/events/batch-create-webhook/
   - Creates 4 events with generated_content populated
   ↓
6. Events appear in /api/events/pending-refinement/
   - Status: "pending" (ready for refinement)
   ↓
7. Staff sees: "4 events created, ready for refinement"
```

### Scenario 2: Direct Edit Refinement

```
1. Staff views event in EventRefinementChatbot
   - Tab 1: Social Media Post
   - Current content: "Tuition Fee Deadline: Pay by Dec 12..."
   ↓
2. Staff clicks "Direct Edit Mode"
   ↓
3. Staff types new content: "🎓 Hey students! Important: Tuition Fee Due..."
   ↓
4. Click "Apply Edit"
   ↓
5. Django /api/events/{id}/refine-chatbot/ 
   - refinement_type: "direct_edit"
   - Updates event.generated_content['social_post']
   - Marks as generation_status: "pending"
   ↓
6. Frontend updates preview immediately
   - "Content updated successfully ✓"
   ↓
7. Staff repeats for email_body, article_body
   ↓
8. Click "Publish Event" → Event goes public
```

### Scenario 3: Prompt-Based AI Refinement

```
1. Staff views event in EventRefinementChatbot
   - Current: "Tuition Fee Deadline: Pay by Dec 12..."
   ↓
2. Staff clicks "AI Suggestions Mode"
   ↓
3. Staff types: "Make this more casual and add relevant emojis"
   ↓
4. Click "Get Suggestions"
   ↓
5. Django /api/events/{id}/refine-chatbot/
   - refinement_type: "prompt"
   - Forwards to n8n webhook /event-refinement
   ↓
6. n8n pipeline:
   - Receives prompt: "Make this more casual..."
   - Calls Groq with original content + instruction
   - Gets back: 3 alternative versions
   ↓
7. Frontend displays suggestions:
   ✓ "🎓 Hey! Heads up: Tuition due Dec 12..."
   ✓ "💰 Don't miss: Tuition payment deadline is Dec 12..."
   ✓ "📚 Quick reminder: Time to pay tuition (Dec 12)..."
   ↓
8. Staff clicks "Apply" on suggestion #1
   ↓
9. Django /api/events/{id}/apply-suggestion/
   - Updates generated_content['social_post']
   - Marks as "pending"
   ↓
10. Frontend shows updated preview
    - "Suggestion applied ✓"
    ↓
11. Staff can further edit or publish
```

---

## Data Flow Architecture

```
Staff Action                Backend Endpoint           n8n Workflow           Database Result
─────────────────────────────────────────────────────────────────────────────────────────────

Upload CSV
  ↓
POST /api/events/import-csv/
  ├─ Validate CSV
  ├─ Forward file to n8n
  │                    → csv_to_events_pipeline
  │                    ├─ Parse CSV rows
  │                    ├─ For each row:
  │                    │  └─ Groq: Generate content
  │                    ├─ Batch payload
  │                    └─ POST back to /batch-create-webhook/
  └─ Returns 200 OK
                       ↓
                    POST /api/events/batch-create-webhook/
                       ├─ Create Event records
                       ├─ Set generated_content (JSONB)
                       ├─ Set generation_status = "pending"
                       └─ Return {created_count: 4}
                                                   ↓
                                            PostgreSQL events table
                                            ├─ event_id: 101
                                            ├─ title: "Tuition Fee"
                                            ├─ generated_content: {
                                            │   "social_post": "...",
                                            │   "email_body": "...",
                                            │   "article_body": "..."
                                            │  }
                                            ├─ generation_status: "pending"
                                            └─ generation_meta: {}

─────────────────────────────────────────────────────────────────────────────────────────────

View in Chatbot
  ↓
GET /api/events/pending-refinement/
  ├─ Query events where generation_status IN ["pending", "idle"]
  └─ Return array with generated_content
                                                   ↓
                                            Frontend displays:
                                            - Tabs for each field
                                            - Current content preview
                                            - Direct Edit button
                                            - AI Suggestions button

─────────────────────────────────────────────────────────────────────────────────────────────

Direct Edit: Staff types new content

  ↓
POST /api/events/{id}/refine-chatbot/
{
  "refinement_type": "direct_edit",
  "content": "New text",
  "field": "social_post"
}
  ├─ Update event.generated_content['social_post']
  ├─ Set generation_meta['last_refined_by']
  └─ Return 200 OK with updated content
                                                   ↓
                                            PostgreSQL events table
                                            ├─ UPDATE event SET
                                            │  generated_content = {...}
                                            │  generation_meta = {...}
                                            └─ generation_status = "pending"

─────────────────────────────────────────────────────────────────────────────────────────────

AI Refinement: Staff sends prompt

  ↓
POST /api/events/{id}/refine-chatbot/
{
  "refinement_type": "prompt",
  "content": "Make more casual",
  "field": "social_post"
}
  ├─ Build payload: {event_id, original_content, prompt}
  └─ Forward to n8n webhook
                    → event_refinement_chatbot
                    ├─ Route by refinement_type
                    ├─ Groq: Generate alternatives
                    │  Input: original + prompt
                    │  Output: 3 alternatives
                    └─ Return to Django
  ↓
  Return {type: "suggestions", suggestions: [...]}
                                                   ↓
                                            Frontend displays:
                                            - List of suggestions
                                            - "Apply" button per suggestion

─────────────────────────────────────────────────────────────────────────────────────────────

Staff selects suggestion

  ↓
POST /api/events/{id}/apply-suggestion/
{
  "suggestion": "Selected suggestion text",
  "field": "social_post"
}
  ├─ Update event.generated_content['social_post']
  └─ Return 200 OK
                                                   ↓
                                            PostgreSQL events table
                                            ├─ UPDATE event SET
                                            │  generated_content[social_post] = suggestion
                                            └─ generation_meta[last_suggestion_applied_at]

─────────────────────────────────────────────────────────────────────────────────────────────

Staff publishes

  ↓
POST /api/events/bulk-publish/
{
  "event_ids": [101],
  "visibility": "public",
  "generation_status": "ready"
}
  ├─ Bulk update events
  └─ Return {updated_count: 1}
                                                   ↓
                                            PostgreSQL events table
                                            ├─ UPDATE event SET
                                            │  visibility = "public"
                                            │  generation_status = "ready"
                                            └─ updated_at = NOW()
```

---

## Files Modified/Created

### Backend Changes
- ✅ `src/backend/core/views_api.py` — Added `refine_chatbot` & `apply_suggestion` endpoints
- ✅ `config/settings/dev.py` — Updated webhook URLs for n8n

### Frontend Changes
- ✅ `src/frontend/src/components/EventRefinementChatbot.jsx` — New chatbot component (260 lines)

### n8n Workflows
- ✅ `n8n_backups/csv_to_events_pipeline.json` — CSV import pipeline
- ✅ `n8n_backups/event_refinement_chatbot.json` — Refinement suggestions pipeline

### Documentation
- ✅ `doc/CHATBOT_REFINEMENT_COMPLETE_GUIDE.md` — Comprehensive 300+ line guide

---

## Next Steps: Import & Test

### 1. Import n8n Workflows
```bash
# In n8n UI (http://localhost:5678):
# - Go to "Import" 
# - Upload: n8n_backups/csv_to_events_pipeline.json
# - Upload: n8n_backups/event_refinement_chatbot.json
# - Verify webhooks are enabled
```

### 2. Configure Groq Credentials
```bash
# In n8n UI:
# - Settings → Credentials
# - Add "Groq account" credential with API key
# - Model: llama-3.3-70b-versatile
```

### 3. Test CSV Import
```bash
curl -X POST http://localhost:8000/api/events/import-csv/ \
  -H "Authorization: Bearer <staff_token>" \
  -F "data=@test-n8n-input/example_end_of_semester_plans.csv"
```

### 4. Integrate Frontend Component
```jsx
// In staff management page:
import EventRefinementChatbot from '../components/EventRefinementChatbot';

// Render:
<EventRefinementChatbot 
  eventId={eventId}
  onClose={handleClose}
  onPublish={handlePublish}
/>
```

### 5. Test End-to-End
- Upload CSV → 4 events created ✓
- See events in pending-refinement ✓
- Open EventRefinementChatbot ✓
- Try direct edit ✓
- Try AI suggestions ✓
- Publish event ✓

---

## Why This Design is Seamless

1. **Bi-directional Integration** — Frontend ↔ Django ↔ n8n ↔ Groq (smooth data flow)
2. **Database-Backed** — All content stored in PostgreSQL with full refinement history
3. **Immediate Feedback** — Direct edits apply instantly, prompts return suggestions in seconds
4. **Staff Control** — Two refinement modes (direct + AI) for flexibility
5. **Stateful** — generation_status & generation_meta track everything
6. **Scalable** — Batch operations support 100s of events from single CSV

---

**Status**: Ready for n8n import and testing
**Created**: 2025-01-25
