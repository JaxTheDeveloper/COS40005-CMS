# CSV Import → Article Editing Workflow API Documentation

This document describes the new API endpoints added to support the complete workflow from CSV import (Step 4) through article editing and publishing (Step 6).

## Workflow Overview

```
1. Staff uploads CSV file
   ↓ (POST /api/events/import-csv/)
2. Backend forwards file to n8n webhook
   ↓
3. n8n parses CSV and generates content (AI)
   ↓ (calls back to webhook endpoint)
4. Backend receives generated events
   ↓ (POST /api/events/batch-create-webhook/)
5. Events stored with generation_status='pending'
   ↓ (Staff reviews via dashboard)
6. Staff refines generated content and publishes
   ↓ (PUT /api/events/{id}/refine_content/ or POST /api/events/bulk-publish/)
7. Events visible to students (visibility='public' or 'unit')
```

---

## New API Endpoints

### 1. Batch Create Events from Webhook
**POST** `/api/events/batch-create-webhook/`

Webhook endpoint for n8n (or any external service) to POST back a batch of generated events.

#### Authentication
- Required: `Authorization: Bearer <token>`
- Must be staff user

#### Request Body
```json
{
  "events": [
    {
      "title": "New Year Kickoff 2025",
      "description": "Join us for an exciting new year celebration with special announcements.",
      "start": "2025-01-15T14:00:00Z",
      "end": "2025-01-15T15:30:00Z",
      "location": "Grand Hall",
      "visibility": "public",
      "generated_content": {
        "social_post": "New Year Kickoff happening Jan 15! Join us...",
        "email_newsletter": "Subject: New Year Event\n\nDear Community...",
        "long_article": "New Year Kickoff 2025\n\nWe are thrilled to...",
        "recruitment_ad": "New Year Kickoff — Grand Hall — Jan 15 — Register Now!"
      },
      "generation_meta": {
        "tone": "enthusiastic",
        "brand_score": 0.95,
        "bias_flag": false,
        "generated_by": "n8n-claude-api",
        "prompt_used": "Create marketing copy for event: ..."
      },
      "related_unit_id": null,
      "related_offering_id": null
    },
    ...more events
  ]
}
```

#### Response (201 Created)
```json
{
  "created_count": 3,
  "error_count": 0,
  "created_events": [
    {
      "id": 42,
      "title": "New Year Kickoff 2025",
      "generation_status": "pending",
      "visibility": "public",
      "created_at": "2025-11-26T10:30:00Z",
      ...
    },
    ...
  ],
  "errors": null
}
```

#### Example: cURL
```bash
curl -X POST http://localhost:8000/api/events/batch-create-webhook/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "title": "Event 1",
        "description": "...",
        "start": "2025-01-15T14:00:00Z",
        "end": "2025-01-15T15:30:00Z",
        "location": "Room A",
        "visibility": "public",
        "generated_content": {...},
        "generation_meta": {...}
      }
    ]
  }'
```

---

### 2. List Pending Events (Requiring Refinement)
**GET** `/api/events/pending-refinement/`

Staff-only endpoint to list all events with `generation_status` in ['pending', 'idle'] that need review and refinement before publishing.

#### Authentication
- Required: `Authorization: Bearer <token>`
- Must be staff user

#### Query Parameters
- `status` (optional, comma-separated): Filter by generation_status. Default: `pending,idle`
  - Example: `?status=pending,idle`
- `unit_id` (optional, integer): Filter by related_unit_id to see only events for a specific unit
  - Example: `?unit_id=5`
- `days` (optional, integer): Only show events created in the last N days
  - Example: `?days=7` shows events from the last 7 days

#### Response (200 OK)
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 42,
      "title": "New Year Kickoff 2025",
      "description": "Join us for an exciting new year celebration...",
      "start": "2025-01-15T14:00:00Z",
      "end": "2025-01-15T15:30:00Z",
      "location": "Grand Hall",
      "visibility": "public",
      "generation_status": "pending",
      "generated_content": {
        "social_post": "...",
        "email_newsletter": "...",
        "long_article": "...",
        "recruitment_ad": "..."
      },
      "generation_meta": {...},
      "created_by": 123,
      "created_at": "2025-11-26T10:30:00Z",
      "updated_at": "2025-11-26T10:30:00Z"
    },
    ...
  ]
}
```

#### Example: cURL
```bash
# Get all pending events
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/events/pending-refinement/"

