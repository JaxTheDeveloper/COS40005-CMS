# System Architecture: Event Chatbot Integration

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          STAFF INTERFACE (React)                                 │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌──────────────────────────────┐      ┌────────────────────────────────────┐  │
│  │  1. Upload CSV Page          │      │  2. EventRefinementChatbot         │  │
│  │                              │      │                                    │  │
│  │  [Choose File] [Upload]      │      │  ┌─────────────────────────────┐  │  │
│  │                              │      │  │ Content Tabs:               │  │  │
│  │  📊 Processing...            │      │  │ • Social Post               │  │  │
│  │  ✓ 4 events created          │      │  │ • Email Body                │  │  │
│  │  Ready for refinement        │      │  │ • Article Body              │  │  │
│  │                              │      │  │ • (+ Vietnamese variants)   │  │  │
│  │                              │      │  └─────────────────────────────┘  │  │
│  │                              │      │                                    │  │
│  │                              │      │  ┌──────────────────────────────┐  │  │
│  │                              │      │  │ Current Content Preview    │  │  │
│  │                              │      │  │                            │  │  │
│  │                              │      │  │ "Tuition Fee Deadline:     │  │  │
│  │                              │      │  │  Pay by Dec 12 2025..."    │  │  │
│  │                              │      │  │                            │  │  │
│  │                              │      │  │ [Edit] [Get AI Suggestions]│  │  │
│  │                              │      │  └──────────────────────────────┘  │  │
│  │                              │      │                                    │  │
│  │                              │      │  Direct Edit | AI Suggestions      │  │
│  │                              │      │                                    │  │
│  │                              │      │  ┌─────────────────────────────┐  │  │
│  │                              │      │  │ [Type new content]          │  │  │
│  │                              │      │  │                             │  │  │
│  │                              │      │  │ [Cancel] [Apply Edit]       │  │  │
│  │                              │      │  └─────────────────────────────┘  │  │
│  │                              │      │                                    │  │
│  │                              │      │  ┌─────────────────────────────┐  │  │
│  │                              │      │  │ ✓ Ready to Publish          │  │  │
│  │                              │      │  └─────────────────────────────┘  │  │
│  │                              │      │                                    │  │
│  │                              │      │ [Close] [Publish Event]            │  │
│  └──────────────────────────────┘      └────────────────────────────────────┘  │
│                                                                                  │
└────┬─────────────────────────────────────────────────────────────────────────┬──┘
     │ POST /api/events/import-csv/              POST /api/events/{id}/refine-chatbot/
     │ (with multipart CSV)                      (with refinement_type & content)
     ↓                                            ↓
