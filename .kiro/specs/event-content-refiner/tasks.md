# Implementation Plan: Event Content Refiner (WF-4)

## Overview

Replace the `refine_content` PUT stub with a POST action that triggers an n8n workflow
(or falls back to a local mock refiner), add a `register_wf4` management command to
register the workflow record, and write property-based tests covering all six correctness
properties from the design.

> **Note — n8n WF-4 workflow:** The n8n workflow itself (webhook path `event-refine`,
> nodes: Webhook → Extract Refine Data → Content Refiner AI Agent → Build Callback Payload
> → POST generation_callback) is built manually by the developer in the n8n UI using the
> node spec in `design.md`. No task is created for it here.

## Tasks

- [x] 1. Replace `refine_content` stub with n8n-triggering POST action
  - In `src/backend/core/views_api.py`, replace the existing `@action(detail=True, methods=['put'], ...)` `refine_content` method on `EventViewSet` with a new `@action(detail=True, methods=['post'], permission_classes=[IsStaff])` implementation
  - Validate `refinement_prompt = request.data.get('refinement_prompt', '').strip()` — return 400 with `{"detail": "refinement_prompt is required"}` if falsy
  - Resolve `current_content = request.data.get('current_content') or event.generated_content`
  - Build `audience_context` dict using `event.visibility`, `event.target_all_students`, `event.get_targeted_students().count()`, `event.target_offerings.values_list('id', flat=True)`, `event.target_intakes.values_list('id', flat=True)`
  - Look up `N8NWorkflow` via `apps.get_model('users', 'N8NWorkflow').objects.filter(trigger_event='event.refine', is_active=True).first()`
  - **n8n path (workflow found):** build flat payload (`event_id`, `current_content`, `refinement_prompt`, `audience_context`, `triggered_by`), create `N8NExecutionLog` with `status='running'`, call `trigger_workflow(wf, event.id, payload)`, set `generation_status='pending'` + `last_generated_at=now()`, save, return 202; on exception set `generation_status='failed'`, update log, return 502
  - **Mock path (no workflow):** for each key in `current_content` prepend `[Refinement note: {refinement_prompt}]\n` to the value, set `generation_status='ready'`, `generation_meta={'generated_by': 'mock-refine', 'refinement_prompt': refinement_prompt}`, save, return 200 with `{generated_content, generation_meta}`
  - Import `trigger_workflow` from `.n8n_client` (lazy, inside the branch, matching the `generate_content` pattern)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 6.1, 6.2, 6.3_

  - [ ]* 1.1 Write property test — Property 1: valid staff POST returns 202 + pending status
    - File: `src/backend/core/tests/test_refine_content.py`
    - `@given(prompt=st.text(min_size=1).filter(lambda s: s.strip()))`
    - Mock `trigger_workflow` to return `(202, {})` and mock `N8NWorkflow` lookup to return an active workflow
    - Assert response status == 202 and `event.generation_status == 'pending'`
    - **Property 1: Valid staff requests set pending status and return 202**
    - **Validates: Requirements 1.1, 2.2**

  - [ ]* 1.2 Write property test — Property 2: whitespace/empty prompt returns 400
    - File: `src/backend/core/tests/test_refine_content.py`
    - `@given(prompt=st.one_of(st.just(''), st.text(alphabet=st.characters(whitelist_categories=('Zs',)))))`
    - Assert response status == 400 and `event.generation_status` is unchanged
    - **Property 2: Empty or whitespace prompts are rejected**
    - **Validates: Requirements 1.3**

  - [ ]* 1.3 Write property test — Property 3: provided current_content used as mock refiner source
    - File: `src/backend/core/tests/test_refine_content.py`
    - `@given(content=st.dictionaries(st.text(min_size=1), st.text(min_size=1), min_size=1))`
    - No active workflow registered; assert each key in the response `generated_content` derives from the provided `content` dict (not from `event.generated_content`)
    - **Property 3: Provided current_content is used as refinement source**
    - **Validates: Requirements 1.4**

- [x] 2. Create `register_wf4` management command
  - Create `src/backend/core/management/commands/register_wf4.py`
  - Subclass `BaseCommand`; `help = 'Register or update the WF-4 event.refine N8NWorkflow record'`
  - `add_arguments`: `--webhook-url` (default `http://cos40005_n8n:5678/webhook/event-refine`), `--test-url` (optional)
  - In `handle`: `get_or_create` on `N8NWorkflow` (from `apps.get_model('users', 'N8NWorkflow')`) filtered by `trigger_event='event.refine'`
  - Print old `webhook_url` before updating
  - Set `name='SwinCMS — Event Content Refiner'`, `configuration['webhook_url']` to `--webhook-url` value, `is_active=True`
  - If `--test-url` provided, also set `configuration['webhook_url_test']`
  - Save and print new `webhook_url`
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [ ]* 2.1 Write property test — Property 6: register_wf4 is idempotent
    - File: `src/backend/core/tests/test_refine_content.py`
    - `@given(url=st.from_regex(r'https?://[a-z0-9.-]+/webhook/[a-z-]+', fullmatch=True))`
    - Call the command multiple times with the same URL; assert exactly one `N8NWorkflow` record with `trigger_event='event.refine'` exists and `is_active=True` after each run
    - **Property 6: register_wf4 is idempotent**
    - **Validates: Requirements 4.1, 4.4, 4.5**

- [x] 3. Write remaining property-based tests
  - File: `src/backend/core/tests/test_refine_content.py`
  - Create the test file with necessary imports (`pytest`, `hypothesis`, `django.test.TestCase` or `APITestCase`, `unittest.mock`)
  - Set up shared fixtures: a staff user, an event with `generated_content`, and helpers to toggle workflow presence

  - [ ]* 3.1 Write property test — Property 4: n8n payload contains all required keys
    - `@given(prompt=st.text(min_size=1).filter(lambda s: s.strip()), target_all=st.booleans())`
    - Capture the payload passed to `trigger_workflow` via `unittest.mock.patch`
    - Assert payload contains `event_id`, `current_content`, `refinement_prompt`, and `audience_context` with keys `visibility`, `target_all_students`, `target_student_count`, `target_offering_ids`, `target_intake_ids`
    - **Property 4: n8n payload contains all required keys for any event**
    - **Validates: Requirements 2.1, 2.5, 3.1, 3.2, 3.3**

  - [ ]* 3.2 Write property test — Property 5: mock refiner prepends note to every field
    - `@given(content=st.dictionaries(st.text(min_size=1), st.text(), min_size=1), prompt=st.text(min_size=1).filter(lambda s: s.strip()))`
    - No active workflow; assert every value in response `generated_content` starts with `f'[Refinement note: {prompt}]\n'`
    - **Property 5: Mock refiner applies prompt note to every content field**
    - **Validates: Requirements 6.1, 6.2, 6.3**

- [x] 4. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
  - Run: `python manage.py test src.backend.core.tests.test_refine_content --verbosity=2`

## Notes

- Tasks marked with `*` are optional and can be skipped for a faster MVP
- `refine_chatbot` (url_path `refine-chatbot`) is untouched — it uses `settings.N8N_REFINE_WEBHOOK` directly and coexists without conflict
- `generation_callback` is already covered by WF-1 tests; no new callback tests are needed
- The `N8NWorkflow` / `N8NExecutionLog` models live in the `users` app — access them via `apps.get_model('users', ...)` to avoid circular imports, matching the pattern in `generate_content`