# Get pending events from the last 7 days
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/events/pending-refinement/?days=7"

# Get pending events for a specific unit
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/events/pending-refinement/?unit_id=5"
```

---

### 3. Bulk Publish Events
**POST** `/api/events/bulk-publish/`

Staff-only endpoint to update visibility and generation_status for multiple events at once (batch publish operation).

#### Authentication
- Required: `Authorization: Bearer <token>`
- Must be staff user

#### Request Body
```json
{
  "event_ids": [42, 43, 44],
  "visibility": "public",
  "generation_status": "ready"
}
```

#### Parameters
- `event_ids` (required, array of integers): List of event IDs to update
- `visibility` (optional, string): One of `public`, `unit`, `staff`. Default: `public`
- `generation_status` (optional, string): One of `idle`, `pending`, `ready`, `failed`. Default: `ready`

#### Response (200 OK)
```json
{
  "message": "Updated 3 events",
  "updated_count": 3,
  "visibility": "public",
  "generation_status": "ready"
}
```

#### Example: cURL
```bash
# Publish 3 events as public
curl -X POST http://localhost:8000/api/events/bulk-publish/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "event_ids": [42, 43, 44],
    "visibility": "public",
    "generation_status": "ready"
  }'

# Publish 3 events but only visible to unit members
curl -X POST http://localhost:8000/api/events/bulk-publish/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "event_ids": [42, 43, 44],
    "visibility": "unit",
    "generation_status": "ready"
  }'
```

---

### 4. Get Generation Status (Single Event)
**GET** `/api/events/{id}/get_generation_status/`

Staff-only endpoint to get detailed generation and publication status for a single event.

#### Authentication
- Required: `Authorization: Bearer <token>`
- Must be staff user (can view own created events)

#### Response (200 OK)
```json
{
  "id": 42,
  "title": "New Year Kickoff 2025",
  "generation_status": "pending",
  "visibility": "public",
  "generated_content": {
    "social_post": "...",
    "email_newsletter": "...",
    "long_article": "...",
    "recruitment_ad": "..."
  },
  "generation_meta": {
    "tone": "enthusiastic",
    "brand_score": 0.95,
    "bias_flag": false,
    "generated_by": "n8n-claude-api"
  },
  "created_at": "2025-11-26T10:30:00Z",
  "updated_at": "2025-11-26T10:30:00Z",
  "last_generated_at": "2025-11-26T10:30:00Z",
  "created_by": "staff@swin.edu.au"
}
```

#### Example: cURL
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/events/42/get_generation_status/"
```

---

### 5. Refine Event Content (Single Event)
**PUT** `/api/events/{id}/refine_content/`

Staff-only endpoint to refine/edit the generated content and publication status for a single event (already existed, enhanced).

#### Authentication
- Required: `Authorization: Bearer <token>`
- Must be staff user

#### Request Body
```json
{
  "generated_content": {
    "social_post": "EDITED: Join us for...",
    "email_newsletter": "EDITED: Dear...",
    "long_article": "EDITED: New Year...",
    "recruitment_ad": "EDITED: New Year..."
  },
  "generation_status": "ready",
  "generation_meta": {
    "tone": "enthusiastic",
    "brand_score": 0.95,
    "bias_flag": false,
    "generated_by": "n8n-claude-api",
    "prompt_used": "...",
    "edited_by": "staff@swin.edu.au",
    "edited_at": "2025-11-26T11:00:00Z"
  }
}
```

#### Response (200 OK)
```json
{
  "id": 42,
  "title": "New Year Kickoff 2025",
  "description": "...",
  "start": "2025-01-15T14:00:00Z",
  "end": "2025-01-15T15:30:00Z",
  "location": "Grand Hall",
  "visibility": "public",
  "generation_status": "ready",
  "generated_content": {
    "social_post": "EDITED: Join us for...",
    ...
  },
  "generation_meta": {...},
  "created_at": "2025-11-26T10:30:00Z",
  "updated_at": "2025-11-26T11:00:00Z"
}
```