┌──────────────────────────────────────────────────────────────────────────────────┐
│                          DJANGO REST API                                         │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  EventViewSet.import_csv()                    EventViewSet.refine_chatbot()      │
│  ├─ Validate CSV                             ├─ If "direct_edit":                │
│  ├─ Forward to n8n webhook                   │  └─ Update DB immediately        │
│  └─ Wait for events to be created            ├─ If "prompt":                     │
│                                              │  ├─ Forward to n8n               │
│  EventViewSet.batch_create_webhook()         │  └─ Return suggestions           │
│  ├─ Receive callback from n8n                                                    │
│  ├─ Create Event records in bulk             EventViewSet.apply_suggestion()     │
│  ├─ Set generated_content                    ├─ Apply selected suggestion       │
│  ├─ Set generation_status = "pending"        └─ Update DB                       │
│  └─ Return {created_count}                                                       │
│                                              EventViewSet.pending_refinement()   │
│  EventViewSet.bulk_publish()                 └─ List events ready for refine    │
│  ├─ Update visibility & status                                                   │
│  └─ Bulk save                                EventViewSet.get_generation_status()│
│                                              └─ Get event details               │
│                                                                                   │
└────┬──────────────────────────────────┬─────────────────────────────────────┬───┘
     │                                  │                                     │
     ↓                                  ↓                                     ↓
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              n8n WORKFLOWS                                      │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  csv_to_events_pipeline.json                 event_refinement_chatbot.json      │
│  Webhook: POST /webhook-test/csv-import      Webhook: POST /webhook-test/...    │
│                                                                                  │
│  ┌─────────────────────────────────┐         ┌─────────────────────────────┐   │
│  │ 1. CSV Upload Webhook           │         │ 1. Refinement Webhook       │   │
│  │    (receive file)               │         │    (receive request)        │   │
│  └────────────┬────────────────────┘         └────────────┬────────────────┘   │
│               ↓                                            ↓                     │
│  ┌─────────────────────────────────┐         ┌─────────────────────────────┐   │
│  │ 2. Extract CSV Rows             │         │ 2. Validate Request         │   │
│  │    (parse headers)              │         │    (check event_id, type)   │   │
│  └────────────┬────────────────────┘         └────────────┬────────────────┘   │
│               ↓                                            ↓                     │
│  ┌─────────────────────────────────┐         ┌──────────────────────────────┐  │
│  │ 3. Validate CSV Rows            │         │ 3. Split by Type             │  │
│  │    (check required fields)      │         │    ├─ prompt path            │  │
│  └────────────┬────────────────────┘         │    └─ direct_edit path       │  │
│               ↓                                └──────┬──────────────┬──────┘  │
│  ┌──────────────────────────────────────┐           ↓              ↓         │
│  │ 4. Groq: Generate Content           │   ┌──────────────┐  ┌────────────┐ │
│  │    For each row:                     │   │ Groq LLM:    │  │ Direct     │ │
│  │    - social_post                     │   │ Generate     │  │ Pass       │ │
│  │    - email_body                      │   │ alternatives │  │ through    │ │
│  │    - article_body                    │   │              │  │            │ │
│  │    - vietnamese variants             │   └──────┬───────┘  └────┬───────┘ │
│  └────────────┬─────────────────────────┘          ↓               ↓          │
│               ↓                                  ┌─────────────────────────┐  │
│  ┌─────────────────────────────────┐           │ Merge Results           │  │
│  │ 5. Parse Generated Content      │           └──────────┬──────────────┘  │
│  │    (extract from Groq response) │                      ↓                   │
│  └────────────┬────────────────────┘           ┌─────────────────────────┐  │
│               ↓                                 │ Format Response         │  │
│  ┌─────────────────────────────────────────┐  │ - Suggestions (prompt)  │  │
│  │ 6. Django: Batch Create Events          │  │ - Confirmation (direct) │  │
│  │    POST /api/events/batch-create-webhook/ │ └─────────┬──────────────┘  │
│  │    {events: [...]}                      │             ↓                   │
│  └─────────────────────────────────────────┘   Return to Django             │
│                                                                               │
└─────────────────────────────┬──────────────────────────────────────────────┬──┘
                              │                                              │
                              ↓                                              ↓
                     (callback to Django)                         (suggestions or confirmation)
                                                                                   
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           PostgreSQL DATABASE                                    │
├──────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│  core_event table:                                                               │
│  ┌──────┬────────────┬──────────────────────────────────────────────┬────────┐   │
│  │ id   │ title      │ generated_content (JSONB)                    │ status │   │
│  ├──────┼────────────┼──────────────────────────────────────────────┼────────┤   │
│  │ 101  │ Tuition Fee│ {                                            │ ready  │   │
│  │      │            │   "social_post": "🎓 Reminder: Tuition due", │        │   │
│  │      │            │   "email_body": "Dear students...",          │        │   │
│  │      │            │   "article_body": "...",                     │        │   │
│  │      │            │   "vietnamese_social_post": "..."            │        │   │
│  │      │            │ }                                            │        │   │
│  ├──────┼────────────┼──────────────────────────────────────────────┼────────┤   │
│  │ 102  │ Unit Enrol │ {...}                                        │ pending│   │
│  ├──────┼────────────┼──────────────────────────────────────────────┼────────┤   │
│  │ 103  │ Winter Bk. │ {...}                                        │ pending│   │
│  ├──────┼────────────┼──────────────────────────────────────────────┼────────┤   │
│  │ 104  │ Xmas Wish  │ {...}                                        │ pending│   │
│  └──────┴────────────┴──────────────────────────────────────────────┴────────┘   │
│                                                                                   │
│  generation_meta (JSONB):                                                        │
│  {                                                                               │
│    "last_refined_by": "staff@swin.edu.au",                                      │
│    "last_refined_at": "2025-01-25T14:30:00Z",                                   │
│    "last_suggestion_applied_at": "2025-01-25T14:25:00Z"                         │
│  }                                                                               │
│                                                                                   │
└──────────────────────────────────────────────────────────────────────────────────┘


FLOW LEGEND:
─────────────

1️⃣ CSV IMPORT FLOW (Left path):
   Staff uploads CSV
   → Django validates & forwards to n8n
   → n8n parses & generates content via Groq
   → n8n creates events in Django via webhook
   → Events appear in PostgreSQL

2️⃣ REFINEMENT FLOW (Right path):
   Staff sends refinement request (prompt or edit)
   → Django routes to n8n (if prompt) or updates DB directly (if edit)
   → If prompt: Groq generates alternatives
   → Returns suggestions to frontend
   → Staff applies one
   → Event updated in database

3️⃣ PUBLISH FLOW:
   Staff clicks publish
   → Django bulk updates visibility & status
   → Events now public in system
```

---

## 🔀 Request/Response Examples

### Example 1: CSV Upload

```
REQUEST:
────────
POST /api/events/import-csv/
Authorization: Bearer token
Content-Type: multipart/form-data

data: [CSV file]

PROCESSING (n8n):
─────────────────
1. Parse CSV: 4 rows
2. For each row, call Groq LLM
3. POST to /api/events/batch-create-webhook/

