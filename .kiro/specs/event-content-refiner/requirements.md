# Requirements Document

## Introduction

WF-4 (Event Content Refiner) extends the existing Event Content Generator (WF-1) in SwinCMS. Staff can view AI-generated event content, supply a natural-language refinement prompt, and receive Groq-refined content written back through the existing `generation_callback` endpoint. The feature adds a `refine_content` action to `EventViewSet`, a new `event.refine` n8n workflow, and a frontend refinement panel on the event detail page.

## Glossary

- **System**: The SwinCMS Django backend running at `cos40005_backend:8000`
- **Refiner**: The `refine_content` action on `EventViewSet` that handles staff refinement requests
- **N8N_Workflow**: An `N8NWorkflow` model instance stored in the `users` app that maps a `trigger_event` string to a webhook URL
- **WF4_Workflow**: The n8n workflow named "SwinCMS — Event Content Refiner" registered with `trigger_event='event.refine'`
- **generation_callback**: The existing `POST /api/core/events/{id}/generation_callback/` endpoint that writes AI content back to an Event
- **generated_content**: The `Event.generated_content` JSONField storing channel-specific copy (social_post, email_newsletter, recruitment_ad, vietnamese_version)
- **generation_status**: The `Event.generation_status` field with values: `idle`, `pending`, `ready`, `failed`
- **refinement_prompt**: Free-text staff feedback describing how the content should be changed
- **Audience_Context**: The resolved set of targeting fields on an Event (`target_students`, `target_offerings`, `target_intakes`, `target_all_students`, `visibility`) used to tailor refined content
- **Staff_User**: A Django user with `user_type` in `['staff', 'unit_convenor']` or `is_staff=True`
- **Mock_Refiner**: A local fallback that applies the refinement_prompt to generated_content without calling n8n, used when no active WF4_Workflow is registered

---

## Requirements

### Requirement 1: Refine Content Action

**User Story:** As a staff member, I want to submit a refinement prompt for an event's generated content, so that Groq can improve the copy based on my feedback.

#### Acceptance Criteria

1. WHEN a Staff_User sends `POST /api/core/events/{id}/refine_content/` with a non-empty `refinement_prompt`, THE Refiner SHALL set `generation_status` to `pending` and return HTTP 202 Accepted.
2. WHEN a non-staff user sends `POST /api/core/events/{id}/refine_content/`, THE Refiner SHALL return HTTP 403 Forbidden.
3. WHEN `refinement_prompt` is absent or empty in the request body, THE Refiner SHALL return HTTP 400 Bad Request with a descriptive error message.
4. WHEN `current_content` is provided in the request body, THE Refiner SHALL use that value as the content to refine; otherwise THE Refiner SHALL use `event.generated_content`.
5. THE Refiner SHALL replace the existing `PUT`-based stub implementation with the new `POST`-based n8n-triggering implementation.

---

### Requirement 2: n8n Workflow Trigger

**User Story:** As a staff member, I want the refinement request to be forwarded to n8n so that Groq can process it asynchronously, so that the UI is not blocked while AI generates the refined content.

#### Acceptance Criteria

1. WHEN an active N8N_Workflow with `trigger_event='event.refine'` exists, THE Refiner SHALL call `n8n_client.trigger_workflow()` with a payload containing `event_id`, `current_content`, `refinement_prompt`, and `audience_context`.
2. WHEN `n8n_client.trigger_workflow()` succeeds (HTTP 2xx from n8n), THE Refiner SHALL return HTTP 202 Accepted with `{"detail": "Refinement triggered", "generation_status": "pending"}`.
3. WHEN `n8n_client.trigger_workflow()` raises an exception, THE Refiner SHALL set `generation_status` to `failed`, log the error, and return HTTP 502 Bad Gateway with a descriptive error message.
4. WHEN no active N8N_Workflow with `trigger_event='event.refine'` exists, THE Refiner SHALL fall back to Mock_Refiner and return HTTP 200 OK with the mock-refined content.
5. THE Refiner SHALL include `audience_context` in the n8n payload as a dict with keys: `visibility`, `target_all_students`, `target_student_count`, `target_offering_ids`, `target_intake_ids`.

---