#### Example: cURL
```bash
curl -X PUT http://localhost:8000/api/events/42/refine_content/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "generated_content": {
      "social_post": "EDITED: ...",
      "email_newsletter": "EDITED: ...",
      "long_article": "EDITED: ...",
      "recruitment_ad": "EDITED: ..."
    },
    "generation_status": "ready"
  }'
```

---

## Complete Workflow Example (Step-by-Step)

### 1. Staff uploads CSV
```bash
curl -X POST http://localhost:8000/api/events/import-csv/ \
  -H "Authorization: Bearer <token>" \
  -F "data=@events.csv"
# Response: CSV forwarded to n8n webhook
```

### 2. n8n processes CSV and calls back
```bash
# n8n calls this endpoint with generated events
curl -X POST http://localhost:8000/api/events/batch-create-webhook/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "events": [
      {
        "title": "Event 1",
        "description": "...",
        "start": "2025-01-15T14:00:00Z",
        "end": "2025-01-15T15:30:00Z",
        "location": "Room A",
        "visibility": "public",
        "generated_content": {...},
        "generation_meta": {...}
      },
      ...
    ]
  }'
# Response: 201 Created, events stored with generation_status='pending'
```

### 3. Staff reviews pending events
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/events/pending-refinement/?days=1"
# Response: List of events created in the last 24 hours awaiting refinement
```

### 4. Staff reviews individual event details
```bash
curl -H "Authorization: Bearer <token>" \
  "http://localhost:8000/api/events/42/get_generation_status/"
# Response: Full generation & publication status
```

### 5. Staff edits one event's content
```bash
curl -X PUT http://localhost:8000/api/events/42/refine_content/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "generated_content": {
      "social_post": "My custom social post",
      "email_newsletter": "My custom email",
      "long_article": "My custom article",
      "recruitment_ad": "My custom ad"
    },
    "generation_status": "ready"
  }'
# Response: Event updated
```

### 6. Staff bulk publishes multiple events
```bash
curl -X POST http://localhost:8000/api/events/bulk-publish/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "event_ids": [42, 43, 44],
    "visibility": "public",
    "generation_status": "ready"
  }'
# Response: 3 events updated and visible to students
```

---

## Frontend Integration Tips

### For Staff Event Manager Dashboard

1. **After CSV upload**, show a "Processing..." indicator and poll `/api/events/pending-refinement/` every 2 seconds.

2. **Refining Events**:
   - Show list from `/api/events/pending-refinement/?days=1`
   - On click, fetch `/api/events/{id}/get_generation_status/`
   - Display `generated_content` fields in editable text areas
   - On save, call `PUT /api/events/{id}/refine_content/`

3. **Bulk Publishing**:
   - Show checkboxes next to each pending event
   - On "Publish All" button, collect selected IDs
   - Call `POST /api/events/bulk-publish/` with those IDs

### For Students (Notification/Calendar)

- Events with `visibility='public'` or `visibility='unit'` (if enrolled) appear in their calendar/notifications
- Events with `generation_status='ready'` are considered "published"

---

## Error Codes & Handling

| Status | Scenario | Example Response |
|--------|----------|------------------|
| 400 | Missing required fields | `{"error": "No events provided"}` |
| 400 | Invalid visibility/status | `{"error": "Invalid visibility value"}` |
| 400 | Malformed JSON | `{"detail": "JSON parse error"}` |
| 403 | Insufficient permissions | `{"detail": "Permission denied"}` |
| 404 | Event not found | `{"detail": "Not found"}` |
| 422 | Validation error in event data | `{"errors": {"title": ["This field is required"]}}` |

---

## Notes

- All timestamps are in ISO 8601 format (UTC).
- `generated_content` is a flexible JSON object; support all 4 fields but gracefully handle extras.
- `generation_meta` is metadata about the generation process; it's preserved on refinement and can be extended by staff (e.g., add `edited_by`, `edited_at`).
- Pagination is applied automatically on list endpoints (default: 20 items per page).
- All staff-only endpoints check `IsStaff` permission class, which requires `is_staff=True` or `user_type` in `['staff', 'unit_convenor', 'admin']`.
