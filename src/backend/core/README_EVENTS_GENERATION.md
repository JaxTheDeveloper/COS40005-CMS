Events generation scaffold

Overview

This module adds a scaffold for generating multi-channel content for events (social posts, email newsletters, long-form articles, and recruitment ads).

Current state

- `Event` model has fields:
  - `generated_content` (JSON) to hold content variants per channel
  - `generation_status` (string) to indicate `idle|pending|ready|failed`
  - `generation_meta` (JSON) to hold tone, brand score, bias flag, prompt used, source
  - `last_generated_at` (datetime)

- `EventViewSet` exposes a POST action `generate_content` at:
  - `POST /api/core/events/{id}/generate_content/`
  - Request body: { "prompt": "<optional prompt>" }
  - Response: { generated_content: { ... }, generation_meta: { ... } }

Notes on n8n integration (future)

- Instead of synchronous generation inside Django, an n8n workflow should be used to orchestrate GenAI calls and downstream actions (posting to social platforms, sending emails).

- Recommended pattern:
  1. Django receives the generate request and creates a "generation job" (or sets `generation_status='pending'`).
  2. Django emits a webhook or pushes a message to n8n (HTTP webhook, or queue). Payload should include event id and prompt.
  3. n8n workflow receives the webhook, calls GenAI (OpenAI, Vertex AI, Azure OpenAI), validates outputs (tone classifier, brand safety), and posts to target channels (Twitter/X, Facebook, LinkedIn, Email via SMTP/API).
  4. n8n posts results back to Django via webhook endpoint (e.g., `POST /api/core/events/{id}/generation_callback/`) with generated_content and meta.

- Example n8n workflow components:
  - HTTP Trigger
  - HTTP Request (OpenAI/Azure/OpenAI-compatible)
  - Function nodes to split into channel templates
  - HTTP Request nodes to post to social APIs
  - HTTP Request back to Django to save results

Payload shapes

- Request to Django generate endpoint (client -> Django):
  {
    "prompt": "Create multi-channel content for the event"
  }

- Webhook payload from Django to n8n (recommended):
  {
    "event_id": 123,
    "prompt": "Create marketing copy...",
    "event": { "title": "...", "description": "...", "start": "...", "location": "..." }
  }

- Callback from n8n (n8n -> Django):
  {
    "generated_content": { "social_post": "...", "email_newsletter": "...", ... },
    "generation_meta": { "tone": "...", "brand_score": 0.9, "bias_flag": false }
  }

Security

- Protect webhook endpoints with a secret/token.
- Validate and sanitize all content before posting.

References

- n8n example workflow: https://n8n.io/workflows/5035-generate-and-auto-post-ai-videos-to-social-media-with-veo3-and-blotato/
- Example GenAI usage: https://www.youtube.com/watch?v=lZ-OiJHAdd8