### Requirement 3: Audience-Aware Refinement Payload

**User Story:** As a staff member, I want the AI to be aware of the event's target audience when refining content, so that the refined copy is appropriately tailored to the intended recipients.

#### Acceptance Criteria

1. THE Refiner SHALL derive `audience_context.target_student_count` by calling `event.get_targeted_students().count()`.
2. THE Refiner SHALL include `audience_context.target_offering_ids` as a list of integer IDs from `event.target_offerings.values_list('id', flat=True)`.
3. THE Refiner SHALL include `audience_context.target_intake_ids` as a list of integer IDs from `event.target_intakes.values_list('id', flat=True)`.
4. WHEN `event.target_all_students` is `True`, THE Refiner SHALL set `audience_context.target_all_students` to `True` and omit individual student IDs from the payload.

---

### Requirement 4: WF4 n8n Workflow Registration

**User Story:** As a developer, I want a management command to register the WF-4 n8n workflow entry, so that the `event.refine` trigger is available without manual database edits.

#### Acceptance Criteria

1. THE System SHALL provide a management command `register_wf4` that creates or updates an N8N_Workflow record with `trigger_event='event.refine'` and `name='SwinCMS — Event Content Refiner'`.
2. WHEN the management command is run with `--webhook-url <url>`, THE System SHALL set `configuration.webhook_url` to the provided URL.
3. WHEN the management command is run without `--webhook-url`, THE System SHALL set `configuration.webhook_url` to `http://cos40005_n8n:5678/webhook/event-refine` as the default internal URL.
4. WHEN an N8N_Workflow with `trigger_event='event.refine'` already exists, THE System SHALL update it rather than create a duplicate.
5. THE System SHALL set `is_active=True` on the created or updated N8N_Workflow record.

---

### Requirement 5: generation_callback Compatibility

**User Story:** As a developer, I want the existing `generation_callback` endpoint to accept refined content from WF-4 without modification, so that the refine workflow reuses the same write-back path as WF-1.

#### Acceptance Criteria

1. WHEN n8n POSTs `{ event_id, generated_content, generation_meta }` to `generation_callback`, THE System SHALL set `generation_status` to `ready` and store the refined content — identical behaviour to WF-1 Phase 2.
2. THE System SHALL accept `generation_meta.refinement_prompt` as an optional field and store it inside `event.generation_meta` without error.
3. WHEN `generation_meta.generated_by` equals `'n8n-groq-refine'`, THE System SHALL store the value without modification.

---

### Requirement 6: Mock Refiner Fallback

**User Story:** As a developer, I want a local mock refinement path so that the feature can be tested end-to-end without a live n8n/Groq connection.

#### Acceptance Criteria

1. WHEN no active WF4_Workflow is registered, THE Mock_Refiner SHALL prepend the `refinement_prompt` as a note to each field in `generated_content` and return the modified content.
2. THE Mock_Refiner SHALL set `generation_status` to `ready` and `generation_meta.generated_by` to `'mock-refine'`.
3. THE Mock_Refiner SHALL return HTTP 200 OK with `{ "generated_content": {...}, "generation_meta": {...} }`.

---

### Requirement 7: Frontend Refinement Panel

**User Story:** As a staff member, I want a refinement panel on the event detail page, so that I can review current generated content, enter feedback, and see the refined result without leaving the page.

#### Acceptance Criteria

1. THE System SHALL display the current `generated_content` fields (social_post, email_newsletter, recruitment_ad, vietnamese_version) in read-only text areas within the refinement panel.
2. THE System SHALL provide a text input labelled "Refinement Feedback" for the staff member to enter a `refinement_prompt`.
3. WHEN a Staff_User clicks "Refine with AI", THE System SHALL send `POST /api/core/events/{id}/refine_content/` with the entered `refinement_prompt` and the current displayed content as `current_content`.
4. WHILE `generation_status` is `pending`, THE System SHALL display a loading spinner and disable the "Refine with AI" button.
5. WHEN `generation_status` transitions to `ready`, THE System SHALL update the displayed content fields with the new `generated_content` values without a full page reload.
6. IF the refinement request returns a non-2xx response, THE System SHALL display an error message to the staff member and re-enable the "Refine with AI" button.