RESPONSE:
────────
{
  "created_count": 4,
  "errors": [],
  "message": "CSV imported and events created successfully"
}

DATABASE RESULT:
────────────────
Event #101: {
  title: "Tuition Fee Deadline",
  generated_content: {
    social_post: "🎓 Heads up students: Tuition deadline Dec 12...",
    email_subject: "Important: Tuition Fee Payment",
    email_body: "Dear students and parents...",
    article_body: "Tuition Fee Deadline...",
    vietnamese_social_post: "...",
    vietnamese_email_body: "...",
    vietnamese_article_body: "..."
  },
  generation_status: "pending",
  generation_meta: {}
}
```

---

### Example 2: Prompt-Based Refinement

```
REQUEST:
────────
POST /api/events/101/refine-chatbot/
Authorization: Bearer token
Content-Type: application/json

{
  "refinement_type": "prompt",
  "content": "Make this more casual and add relevant emojis",
  "field": "social_post"
}

PROCESSING (n8n):
─────────────────
1. Receive event_id=101, prompt="make casual..."
2. Get event from Django: current social_post
3. Call Groq with: original + prompt
4. Groq returns 3 alternatives

RESPONSE:
────────
{
  "type": "suggestions",
  "event_id": 101,
  "suggestions": [
    "🎓 Quick heads up! Tuition's due Dec 12—pay now to stay enrolled.",
    "💰 Don't sleep on this: Tuition deadline Dec 12. Time to pay!",
    "📚 Friendly reminder: Your tuition payment deadline is coming Dec 12."
  ],
  "user_request": "Make this more casual and add relevant emojis",
  "field": "social_post"
}

FRONTEND DISPLAYS:
──────────────────
✓ Suggestion 1: "🎓 Quick heads up!..." [Apply]
✓ Suggestion 2: "💰 Don't sleep..."    [Apply]
✓ Suggestion 3: "📚 Friendly..."       [Apply]
```

---

### Example 3: Direct Edit

```
REQUEST:
────────
POST /api/events/101/refine-chatbot/
Authorization: Bearer token
Content-Type: application/json

{
  "refinement_type": "direct_edit",
  "content": "🎓 IMPORTANT: Tuition payment deadline is December 12, 2025",
  "field": "social_post"
}

PROCESSING (Django):
────────────────────
1. Validate: refinement_type = "direct_edit"
2. Update: event.generated_content['social_post'] = new text
3. Set: generation_meta['last_refined_by'] = staff@swin.edu.au
4. Save to database

RESPONSE:
────────
{
  "type": "confirmation",
  "event_id": 101,
  "message": "Content updated successfully",
  "updated_field": "social_post",
  "generated_content": {
    "social_post": "🎓 IMPORTANT: Tuition payment deadline is December 12, 2025",
    ...
  },
  "ready_to_publish": true
}

DATABASE UPDATED:
─────────────────
Event #101 {
  generated_content: {
    social_post: "🎓 IMPORTANT: Tuition payment deadline...", ← UPDATED
    ...
  },
  generation_meta: {
    "last_refined_by": "staff@swin.edu.au",
    "last_refined_at": "2025-01-25T14:30:00Z"
  }
}
```

---

### Example 4: Apply Suggestion

```
REQUEST:
────────
POST /api/events/101/apply-suggestion/
Authorization: Bearer token
Content-Type: application/json

{
  "suggestion": "🎓 Quick heads up! Tuition's due Dec 12—pay now to stay enrolled.",
  "field": "social_post"
}

PROCESSING (Django):
────────────────────
1. Find event #101
2. Update: event.generated_content['social_post'] = suggestion
3. Update: generation_meta['last_suggestion_applied_at']
4. Save to database

RESPONSE:
────────
{
  "message": "Suggestion applied successfully",
  "field": "social_post",
  "suggestion": "🎓 Quick heads up!...",
  "generated_content": {
    "social_post": "🎓 Quick heads up!...", ← UPDATED
    ...
  },
  "ready_to_publish": true
}
```

---

### Example 5: Bulk Publish

```
REQUEST:
────────
POST /api/events/bulk-publish/
Authorization: Bearer token
Content-Type: application/json

{
  "event_ids": [101, 102, 103, 104],
  "visibility": "public",
  "generation_status": "ready"
}

PROCESSING (Django):
────────────────────
Event.objects.filter(id__in=[101, 102, 103, 104]).update(
  visibility="public",
  generation_status="ready"
)

RESPONSE:
────────
{
  "message": "Updated 4 events",
  "updated_count": 4,
  "visibility": "public",
  "generation_status": "ready"
}

DATABASE RESULT:
────────────────
Events 101-104 now have:
  visibility: "public"
  generation_status: "ready"
  ✓ Events now visible to students & public
```

---

**Last Updated**: 2025-01-25
